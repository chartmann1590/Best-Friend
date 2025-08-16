# OpenTTS Integration Guide

## Overview

OpenTTS (Open Text-to-Speech) is an open-source, multilingual text-to-speech system that provides high-quality voice synthesis for the Best Friend AI Companion. This document explains how OpenTTS works, how to set it up, and how to manage voices.

## What is OpenTTS?

OpenTTS is a free, open-source text-to-speech server that:
- Supports multiple languages and voices
- Provides RESTful API endpoints
- Supports various TTS engines (Piper, Coqui, etc.)
- Offers real-time speech synthesis
- Allows custom voice training and management

## Architecture

```
┌─────────────────┐    HTTP/HTTPS    ┌─────────────────┐
│   Best Friend   │ ◄──────────────► │    OpenTTS      │
│     App         │                  │     Server      │
└─────────────────┘                  └─────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │   TTS Engine    │
                                    │   (Piper, etc.) │
                                    └─────────────────┘
```

## Features

### Core Capabilities
- **Real-time Synthesis**: Generate speech on-demand
- **Multiple Voices**: Support for various voice types and languages
- **Streaming Audio**: Stream audio for real-time playback
- **Voice Management**: Add, remove, and configure voices
- **Quality Control**: Adjustable speed, pitch, and audio quality

### Supported TTS Engines
- **Piper**: High-quality neural TTS (recommended)
- **Coqui TTS**: Advanced neural TTS with multiple models
- **Festival**: Traditional rule-based TTS
- **Custom Engines**: Support for custom TTS implementations

## Installation & Setup

### Docker Compose (Recommended)

```yaml
# docker-compose.yml
services:
  opentts:
    image: synesthesiam/opentts:latest
    ports:
      - "5500:5500"
    volumes:
      - opentts_data:/app/voices
      - opentts_config:/app/config
    environment:
      - TTS_ENGINE=piper
      - TTS_VOICES_PATH=/app/voices
    restart: unless-stopped

volumes:
  opentts_data:
  opentts_config:
```

### Manual Installation

```bash
# Clone OpenTTS repository
git clone https://github.com/synesthesiam/opentts.git
cd opentts

# Install dependencies
pip install -r requirements.txt

# Run OpenTTS
python -m opentts --port 5500
```

### Configuration

```bash
# Environment variables
export TTS_ENGINE=piper
export TTS_VOICES_PATH=/path/to/voices
export TTS_CACHE_PATH=/path/to/cache
export TTS_LOG_LEVEL=INFO
```

## Voice Management

### Understanding Voice Structure

OpenTTS voices are organized as follows:
```
voices/
├── en_US-amy-low/
│   ├── model.onnx          # Neural model file
│   ├── config.json         # Voice configuration
│   └── README.md           # Voice documentation
├── en_US-amy-medium/
│   ├── model.onnx
│   ├── config.json
│   └── README.md
└── es_ES-m-ailabs-low/
    ├── model.onnx
    ├── config.json
    └── README.md
```

### Adding New Voices

#### Method 1: Download Pre-trained Models

```bash
# Download Piper voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/low/en_US-amy-low.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/low/en_US-amy-low.onnx.json

# Create voice directory
mkdir -p voices/en_US-amy-low

# Move files
mv en_US-amy-low.onnx voices/en_US-amy-low/model.onnx
mv en_US-amy-low.onnx.json voices/en_US-amy-low/config.json
```

#### Method 2: Use OpenTTS Voice Manager

```bash
# Install voice manager
pip install opentts-voice-manager

# List available voices
opentts-voice-manager list

# Download specific voice
opentts-voice-manager download en_US-amy-low

# Install voice
opentts-voice-manager install en_US-amy-low
```

#### Method 3: Custom Voice Training

```bash
# Prepare training data
mkdir custom_voice
# Add audio files and transcripts

# Train with Piper
piper-train --config config.json --data_dir custom_voice

# Convert to ONNX format
piper-convert model.pth config.json model.onnx
```

### Voice Configuration

Each voice has a `config.json` file:

```json
{
  "name": "en_US-amy-low",
  "language": "en-US",
  "gender": "female",
  "description": "Amy - Low quality English voice",
  "sample_rate": 22050,
  "espeak_voice": "en-us",
  "length_scale": 1.0,
  "noise_scale": 0.667,
  "noise_w": 0.8
}
```

### Removing Voices

```bash
# Remove voice directory
rm -rf voices/en_US-amy-low

# Restart OpenTTS to apply changes
docker restart opentts
```

## API Reference

### Core Endpoints

#### List Available Voices
```http
GET /api/voices
```

**Response:**
```json
[
  {
    "id": "en_US-amy-low",
    "name": "en_US-amy-low",
    "language": "en-US",
    "gender": "female",
    "description": "Amy - Low quality English voice"
  }
]
```

#### Synthesize Speech
```http
POST /api/tts
```

**Parameters:**
- `voice`: Voice ID (required)
- `text`: Text to synthesize (required)
- `speed`: Speech speed (0.5-2.0, default: 1.0)
- `pitch`: Voice pitch (0.5-2.0, default: 1.0)

**Example:**
```bash
curl -X POST "http://localhost:5500/api/tts" \
  -d "voice=en_US-amy-low" \
  -d "text=Hello, this is a test." \
  -d "speed=1.0" \
  -d "pitch=1.0" \
  --output speech.wav
```

