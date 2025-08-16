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

# Remove old .env file and create fresh one every time
echo "🗑️  Removing old .env file..."
rm -f .env

echo "📝 Creating fresh .env file..."
{
    echo "# Best Friend AI Companion Environment Configuration"
    echo "# Generated automatically by deploy.sh - DO NOT EDIT MANUALLY"
    echo ""
    echo "# Database Configuration"
    echo "DATABASE_URL=postgresql://bestfriend:bestfriend@localhost:5432/bestfriend"
    echo "REDIS_URL=redis://localhost:6379/0"
    echo ""
    echo "# Ollama Configuration (Remote)"
    echo "OLLAMA_BASE_URL=http://your-ollama-server:11434"
    echo "OLLAMA_MODEL=llama3.1:8b"
    echo "EMBED_MODEL=nomic-embed-text"
    echo ""
    echo "# TTS Configuration"
    echo "TTS_URL=http://localhost:5500"
    echo "TTS_VOICE=en_US-amy-low"
    echo ""
    echo "# STT Configuration"
    echo "STT_LANGUAGE=en"
    echo ""
    echo "# Security Keys (will be generated automatically)"
    echo "FERNET_KEY=your-fernet-key-here"
    echo "SECRET_KEY=your-secret-key-here"
    echo ""
    echo "# Application Settings"
    echo "DEBUG=false"
    echo "LOG_LEVEL=INFO"
    echo "MAX_UPLOAD_SIZE=16777216"
    echo "RATE_LIMIT_PER_MINUTE=60"
    echo "RATE_LIMIT_PER_HOUR=1000"
    echo ""
    echo "# Admin User (will be created automatically)"
    echo "ADMIN_EMAIL=admin@bestfriend.local"
    echo "ADMIN_PASSWORD=admin123"
} > .env

# Verify .env file was created properly
echo "🔍 Verifying .env file creation..."
if [ ! -f .env ]; then
    echo "❌ .env file was not created!"
    exit 1
fi

if [ ! -s .env ]; then
    echo "❌ .env file is empty!"
    exit 1
fi

echo "✅ .env file created successfully with $(wc -l < .env) lines"

# Generate Fernet key if not present
if ! grep -q "FERNET_KEY=" .env || grep -q "your-fernet-key-here" .env; then
    echo "🔑 Generating Fernet key..."
    # Try to use Python3 with cryptography, fallback to openssl if not available
    if python3 -c "import cryptography.fernet" 2>/dev/null; then
        FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
        echo "✅ Fernet key generated using Python cryptography"
    else
        echo "⚠️  Python cryptography module not available, using OpenSSL fallback..."
        # Generate exactly 32 bytes and base64 encode for Fernet compatibility
        FERNET_KEY=$(openssl rand 32 | base64)
        echo "✅ Fernet key generated using OpenSSL"
    fi
    # Use awk for safer replacement (handles special characters better)
    awk -v key="$FERNET_KEY" 'sub(/^FERNET_KEY=.*/, "FERNET_KEY=" key)' .env > .env.tmp && mv .env.tmp .env
    
    # Validate the generated key
    if [ ${#FERNET_KEY} -eq 44 ]; then
        echo "✅ Fernet key length verified: ${#FERNET_KEY} characters"
    else
        echo "⚠️  Warning: Fernet key length is ${#FERNET_KEY} characters (expected 44)"
    fi
fi

# Generate secret key if not present
if ! grep -q "SECRET_KEY=" .env || grep -q "your-secret-key-here" .env; then
    echo "🔑 Generating secret key..."
    # Use OpenSSL for consistent 44-character base64-encoded keys
    SECRET_KEY=$(openssl rand 32 | base64)
    echo "✅ Secret key generated using OpenSSL"
    # Use awk for safer replacement
    awk -v key="$SECRET_KEY" 'sub(/^SECRET_KEY=.*/, "SECRET_KEY=" key)' .env > .env.tmp && mv .env.tmp .env
    
    # Validate the generated key
    if [ ${#SECRET_KEY} -eq 44 ]; then
        echo "✅ Secret key length verified: ${#SECRET_KEY} characters"
    else
        echo "⚠️  Warning: Secret key length is ${#SECRET_KEY} characters (expected 44)"
    fi
fi

# Load environment variables for Docker Compose
echo "🔧 Loading environment variables..."

# Debug: Show .env file contents and line count
echo "📋 .env file contents (${#FERNET_KEY} chars for FERNET_KEY, ${#SECRET_KEY} chars for SECRET_KEY):"
echo "📄 .env file line count: $(wc -l < .env)"
grep -E "^(FERNET_KEY|SECRET_KEY)=" .env | sed 's/=.*/=***HIDDEN***/'
echo "🔍 Full .env file:"
cat .env

# Load environment variables
set -a  # automatically export all variables
source .env
set +a  # stop automatically exporting

# Verify environment variables are loaded
echo "🔍 Verifying environment variables..."
if [ -n "$FERNET_KEY" ]; then
    echo "✅ FERNET_KEY loaded: ${FERNET_KEY:0:20}..."
else
    echo "❌ FERNET_KEY not loaded!"
    exit 1
fi

if [ -n "$SECRET_KEY" ]; then
    echo "✅ SECRET_KEY loaded: ${SECRET_KEY:0:20}..."
else
    echo "❌ SECRET_KEY not loaded!"
    exit 1
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
