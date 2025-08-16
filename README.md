# Best Friend AI Companion 🤖💬

A production-ready, Dockerized Flask web application that provides a personal AI companion with text and voice chat capabilities, long-term memory, and various AI service integrations.

[![CI/CD](https://github.com/chartmann1590/Best-Friend/actions/workflows/ci.yml/badge.svg)](https://github.com/chartmann1590/Best-Friend/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [✨ Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [📦 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [🔧 Development](#-development)
- [📚 API Documentation](#-api-documentation)
- [🔒 Security](#-security)
- [🚀 Deployment](#-deployment)
- [📖 Documentation](#-documentation)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [💬 Support](#-support)
- [🛣️ Roadmap](#️-roadmap)

## 🚀 Quick Start

### One-Command Deployment

```bash
# Clone and deploy in one go
git clone https://github.com/chartmann1590/Best-Friend.git && cd Best-Friend && ./deploy.sh

# Access at https://YOUR_SYSTEM_IP
```

### Manual Deployment

1. **Clone the repository**
   ```bash
   git clone https://github.com/chartmann1590/Best-Friend.git
   cd Best-Friend
   ```

2. **Deploy with deploy script**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **Access your AI companion**
   - 🌐 Open https://YOUR_SYSTEM_IP in your browser
   - 🔒 Accept the self-signed certificate warning
   - 🎯 Complete the onboarding wizard
   - 🚀 Start chatting with your AI companion!

### Default Credentials

- **Admin Email**: `admin@bestfriend.local`
- **Admin Password**: `admin123`

⚠️ **Important**: Change these credentials immediately in production!

## ✨ Features

- 🤖 **AI Chat**: Text and voice conversations with configurable LLM (Ollama)
- 🎤 **Voice Interface**: Speech-to-text and text-to-speech capabilities  
- 🧠 **Long-term Memory**: Persistent conversation memory using pgvector
- ⚙️ **Customizable**: Personalize AI personality, voice, and settings
- 🔒 **Privacy-Focused**: Local deployment with data export/delete options
- 🛡️ **Secure**: Authentication, rate limiting, and security headers
- 📱 **Mobile-Friendly**: Responsive design with modern UI
- 🔐 **Encrypted Storage**: Sensitive data encrypted at rest
- 📊 **Admin Dashboard**: System monitoring and user management
- 🚀 **Production Ready**: Docker, CI/CD, and comprehensive testing

## 📦 Installation

### Prerequisites

- 🐳 **Docker** and **Docker Compose** (v20.10+)
- 📥 **Git** for repository cloning
- 🔐 **OpenSSL** for SSL certificate generation
- 💻 **Linux/macOS/Windows** with Docker support

### System Requirements

- **CPU**: 4+ cores (2.4 GHz+)
- **RAM**: 8+ GB
- **Storage**: 50+ GB SSD
- **Network**: 100+ Mbps connection

## 🏗️ Architecture

### Services

- **Web**: Flask application with Gunicorn
- **Nginx**: Reverse proxy with SSL termination
- **PostgreSQL**: Database with pgvector extension
- **Redis**: Caching and rate limiting
- **OpenTTS**: Text-to-speech service
- **Ollama**: Remote LLM inference server (user-configured)

### Key Components

- **Memory System**: Vector embeddings stored in pgvector
- **STT/TTS**: Speech processing with faster-whisper and OpenTTS
- **Security**: Encrypted settings, rate limiting, CSRF protection
- **UI**: Modern interface with Tailwind CSS and HTMX

## ⚙️ Configuration

### Environment Variables

Copy `env.example` to `.env` and configure:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key
FERNET_KEY=your-fernet-key

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Ollama Configuration (Remote)
OLLAMA_BASE_URL=http://your-ollama-server:11434
OLLAMA_MODEL=llama3.1:8b
EMBED_MODEL=nomic-embed-text

# TTS Configuration
TTS_URL=http://opentts:5500
TTS_VOICE=en_US-amy-low
```

### AI Service Configuration

#### Ollama Server Setup
```bash
# Example Ollama server configuration
OLLAMA_URL=http://10.0.0.121:11434
OLLAMA_MODEL=llama3.1:8b

# Test connection and discover models
# Use the "Test" button in settings to verify connectivity
```

#### OpenTTS Server Setup
```bash
# Example TTS server configuration
TTS_URL=http://10.0.0.121:5500
TTS_VOICE=en_US-amy-low

# Test connection and discover voices
# Use the "Test" button in settings to verify connectivity
```

### Common Configuration Scenarios

#### Local Development
```bash
FLASK_ENV=development
DEBUG=true
DATABASE_URL=postgresql://localhost/bestfriend_dev
```

#### Production Deployment
```bash
FLASK_ENV=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@db/bestfriend
SECURE_COOKIES=true
```

#### Multi-Server Setup
```bash
# Primary Ollama server
OLLAMA_URL=http://primary-server:11434

# Backup Ollama server
OLLAMA_BACKUP_URL=http://backup-server:11434

# Load balancer configuration
NGINX_UPSTREAM=upstream_ollama
```

### Ollama Configuration

**Important**: This application uses a remote Ollama server. You need to:

1. **Set up Ollama** on a separate server/machine
2. **Configure the URL** in the settings (e.g., `http://your-server:11434`)
3. **Ensure network access** between this app and your Ollama server

### Settings

Configure your AI companion through the web interface:

- **Personality**: Customize AI behavior and responses
- **Voice**: Select TTS voice and speaking rate
- **Memory**: Toggle memory features and export data
- **Privacy**: Control data retention and sharing

## 🔧 Development

### Local Development

1. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env for development settings
   ```

3. **Run migrations**
   ```bash
   flask db upgrade
   ```

4. **Start development server**
   ```bash
   flask run --debug
   ```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## 📚 API Documentation

### Chat Endpoints

- `POST /api/chat` - Send text message
- `POST /api/stt` - Upload audio for transcription
- `GET /api/tts/stream` - Stream TTS audio

### Settings Endpoints

- `GET /settings` - Get user settings
- `POST /settings` - Update settings
- `GET /api/memory/search` - Search memories (admin)

### Privacy Endpoints

- `GET /api/export` - Export user data
- `DELETE /api/delete` - Delete user data

## 🔒 Security

### Features

- **Authentication**: Local password-based login
- **Rate Limiting**: Per-IP and per-user limits
- **CSRF Protection**: Token-based form protection
- **Security Headers**: CSP, HSTS, XSS protection
- **Encryption**: Fernet encryption for sensitive data

### Best Practices

- Change default credentials
- Use strong passwords
- Keep dependencies updated
- Monitor logs regularly
- Backup data regularly

## 🚀 Deployment

### Production Deployment

1. **Configure production environment**
   ```bash
   # Update .env with production values
   FLASK_ENV=production
   SECRET_KEY=<strong-secret-key>
   FERNET_KEY=<strong-fernet-key>
   ```

2. **Set up SSL certificates**
   ```bash
   # Replace self-signed certs with real certificates
   cp your-cert.pem certs/cert.pem
   cp your-key.pem certs/key.pem
   ```

3. **Deploy**
   ```bash
   ./deploy.sh
   ```

### Backup and Restore

```bash
# Backup database
docker compose exec db pg_dump -U bestfriend bestfriend > backup.sql

# Restore database
docker compose exec -T db psql -U bestfriend bestfriend < backup.sql
```

## 📖 Documentation

Comprehensive documentation is available in the `/docs` directory:

### 🏗️ **System Documentation**
- **[Architecture](docs/ARCHITECTURE.md)** - System design and technical details
- **[Configuration](docs/CONFIGURATION.md)** - Setup and configuration options
- **[API Reference](docs/API.md)** - Complete API documentation
- **[Deployment](docs/DEPLOYMENT.md)** - Production deployment guide
- **[Operations](docs/OPERATIONS.md)** - Maintenance and operations

### 🔒 **Security & Privacy**
- **[Security](docs/SECURITY.md)** - Security policies and procedures
- **[Privacy](docs/PRIVACY.md)** - Privacy policy and data handling

### 🤖 **AI Service Integration**
- **[Ollama Integration](docs/OLLAMA.md)** - Complete guide to Ollama LLM server setup and management
- **[OpenTTS Integration](docs/OPENTTS.md)** - Comprehensive guide to text-to-speech setup and voice management

### 👤 **User Experience**
- **[User Guide](docs/USER_GUIDE.md)** - Complete user manual with setup, features, and troubleshooting

### 📚 **Quick Reference**
- **[Quick Start Guide](#-quick-start)** - Get up and running in minutes
- **[Configuration Examples](#️-configuration)** - Common configuration scenarios
- **[Troubleshooting](#-troubleshooting)** - Common issues and solutions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 💬 Support

- **Issues**: Report bugs and feature requests on GitHub
- **Documentation**: See `/docs` directory for detailed guides
- **Security**: Report security issues privately

## 🔧 Troubleshooting

### Common Issues

#### Connection Problems
- **Ollama Server**: Check server URL and ensure Ollama is running
- **TTS Server**: Verify OpenTTS server connectivity and voice availability
- **Database**: Ensure PostgreSQL is running and accessible

#### Voice Issues
- **Microphone Access**: Grant browser permissions and check device settings
- **TTS Not Working**: Verify TTS server connection and voice selection
- **Audio Quality**: Adjust speaking rate and pitch settings

#### Performance Issues
- **Slow Responses**: Check server resources and model complexity
- **High Memory Usage**: Optimize model settings and server configuration

### Getting Help

1. **Check Documentation**: Review the comprehensive guides in `/docs`
2. **Test Connections**: Use built-in test functions in settings
3. **Review Logs**: Check application and service logs
4. **Community Support**: Report issues on GitHub

For detailed troubleshooting, see the [User Guide](docs/USER_GUIDE.md) and service-specific documentation.

## 🛣️ Roadmap

- [ ] Multi-user support
- [ ] Advanced memory management
- [ ] Plugin system
- [ ] Mobile app
- [ ] Voice cloning
- [ ] Integration APIs
