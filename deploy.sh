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
cat > .env << 'EOF'
# Best Friend AI Companion Environment Configuration
# Generated automatically by deploy.sh - DO NOT EDIT MANUALLY

# Database Configuration
DATABASE_URL=postgresql://bestfriend:bestfriend@localhost:5432/bestfriend
REDIS_URL=redis://localhost:6379/0

# Ollama Configuration (Remote)
OLLAMA_BASE_URL=http://your-ollama-server:11434
OLLAMA_MODEL=llama3.1:8b
EMBED_MODEL=nomic-embed-text

# TTS Configuration
TTS_URL=http://localhost:5500
TTS_VOICE=en_US-amy-low

# STT Configuration
STT_LANGUAGE=en

# Security Keys (will be generated automatically)
FERNET_KEY=your-fernet-key-here
SECRET_KEY=your-secret-key-here

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE=16777216
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Admin User (will be created automatically)
ADMIN_EMAIL=admin@bestfriend.local
ADMIN_PASSWORD=admin123
EOF

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
        FERNET_KEY=$(openssl rand 32 | base64 | tr -d '\n')
        echo "✅ Fernet key generated using OpenSSL"
    fi
    
    # Use sed with delimiter that won't conflict with base64 characters
    sed -i "s|^FERNET_KEY=.*|FERNET_KEY=${FERNET_KEY}|" .env
    
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
    SECRET_KEY=$(openssl rand 32 | base64 | tr -d '\n')
    echo "✅ Secret key generated using OpenSSL"
    
    # Use sed with delimiter that won't conflict with base64 characters
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env
    
    # Validate the generated key
    if [ ${#SECRET_KEY} -eq 44 ]; then
        echo "✅ Secret key length verified: ${#SECRET_KEY} characters"
    else
        echo "⚠️  Warning: Secret key length is ${#SECRET_KEY} characters (expected 44)"
    fi
fi

# Export environment variables for Docker Compose
echo "🔧 Exporting environment variables for Docker Compose..."

# Read the .env file and export each variable
while IFS='=' read -r key value; do
    # Skip comments and empty lines
    if [[ ! "$key" =~ ^#.*$ ]] && [[ -n "$key" ]]; then
        # Remove any surrounding quotes from the value
        value="${value%\"}"
        value="${value#\"}"
        value="${value%\'}"
        value="${value#\'}"
        # Export the variable
        export "$key=$value"
    fi
done < .env

# Verify critical environment variables are exported
echo "🔍 Verifying exported environment variables..."
if [ -n "$FERNET_KEY" ]; then
    echo "✅ FERNET_KEY exported: ${FERNET_KEY:0:20}..."
else
    echo "❌ FERNET_KEY not exported!"
    exit 1
fi

if [ -n "$SECRET_KEY" ]; then
    echo "✅ SECRET_KEY exported: ${SECRET_KEY:0:20}..."
else
    echo "❌ SECRET_KEY not exported!"
    exit 1
fi

# Alternative method: Use --env-file flag with docker compose
echo "📋 Using .env file with Docker Compose..."

# Build and start containers with explicit env file
echo "🐳 Building and starting containers..."
$COMPOSE_CMD --env-file .env pull
$COMPOSE_CMD --env-file .env up -d --build

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
for i in {1..30}; do
    if $COMPOSE_CMD exec -T db pg_isready -U bestfriend > /dev/null 2>&1; then
        echo "✅ Database is ready!"
        break
    fi
    echo "   Waiting for database... ($i/30)"
    sleep 2
done

# Run database migrations
echo "🗄️  Running database migrations..."
$COMPOSE_CMD exec -T web flask db upgrade || echo "⚠️  Migration failed, but continuing..."

# Create admin user if it doesn't exist
echo "👤 Setting up admin user..."
$COMPOSE_CMD exec -T web flask create-admin || echo "⚠️  Admin setup failed, but continuing..."

# Get the actual IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}' | head -1)
if [ -z "$IP_ADDRESS" ]; then
    IP_ADDRESS="localhost"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📱 Access your Best Friend AI Companion at:"
echo "   https://${IP_ADDRESS}"
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
echo "   View web logs: $COMPOSE_CMD logs -f web"
echo "   View nginx logs: $COMPOSE_CMD logs -f nginx"
echo "   Connect to database: $COMPOSE_CMD exec db psql -U bestfriend"
echo ""
echo "⚠️  Note: This is using a self-signed certificate."
echo "   You'll need to accept the security warning in your browser."
echo ""
echo "💡 Troubleshooting:"
echo "   If services fail to start, check logs with: $COMPOSE_CMD logs"
echo "   To rebuild from scratch: $COMPOSE_CMD down -v && ./deploy.sh"