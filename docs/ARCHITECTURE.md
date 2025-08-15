# Architecture Documentation

This document describes the technical architecture of the Best Friend AI Companion application.

## System Overview

The Best Friend AI Companion is a Flask-based web application that provides an AI chat interface with voice capabilities, long-term memory, and personalization features. The system is designed as a microservices architecture running in Docker containers.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser  │    │   Mobile App   │    │   API Client   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │        Nginx             │
                    │   (Reverse Proxy)        │
                    │   - SSL Termination      │
                    │   - Static Files         │
                    │   - Security Headers     │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │      Flask Web App       │
                    │   (Gunicorn Workers)     │
                    │   - Authentication       │
                    │   - Chat Interface       │
                    │   - Settings Management  │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
┌─────────▼─────────┐  ┌─────────▼─────────┐  ┌─────────▼─────────┐
│   PostgreSQL      │  │      Redis        │  │     Ollama       │
│   + pgvector      │  │   - Rate Limiting │  │   - LLM Backend  │
│   - User Data     │  │   - Task Queue    │  │   - Embeddings   │
│   - Messages      │  │   - Sessions      │  │                  │
│   - Memories      │  └───────────────────┘  └───────────────────┘
│   - Settings      │
└───────────────────┘
          │
          │
┌─────────▼─────────┐  ┌─────────▼─────────┐
│   OpenTTS/Piper   │  │  faster-whisper   │
│   - TTS Service   │  │   - STT Service   │
└───────────────────┘  └───────────────────┘
```

## Component Details

### 1. Frontend Layer

#### Web Interface
- **Technology**: HTML5, Tailwind CSS, JavaScript (ES6+)
- **Framework**: Vanilla JavaScript with modular architecture
- **Features**: 
  - Responsive design (mobile-first)
  - Dark/light theme support
  - Real-time chat interface
  - Voice recording and playback
  - Settings management
  - Onboarding wizard

#### Key Components
- **Chat Interface**: Real-time message display with user/AI distinction
- **Voice Controls**: Microphone access, recording visualization, audio playback
- **Settings Panel**: Comprehensive configuration management
- **Onboarding Flow**: Step-by-step setup wizard

### 2. Reverse Proxy Layer

#### Nginx Configuration
- **SSL/TLS Termination**: Handles HTTPS encryption
- **Static File Serving**: Serves CSS, JS, and image assets
- **Security Headers**: Implements comprehensive security policies
- **Load Balancing**: Can distribute traffic across multiple web instances
- **Gzip Compression**: Optimizes response sizes

#### Security Features
- Content Security Policy (CSP)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy
- HSTS (when SSL is enabled)

### 3. Application Layer

#### Flask Application
- **Architecture Pattern**: Application Factory with Blueprints
- **WSGI Server**: Gunicorn with multiple workers
- **Extensions**: Flask-SQLAlchemy, Flask-Login, Flask-Limiter, Flask-Migrate

#### Blueprint Structure
```
app/
├── __init__.py          # Application factory
├── config.py            # Configuration management
├── extensions.py        # Flask extensions
├── models/              # Database models
│   ├── user.py         # User authentication
│   ├── message.py      # Chat messages
│   ├── memory.py       # Long-term memory
│   └── setting.py      # User settings
├── services/            # Business logic
│   ├── ollama_client.py # LLM integration
│   ├── memory.py       # Memory management
│   ├── stt.py          # Speech-to-text
│   ├── tts.py          # Text-to-speech
│   ├── prompts.py      # Prompt engineering
│   ├── security.py     # Encryption utilities
│   └── tasks.py        # Background jobs
├── blueprints/          # Route handlers
│   ├── auth.py         # Authentication
│   ├── chat.py         # Chat interface
│   ├── settings.py     # Settings management
│   ├── admin.py        # Admin panel
│   ├── privacy.py      # Data privacy
│   ├── health.py       # Health checks
│   └── main.py         # Main routes
└── templates/           # HTML templates
```

### 4. Data Layer

#### PostgreSQL Database
- **Version**: 13+ with pgvector extension
- **Schema**: Normalized design with proper indexing
- **Extensions**: pgvector for vector similarity search

#### Database Models
```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    timezone VARCHAR(50),
    bio TEXT,
    preferences JSONB,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages table
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    conversation_id VARCHAR(50),
    metadata JSONB
);

-- Memories table with vector embeddings
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    content TEXT NOT NULL,
    embedding VECTOR(384), -- pgvector column
    memory_type VARCHAR(50),
    importance FLOAT DEFAULT 1.0,
    last_accessed TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Settings table
CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key VARCHAR(100) NOT NULL,
    value TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, key)
);
```

#### Redis Cache
- **Purpose**: Rate limiting, session storage, task queue
- **Data Structures**: 
  - Rate limiting buckets (per IP, per user)
  - Session data
  - Background job queue
  - Temporary data caching

### 5. AI Services Layer

#### Ollama Integration
- **Protocol**: HTTP REST API
- **Models**: Configurable LLM and embedding models
- **Features**: Text generation, embedding creation, model management
- **Fallback**: Local model support for offline operation

#### Speech Processing
- **STT (Speech-to-Text)**: faster-whisper integration
  - Model: Configurable (tiny, base, small, medium, large)
  - Input: 16kHz mono audio (WAV, MP3, M4A, FLAC, OGG, WEBM)
  - Output: Transcribed text with confidence scores
  
- **TTS (Text-to-Speech)**: OpenTTS/Piper integration
  - Protocol: HTTP API
  - Voices: Multiple language and gender options
  - Output: Streaming audio (WAV format)
  - Customization: Speed, pitch, voice selection

### 6. Memory System

#### Vector Embeddings
- **Technology**: pgvector with PostgreSQL
- **Model**: Configurable embedding model (default: nomic-embed-text)
- **Dimensions**: 384-dimensional vectors
- **Similarity**: Cosine distance for memory retrieval

#### Memory Types
- **Conversation**: Chat history summaries
- **Preference**: User likes/dislikes
- **Fact**: Important information about user
- **Conversation Summary**: AI-generated conversation summaries

#### Memory Management
- **Automatic Creation**: Generated during conversations
- **Importance Scoring**: Dynamic scoring based on usage and age
- **Compaction**: Merging similar memories to reduce redundancy
- **Cleanup**: Automatic removal of old, low-importance memories

### 7. Security Architecture

#### Authentication
- **Method**: Session-based with secure cookies
- **Password Hashing**: bcrypt with configurable rounds
- **Session Management**: Redis-backed sessions with expiration
- **CSRF Protection**: Token-based protection on all forms

#### Data Protection
- **Encryption**: Fernet symmetric encryption for sensitive settings
- **Key Management**: Environment variable-based key storage
- **Data Privacy**: User data isolation and export/deletion capabilities

#### Rate Limiting
- **Per IP**: 100 requests per minute
- **Per User**: 50 requests per minute
- **Special Limits**: STT (30/min), TTS (100/min)
- **Storage**: Redis-based with sliding window

### 8. Background Processing

#### Task Queue
- **Technology**: Redis Queue (RQ)
- **Job Types**:
  - Conversation summarization
  - Memory compaction
  - Importance score updates
  - Scheduled maintenance

#### Scheduled Tasks
- **Frequency**: Daily, weekly, monthly
- **Operations**: Database maintenance, memory cleanup, performance optimization

## Deployment Architecture

### Container Structure
```yaml
services:
  web:           # Flask application
  nginx:         # Reverse proxy
  db:            # PostgreSQL + pgvector
  redis:         # Cache and queue
  opentts:       # TTS service (optional)
  ollama:        # LLM service (optional)
```

### Network Configuration
- **Internal Network**: Docker bridge network for service communication
- **External Access**: Only Nginx exposed to host network
- **Port Mapping**: 80/443 (HTTP/HTTPS) → Nginx → Web (8000)

### Volume Management
- **Database**: Persistent PostgreSQL data
- **Redis**: Persistent cache data
- **TTS**: Voice model storage
- **Certificates**: SSL certificate storage

## Scalability Considerations

### Horizontal Scaling
- **Web Workers**: Multiple Gunicorn workers per container
- **Load Balancing**: Nginx can distribute across multiple web instances
- **Database**: Read replicas for query distribution
- **Cache**: Redis cluster for high availability

### Performance Optimization
- **Database Indexing**: Proper indexes on frequently queried columns
- **Connection Pooling**: SQLAlchemy connection pooling
- **Caching Strategy**: Redis-based caching for expensive operations
- **Async Processing**: Background task processing for heavy operations

### Monitoring and Observability
- **Health Checks**: Comprehensive service health monitoring
- **Logging**: Structured logging with correlation IDs
- **Metrics**: Performance metrics collection
- **Alerting**: Automated alerting for service issues

## Development Workflow

### Local Development
- **Docker Compose**: Full stack development environment
- **Hot Reloading**: Flask development server with auto-reload
- **Database Migrations**: Alembic for schema management
- **Testing**: Pytest with test database

### CI/CD Pipeline
- **GitHub Actions**: Automated testing and deployment
- **Testing**: Unit tests, integration tests, security scans
- **Quality Gates**: Code quality, test coverage, security checks
- **Deployment**: Automated deployment to staging/production

## Future Enhancements

### Planned Features
- **WebSocket Support**: Real-time chat updates
- **Multi-language Support**: Internationalization
- **Advanced Analytics**: User behavior insights
- **Plugin System**: Extensible functionality
- **Mobile App**: Native mobile applications

### Technical Improvements
- **GraphQL API**: Alternative to REST endpoints
- **Microservices**: Further service decomposition
- **Event Sourcing**: Audit trail and event replay
- **Machine Learning**: Advanced memory optimization
- **Edge Computing**: Distributed deployment options
