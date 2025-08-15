#!/bin/bash

set -e

echo "🚀 Deploying Best Friend AI Companion..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose first."
    exit 1
fi

# Use docker compose (newer) if available, otherwise docker-compose
COMPOSE_CMD="docker compose"
if ! docker compose version &> /dev/null; then
    COMPOSE_CMD="docker-compose"
fi

# Create necessary directories
mkdir -p certs
mkdir -p logs

# Generate self-signed SSL certificate if it doesn't exist
if [ ! -f certs/cert.pem ] || [ ! -f certs/key.pem ]; then
    echo "🔐 Generating self-signed SSL certificate..."
    openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=BestFriend/CN=localhost"
    echo "✅ SSL certificate generated"
fi

# Pull latest changes if this is a git repository
if [ -d .git ]; then
    echo "📥 Pulling latest changes..."
    git pull origin main || git pull origin master || echo "⚠️  Could not pull latest changes"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please review and update .env file with your configuration"
fi

# Generate Fernet key if not present
if ! grep -q "FERNET_KEY=" .env || grep -q "your-fernet-key-here" .env; then
    echo "🔑 Generating Fernet key..."
    # Try to use Python3 with cryptography, fallback to openssl if not available
    if python3 -c "import cryptography.fernet" 2>/dev/null; then
        FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
        echo "✅ Fernet key generated using Python cryptography"
    else
        echo "⚠️  Python cryptography module not available, using OpenSSL fallback..."
        # Generate a 32-byte key using OpenSSL and base64 encode it
        FERNET_KEY=$(openssl rand -base64 32)
        echo "✅ Fernet key generated using OpenSSL"
    fi
    # Use awk for safer replacement (handles special characters better)
    awk -v key="$FERNET_KEY" 'sub(/^FERNET_KEY=.*/, "FERNET_KEY=" key)' .env > .env.tmp && mv .env.tmp .env
fi

# Generate secret key if not present
if ! grep -q "SECRET_KEY=" .env || grep -q "your-secret-key-here" .env; then
    echo "🔑 Generating secret key..."
    # Try to use Python3 with secrets, fallback to openssl if not available
    if python3 -c "import secrets" 2>/dev/null; then
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        echo "✅ Secret key generated using Python secrets"
    else
        echo "⚠️  Python secrets module not available, using OpenSSL fallback..."
        # Generate a 32-byte key using OpenSSL and base64 encode it
        SECRET_KEY=$(openssl rand -base64 32)
        echo "✅ Secret key generated using OpenSSL"
    fi
    # Use awk for safer replacement
    awk -v key="$SECRET_KEY" 'sub(/^SECRET_KEY=.*/, "SECRET_KEY=" key)' .env > .env.tmp && mv .env.tmp .env
fi

# Build and start containers
echo "🐳 Building and starting containers..."
$COMPOSE_CMD pull
$COMPOSE_CMD up -d --build

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run database migrations
echo "🗄️  Running database migrations..."
$COMPOSE_CMD exec -T web flask db upgrade || echo "⚠️  Migration failed, but continuing..."

# Create admin user if it doesn't exist
echo "👤 Setting up admin user..."
$COMPOSE_CMD exec -T web flask create-admin || echo "⚠️  Admin setup failed, but continuing..."

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📱 Access your Best Friend AI Companion at:"
echo "   https://$(hostname -I | awk '{print $1}' | head -1)"
echo "   or https://localhost"
echo ""
echo "🔧 Admin credentials (from .env file):"
echo "   Email: $(grep ADMIN_EMAIL .env | cut -d'=' -f2)"
echo "   Password: $(grep ADMIN_PASSWORD .env | cut -d'=' -f2)"
echo ""
echo "📋 Useful commands:"
echo "   View logs: $COMPOSE_CMD logs -f"
echo "   Stop services: $COMPOSE_CMD down"
echo "   Restart services: $COMPOSE_CMD restart"
echo ""
echo "⚠️  Note: This is using a self-signed certificate."
echo "   You'll need to accept the security warning in your browser."
