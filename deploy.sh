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

# Get system IP address for SSL certificate
SYSTEM_IP=$(hostname -I | awk '{print $1}' | head -1)
if [ -z "$SYSTEM_IP" ]; then
    SYSTEM_IP=$(ip route get 1.1.1.1 | awk '{print $7}' | head -1)
fi
if [ -z "$SYSTEM_IP" ]; then
    SYSTEM_IP="localhost"
fi

echo "🌐 System IP detected: $SYSTEM_IP"

# Generate self-signed SSL certificate if it doesn't exist
if [ ! -f certs/cert.pem ] || [ ! -f certs/key.pem ]; then
    echo "🔐 Generating self-signed SSL certificate for IP: $SYSTEM_IP..."
    openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=BestFriend/CN=$SYSTEM_IP"
    echo "✅ SSL certificate generated for $SYSTEM_IP"
else
    # Check if existing certificate matches current IP
    CERT_CN=$(openssl x509 -in certs/cert.pem -noout -subject | sed 's/.*CN=//')
    if [ "$CERT_CN" != "$SYSTEM_IP" ] && [ "$CERT_CN" != "localhost" ]; then
        echo "⚠️  SSL certificate CN ($CERT_CN) doesn't match current IP ($SYSTEM_IP)"
        echo "🔄 Regenerating SSL certificate for current IP..."
        openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=BestFriend/CN=$SYSTEM_IP"
        echo "✅ SSL certificate regenerated for $SYSTEM_IP"
    else
        echo "✅ SSL certificate is valid for current IP ($SYSTEM_IP)"
    fi
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

# Session Configuration
SESSION_TYPE=filesystem
SESSION_FILE_DIR=/tmp/flask_session
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

# Display access information
echo ""
echo "🌐 Access Information:"
echo "   Local access: https://localhost"
echo "   External access: https://$SYSTEM_IP"
echo "   OpenTTS: http://$SYSTEM_IP:5500"
echo ""
echo "⚠️  Note: If accessing from external devices, make sure:"
echo "   1. Firewall allows ports 80, 443, and 5500"
echo "   2. Router forwards these ports if behind NAT"
echo "   3. SSL certificate is valid for your IP address"
echo ""
echo "🔧 Network Configuration Tips:"
echo "   - Check firewall: sudo ufw status"
echo "   - Allow ports: sudo ufw allow 80,443,5500"
echo "   - Check port forwarding on your router"
echo "   - Verify SSL certificate: openssl x509 -in certs/cert.pem -text -noout | grep DNS"
echo ""

# Generate Fernet key if not present
if ! grep -q "FERNET_KEY=" .env || grep -q "your-fernet-key-here" .env; then
    echo "🔑 Generating Fernet key..."
    # Use Python to generate a proper Fernet key
    FERNET_KEY=$(python3 -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode('ascii'))")
    
    # Validate the generated key
    if [ ${#FERNET_KEY} -eq 44 ]; then
        echo "✅ Fernet key generated: ${#FERNET_KEY} characters"
    else
        echo "❌ Error: Fernet key generation failed (got ${#FERNET_KEY} characters)"
        exit 1
    fi
    
    # Use sed with delimiter that won't conflict with base64 characters
    sed -i "s|^FERNET_KEY=.*|FERNET_KEY=${FERNET_KEY}|" .env
fi

# Generate secret key if not present
if ! grep -q "SECRET_KEY=" .env || grep -q "your-secret-key-here" .env; then
    echo "🔑 Generating secret key..."
    # Use Python to generate a proper key
    SECRET_KEY=$(python3 -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode('ascii'))")
    
    # Validate the generated key
    if [ ${#SECRET_KEY} -eq 44 ]; then
        echo "✅ Secret key generated: ${#SECRET_KEY} characters"
    else
        echo "❌ Error: Secret key generation failed (got ${#SECRET_KEY} characters)"
        exit 1
    fi
    
    # Use sed with delimiter that won't conflict with base64 characters
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env
fi

# Export environment variables for Docker Compose
echo "🔧 Exporting environment variables for Docker Compose..."

# THE FIX: Use proper IFS handling to preserve full line content
while IFS= read -r line; do
    # Skip comments and empty lines
    if [[ "$line" =~ ^#.*$ ]] || [[ -z "$line" ]]; then
        continue
    fi
    
    # Check if line contains an = sign
    if [[ "$line" == *"="* ]]; then
        # Split on first = only
        key="${line%%=*}"
        value="${line#*=}"
        
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
echo "   FERNET_KEY: ${FERNET_KEY:0:20}... (${#FERNET_KEY} chars)"
echo "   SECRET_KEY: ${SECRET_KEY:0:20}... (${#SECRET_KEY} chars)"

if [ ${#FERNET_KEY} -ne 44 ] || [ ${#SECRET_KEY} -ne 44 ]; then
    echo "❌ Keys are not the correct length! Cannot continue."
    echo "   FERNET_KEY length: ${#FERNET_KEY}"
    echo "   SECRET_KEY length: ${#SECRET_KEY}"
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
echo "   View nginx logs: $COMPOSE_CMD logs -f nginx"
echo "   Connect to database: $COMPOSE_CMD exec db psql -U bestfriend"
echo ""
echo "⚠️  Note: This is using a self-signed certificate."
echo "   You'll need to accept the security warning in your browser."
echo ""
echo "💡 Troubleshooting:"
echo "   If services fail to start, check logs with: $COMPOSE_CMD logs"
echo "   To rebuild from scratch: $COMPOSE_CMD down -v && ./deploy.sh"