#### Get Voice Information
```http
GET /api/voices/{voice_id}
```

#### Health Check
```http
GET /api/health
```

### Advanced Endpoints

#### Batch Synthesis
```http
POST /api/tts/batch
```

**Request Body:**
```json
{
  "voices": [
    {
      "voice": "en_US-amy-low",
      "text": "Hello world",
      "speed": 1.0
    }
  ]
}
```

#### Voice Statistics
```http
GET /api/voices/{voice_id}/stats
```

## Integration with Best Friend AI

### Configuration

In your Best Friend AI settings:

1. **TTS Server URL**: Set to your OpenTTS server (e.g., `http://10.0.0.121:5500`)
2. **Voice Selection**: Choose from available voices in the dropdown
3. **Test Connection**: Use the "Test" button to verify connectivity

### Voice Settings

- **Speaking Rate**: Adjust speech speed (0.5x to 2.0x)
- **Pitch**: Modify voice pitch (0.5x to 2.0x)
- **Voice**: Select from discovered voices

### Automatic Voice Discovery

The Best Friend AI automatically:
- Tests connection to your OpenTTS server
- Discovers all available voices
- Populates the voice dropdown
- Refreshes voice list on demand

## Troubleshooting

### Common Issues

#### Voice Not Found
```bash
# Check voice directory permissions
ls -la voices/

# Verify voice files exist
ls -la voices/en_US-amy-low/

# Check OpenTTS logs
docker logs opentts
```

#### Audio Quality Issues
```bash
# Adjust voice parameters
# Lower speed for clarity
# Adjust pitch for natural sound
# Check sample rate compatibility
```

#### Connection Problems
```bash
# Verify OpenTTS is running
curl http://localhost:5500/api/health

# Check firewall settings
sudo ufw status

# Verify port binding
netstat -tlnp | grep 5500
```

### Performance Optimization

#### Memory Management
```bash
# Limit voice cache size
export TTS_CACHE_SIZE=1000

# Enable voice preloading
export TTS_PRELOAD_VOICES=true
```

#### Audio Quality vs Speed
```bash
# High quality (slower)
export TTS_QUALITY=high

# Balanced (recommended)
export TTS_QUALITY=medium

# Fast (lower quality)
export TTS_QUALITY=fast
```

## Best Practices

### Voice Selection
- **Production**: Use medium or high quality voices
- **Development**: Use low quality voices for faster processing
- **Multilingual**: Install voices for all supported languages

### Server Management
- **Monitoring**: Set up health checks and logging
- **Backup**: Regularly backup voice configurations
- **Updates**: Keep OpenTTS updated for latest features

### Performance
- **Caching**: Enable voice caching for frequently used voices
- **Load Balancing**: Use multiple OpenTTS instances for high traffic
- **CDN**: Consider CDN for voice file distribution

## Advanced Features

### Custom Voice Training

```bash
# Install training tools
pip install piper-train

# Prepare training data
# - High-quality audio recordings
# - Accurate transcriptions
# - Consistent speaking style

# Train model
piper-train --config config.json --data_dir training_data

# Validate model
piper-validate model.onnx
```

### Voice Cloning

```bash
# Use Coqui TTS for voice cloning
pip install TTS

# Clone voice from sample
tts --text "Hello world" \
    --model_path path/to/model \
    --out_path output.wav
```

### Multi-language Support

```bash
# Install voices for multiple languages
opentts-voice-manager download en_US-amy-low
opentts-voice-manager download es_ES-m-ailabs-low
opentts-voice-manager download fr_FR-m-ailabs-low
opentts-voice-manager download de_DE-m-ailabs-low
```

## Security Considerations

### Network Security
- **HTTPS**: Use SSL/TLS for production deployments
- **Firewall**: Restrict access to OpenTTS server
- **Authentication**: Implement API key authentication if needed

### Voice Security
- **Validation**: Validate all input text for malicious content
- **Rate Limiting**: Implement request rate limiting
- **Monitoring**: Log all synthesis requests for audit

## Monitoring & Logging

### Health Checks
```bash
# Basic health check
curl http://localhost:5500/api/health

# Detailed status
curl http://localhost:5500/api/status
```

### Logging
```bash
# View OpenTTS logs
docker logs opentts

# Set log level
export TTS_LOG_LEVEL=DEBUG
```

### Metrics
- **Request Count**: Total TTS requests
- **Response Time**: Average synthesis time
- **Error Rate**: Failed requests percentage
- **Voice Usage**: Most popular voices

## Support & Resources

### Official Documentation
- [OpenTTS GitHub](https://github.com/synesthesiam/opentts)
- [Piper TTS](https://github.com/rhasspy/piper)
- [Coqui TTS](https://github.com/coqui-ai/TTS)

### Community
- [OpenTTS Discussions](https://github.com/synesthesiam/opentts/discussions)
- [Piper TTS Issues](https://github.com/rhasspy/piper/issues)

### Training Resources
- [Voice Training Guide](https://github.com/rhasspy/piper/blob/master/TRAINING.md)
- [Audio Preparation](https://github.com/rhasspy/piper/blob/master/AUDIO.md)

---

*This documentation is part of the Best Friend AI Companion project. For more information, see the main [README.md](../README.md) file.*
