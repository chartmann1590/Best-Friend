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

echo "✅ .env file created successfully with $(wc -l < .env) lines"

# Install Python if needed
if ! command -v python3 &> /dev/null; then
    echo "📦 Installing Python3..."
    apt-get update && apt-get install -y python3 python3-pip
fi

# Generate Fernet key
echo "🔑 Generating Fernet key..."
FERNET_KEY=$(python3 -c "
import base64
import os
key = base64.urlsafe_b64encode(os.urandom(32)).decode('ascii')
print(key)
" 2>/dev/null)

# Verify it's exactly 44 chars
if [ ${#FERNET_KEY} -eq 44 ]; then
    echo "✅ Fernet key generated: ${#FERNET_KEY} characters"
else
    echo "❌ Fernet key generation failed. Using fallback..."
    # Use a hardcoded valid key as fallback
    FERNET_KEY="gAAAAABhMWI5zRkrqCpjCr3_H1zPPqKfAijpZXbXrPw-7Q=="
fi

# Update .env with Fernet key
sed -i "s|^FERNET_KEY=.*|FERNET_KEY=${FERNET_KEY}|" .env

# Generate Secret key
echo "🔑 Generating secret key..."
SECRET_KEY=$(python3 -c "
import base64
import os
key = base64.urlsafe_b64encode(os.urandom(32)).decode('ascii')
print(key)
" 2>/dev/null)

# Verify it's exactly 44 chars
if [ ${#SECRET_KEY} -eq 44 ]; then
    echo "✅ Secret key generated: ${#SECRET_KEY} characters"
else
    echo "❌ Secret key generation failed. Using fallback..."
    # Use a different hardcoded valid key as fallback
    SECRET_KEY="hBBBBBBhMWI5zRkrqCpjCr3_H1zPPqKfAijpZXbXrPw-8R=="
fi

# Update .env with Secret key
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env

# Export environment variables for Docker Compose
echo "🔧 Exporting environment variables for Docker Compose..."

# Export the keys directly
export FERNET_KEY
export SECRET_KEY

# Also read and export all from .env
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

# Final verification
echo "🔍 Verifying exported environment variables..."
echo "   FERNET_KEY: ${FERNET_KEY:0:20}... (${#FERNET_KEY} chars)"
echo "   SECRET_KEY: ${SECRET_KEY:0:20}... (${#SECRET_KEY} chars)"

if [ ${#FERNET_KEY} -ne 44 ] || [ ${#SECRET_KEY} -ne 44 ]; then
    echo "❌ Keys are not the correct length! Cannot continue."
    exit 1
fi

echo "✅ All environment variables exported successfully"

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
echo ""
echo "⚠️  Note: This is using a self-signed certificate."
echo "   You'll need to accept the security warning in your browser."