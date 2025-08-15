# API Documentation

This document describes the REST API endpoints for the Best Friend AI Companion application.

## Base URL

All API endpoints are prefixed with `/api/`

## Authentication

Most API endpoints require authentication. Include your session cookie or use the login endpoint to authenticate.

## Endpoints

### Chat

#### POST /api/chat

Send a message to the AI companion.

**Request Body:**
```json
{
    "message": "Hello, how are you today?"
}
```

**Response:**
```json
{
    "response": "Hello! I'm doing well, thank you for asking. How about you?",
    "message_id": 123
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad request (missing message)
- `401` - Unauthorized
- `429` - Rate limit exceeded

---

#### POST /api/stt

Convert speech to text.

**Request:**
- `Content-Type: multipart/form-data`
- `audio`: Audio file (WAV, MP3, M4A, FLAC, OGG, WEBM)

**Response:**
```json
{
    "text": "Hello, this is a test message",
    "confidence": 0.95,
    "language": "en",
    "language_probability": 0.99,
    "segments": 1
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad request (no audio file)
- `401` - Unauthorized
- `429` - Rate limit exceeded

---

#### GET /api/tts/stream

Generate speech from text.

**Query Parameters:**
- `text` (required): Text to convert to speech
- `voice` (optional): Voice ID (default: user's configured voice)
- `speed` (optional): Speaking rate (0.5-2.0, default: 1.0)
- `pitch` (optional): Pitch (0.5-2.0, default: 1.0)

**Response:**
- `Content-Type: audio/wav`
- Audio data stream

**Status Codes:**
- `200` - Success
- `400` - Bad request (missing text)
- `401` - Unauthorized
- `429` - Rate limit exceeded

---

#### GET /api/memory/search

Search user memories using vector similarity.

**Query Parameters:**
- `q` (required): Search query
- `limit` (optional): Maximum results (default: 10)
- `threshold` (optional): Similarity threshold (0.0-1.0, default: 0.5)

**Response:**
```json
{
    "memories": [
        {
            "id": 1,
            "content": "User mentioned they like hiking",
            "memory_type": "preference",
            "relevance": 0.85,
            "created_at": "2024-01-01T12:00:00Z"
        }
    ],
    "query": "hiking"
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad request (missing query)
- `401` - Unauthorized

---

### Settings

#### GET /settings

Get user settings page.

**Response:**
- HTML page with settings form

**Status Codes:**
- `200` - Success
- `401` - Unauthorized

---

#### POST /settings

Update user settings.

**Request Body:**
```json
{
    "name": "John Doe",
    "timezone": "America/New_York",
    "bio": "I love technology and AI",
    "ollama_url": "http://ollama:11434",
    "ollama_model": "llama3.1:8b",
    "personality": "You are a helpful AI companion...",
    "tts_url": "http://opentts:5500",
    "tts_voice": "en_US-amy-low",
    "speaking_rate": "1.0",
    "pitch": "1.0",
    "memory_enabled": "true",
    "auto_summarize": "true",
    "share_analytics": "false"
}
```

**Response:**
- Redirect to settings page with success message

**Status Codes:**
- `302` - Redirect (success)
- `401` - Unauthorized

---

#### GET /api/settings

Get user settings as JSON.

**Response:**
```json
{
    "name": "John Doe",
    "timezone": "America/New_York",
    "bio": "I love technology and AI",
    "ollama_url": "http://ollama:11434",
    "ollama_model": "llama3.1:8b",
    "personality": "You are a helpful AI companion...",
    "tts_url": "http://opentts:5500",
    "tts_voice": "en_US-amy-low",
    "speaking_rate": "1.0",
    "pitch": "1.0",
    "memory_enabled": "true",
    "auto_summarize": "true",
    "share_analytics": "false"
}
```

**Status Codes:**
- `200` - Success
- `401` - Unauthorized

---

### Privacy

#### GET /api/export

Export all user data.

**Response:**
- `Content-Type: application/json`
- `Content-Disposition: attachment; filename=bestfriend_export_*.json`

**Status Codes:**
- `200` - Success
- `401` - Unauthorized

---

#### DELETE /api/delete

Delete all user data.

**Response:**
```json
{
    "message": "All data deleted successfully"
}
```

**Status Codes:**
- `200` - Success
- `401` - Unauthorized
- `500` - Server error

---

### Authentication

#### GET /auth/login

Get login page.

**Response:**
- HTML login form

**Status Codes:**
- `200` - Success

---

#### POST /auth/login

Authenticate user.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "password123"
}
```

**Response:**
- Redirect to dashboard on success
- Login form with error message on failure

**Status Codes:**
- `200` - Success (with error message)
- `302` - Redirect (success)

---

#### GET /auth/logout

Logout user.

**Response:**
- Redirect to login page

**Status Codes:**
- `302` - Redirect

---

#### GET /auth/change-password

Get password change page.

**Response:**
- HTML password change form

**Status Codes:**
- `200` - Success
- `401` - Unauthorized

---

#### POST /auth/change-password

Change user password.

**Request Body:**
```json
{
    "current_password": "oldpassword",
    "new_password": "newpassword123",
    "confirm_password": "newpassword123"
}
```

**Response:**
- Redirect to dashboard with success message

**Status Codes:**
- `200` - Success (with error message)
- `302` - Redirect (success)
- `401` - Unauthorized

---

### Admin

#### GET /admin

Get admin dashboard.

**Response:**
- HTML admin dashboard

**Status Codes:**
- `200` - Success
- `401` - Unauthorized
- `403` - Forbidden (not admin)

---

#### GET /api/stats

Get system statistics.

**Response:**
```json
{
    "total_users": 5,
    "total_messages": 150,
    "total_memories": 75,
    "active_users": 3
}
```

**Status Codes:**
- `200` - Success
- `401` - Unauthorized
- `403` - Forbidden (not admin)

---

### Health

#### GET /healthz

Get system health status.

**Response:**
```json
{
    "status": "healthy",
    "services": {
        "database": "healthy",
        "redis": "healthy",
        "ollama": "healthy",
        "tts": "healthy"
    }
}
```

**Status Codes:**
- `200` - Success

---

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Per IP**: 100 requests per minute
- **Per User**: 50 requests per minute
- **STT**: 30 requests per minute
- **TTS**: 100 requests per minute

When rate limited, the API returns:
- `429 Too Many Requests`
- `Retry-After` header with seconds to wait

## Error Handling

All API endpoints return consistent error responses:

```json
{
    "error": "Error description",
    "details": "Additional error information (optional)"
}
```

Common HTTP status codes:
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (not authenticated)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error

## Data Models

### User
```json
{
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "timezone": "America/New_York",
    "bio": "I love technology and AI",
    "preferences": {},
    "is_admin": false,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
}
```

### Message
```json
{
    "id": 123,
    "role": "user",
    "content": "Hello, how are you?",
    "timestamp": "2024-01-01T12:00:00Z",
    "conversation_id": "conv_123",
    "metadata": {}
}
```

### Memory
```json
{
    "id": 1,
    "content": "User mentioned they like hiking",
    "memory_type": "preference",
    "importance": 0.8,
    "last_accessed": "2024-01-01T12:00:00Z",
    "created_at": "2024-01-01T12:00:00Z",
    "metadata": {}
}
```

### Setting
```json
{
    "id": 1,
    "key": "ollama_model",
    "value": "llama3.1:8b",
    "is_encrypted": false,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
}
```

## WebSocket Support

Future versions may include WebSocket endpoints for:
- Real-time chat streaming
- Live voice streaming
- Memory updates
- System notifications

## SDK Examples

### Python
```python
import requests

# Login
session = requests.Session()
response = session.post('https://localhost/auth/login', data={
    'email': 'user@example.com',
    'password': 'password123'
})

# Send chat message
response = session.post('https://localhost/api/chat', json={
    'message': 'Hello, AI!'
})
print(response.json()['response'])
```

### JavaScript
```javascript
// Send chat message
const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        message: 'Hello, AI!'
    })
});

const data = await response.json();
console.log(data.response);
```

### cURL
```bash
# Login
curl -c cookies.txt -X POST https://localhost/auth/login \
  -d "email=user@example.com&password=password123"

# Send chat message
curl -b cookies.txt -X POST https://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, AI!"}'
```

## Support

For API support:
1. Check the health endpoint: `GET /healthz`
2. Review error messages in responses
3. Check rate limiting headers
4. Consult the logs for detailed error information
5. Open an issue on GitHub for bugs or feature requests
