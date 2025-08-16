# Ollama Integration Guide

## Overview

Ollama is a powerful, open-source large language model (LLM) server that provides high-performance AI inference for the Best Friend AI Companion. This document explains how Ollama works, how to manage models, and how to integrate it with your application.

## What is Ollama?

Ollama is a lightweight, fast, and user-friendly LLM server that:
- Runs large language models locally or remotely
- Supports multiple model formats (GGUF, ONNX, etc.)
- Provides RESTful API endpoints
- Offers high-performance inference
- Allows easy model management and switching

## Architecture

```
┌─────────────────┐    HTTP/HTTPS    ┌─────────────────┐
│   Best Friend   │ ◄──────────────► │     Ollama      │
│     App         │                  │     Server      │
└─────────────────┘                  └─────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │   LLM Models    │
                                    │ (llama3.1, etc.)│
                                    └─────────────────┘
```

## Features

### Core Capabilities
- **High Performance**: Optimized inference with various backends
- **Multiple Models**: Support for various LLM architectures
- **Real-time Generation**: Stream responses for interactive chat
- **Model Management**: Easy model downloading and switching
- **API Compatibility**: RESTful API with streaming support

### Supported Model Types
- **Llama Models**: Llama 2, Llama 3, Code Llama
- **Mistral Models**: Mistral 7B, Mixtral 8x7B
- **Code Models**: CodeLlama, StarCoder, WizardCoder
- **Chat Models**: Vicuna, Alpaca, ChatGLM
- **Custom Models**: GGUF, ONNX, and other formats

## Installation & Setup

### Docker Compose (Recommended)

```yaml
# docker-compose.yml
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
      - OLLAMA_ORIGINS=*
    restart: unless-stopped

volumes:
  ollama_data:
```

### Manual Installation

#### Linux/macOS
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve
```

#### Windows
```bash
# Download from https://ollama.ai/download
# Run installer and follow prompts
```

### Configuration

```bash
# Environment variables
export OLLAMA_HOST=0.0.0.0
export OLLAMA_ORIGINS=*
export OLLAMA_MODELS=/path/to/models
export OLLAMA_KEEP_ALIVE=5m
```

## Model Management

### Understanding Model Structure

Ollama models are organized as follows:
```
~/.ollama/
├── models/
│   ├── llama3.1:8b/
│   │   ├── model.gguf          # Model weights
│   │   ├── config.json         # Model configuration
│   │   └── tokenizer.json      # Tokenizer configuration
│   ├── mistral:7b/
│   │   ├── model.gguf
│   │   ├── config.json
│   │   └── tokenizer.json
│   └── codellama:7b/
│       ├── model.gguf
│       ├── config.json
│       └── tokenizer.json
```

### Adding New Models

#### Method 1: Pull from Ollama Library

```bash
# List available models
ollama list

# Pull specific model
ollama pull llama3.1:8b

# Pull with specific tag
ollama pull llama3.1:8b-instruct

# Pull custom model
ollama pull custom-model:latest
```

#### Method 2: Create Custom Modelfile

```bash
# Create Modelfile
cat > Modelfile << EOF
FROM llama3.1:8b
PARAMETER temperature 0.7
PARAMETER top_p 0.9
SYSTEM "You are a helpful AI assistant."
EOF

# Build custom model
ollama create my-assistant -f Modelfile

# Run custom model
ollama run my-assistant
```

#### Method 3: Import Existing Models

```bash
# Import GGUF model
ollama create my-model -f Modelfile

# Modelfile content:
# FROM ./path/to/model.gguf
# PARAMETER temperature 0.7
```

### Model Configuration

Each model can be configured with parameters:

```bash
# Set model parameters
ollama run llama3.1:8b --temperature 0.7 --top-p 0.9

# Create model with specific parameters
cat > Modelfile << EOF
FROM llama3.1:8b
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
SYSTEM "You are a helpful AI assistant."
EOF

ollama create my-assistant -f Modelfile
```

### Removing Models

```bash
# Remove specific model
ollama rm llama3.1:8b

# Remove all models
ollama rm --all

# Clean up unused models
ollama prune
```

## API Reference

### Core Endpoints

#### Generate Response
```http
POST /api/generate
```

**Request Body:**
```json
{
  "model": "llama3.1:8b",
  "prompt": "Hello, how are you?",
  "stream": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "repeat_penalty": 1.1
  }
}
```

**Response:**
```json
{
  "model": "llama3.1:8b",
  "created_at": "2024-01-01T00:00:00Z",
  "response": "Hello! I'm doing well, thank you for asking.",
  "done": true,
  "context": [1, 2, 3],
  "total_duration": 1234567890,
  "load_duration": 123456789,
  "prompt_eval_duration": 123456789,
  "eval_duration": 123456789
}
```

#### Stream Response
```http
POST /api/generate
```

**Request Body:**
```json
{
  "model": "llama3.1:8b",
  "prompt": "Tell me a story",
  "stream": true
}
```

**Streaming Response:**
```json
{"model":"llama3.1:8b","created_at":"2024-01-01T00:00:00Z","response":"Once","done":false}
{"model":"llama3.1:8b","created_at":"2024-01-01T00:00:00Z","response":" upon","done":false}
{"model":"llama3.1:8b","created_at":"2024-01-01T00:00:00Z","response":" a","done":false}
{"model":"llama3.1:8b","created_at":"2024-01-01T00:00:00Z","response":" time","done":true}
```

#### List Models
```http
GET /api/tags
```

**Response:**
```json
{
  "models": [
    {
      "name": "llama3.1:8b",
      "modified_at": "2024-01-01T00:00:00Z",
      "size": 4294967296
    }
  ]
}
```

#### Generate Embeddings
```http
POST /api/embeddings
```

**Request Body:**
```json
{
  "model": "nomic-embed-text",
  "prompt": "Hello world"
}
```

**Response:**
```json
{
  "embedding": [0.1, 0.2, 0.3, ...]
}
```

### Advanced Endpoints

#### Chat Completion
```http
POST /api/chat
```

**Request Body:**
```json
{
  "model": "llama3.1:8b",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false
}
```

#### Model Information
```http
GET /api/show
```

**Query Parameters:**
- `name`: Model name

#### Copy Model
```http
POST /api/copy
```

**Request Body:**
```json
{
  "source": "llama3.1:8b",
  "destination": "my-llama"
}
```

## Integration with Best Friend AI

### Configuration

In your Best Friend AI settings:

1. **Ollama Server URL**: Set to your Ollama server (e.g., `http://10.0.0.121:11434`)
2. **Model Selection**: Choose from available models in the dropdown
3. **Test Connection**: Use the "Test" button to verify connectivity

### Model Settings

- **Temperature**: Controls randomness (0.0-2.0)
- **Top-P**: Controls diversity (0.1-1.0)
- **Model**: Select from discovered models

### Automatic Model Discovery

The Best Friend AI automatically:
- Tests connection to your Ollama server
- Discovers all available models
- Populates the model dropdown
- Refreshes model list on demand

## Performance Optimization

### Hardware Acceleration

#### GPU Acceleration
```bash
# Install CUDA support
docker run --gpus all -p 11434:11434 ollama/ollama:latest

# Set GPU layers
export OLLAMA_GPU_LAYERS=35
```

#### CPU Optimization
```bash
# Use multiple threads
export OLLAMA_NUM_THREADS=8

# Enable AVX instructions
export OLLAMA_CPU_ARCH=native
```

### Memory Management
```bash
# Limit model memory
export OLLAMA_MAX_MEMORY=8GB

# Enable model offloading
export OLLAMA_OFFLOAD_LAYERS=20
```

### Model Quantization
```bash
# Use quantized models for better performance
ollama pull llama3.1:8b-q4_0

# Create custom quantized model
ollama create my-model-q4 -f Modelfile
# Modelfile: FROM llama3.1:8b PARAMETER num_ctx 4096
```

## Troubleshooting

### Common Issues

#### Model Not Found
```bash
# Check model installation
ollama list

# Verify model files
ls -la ~/.ollama/models/

# Reinstall model
ollama rm llama3.1:8b
ollama pull llama3.1:8b
```

#### Performance Issues
```bash
# Check system resources
htop
nvidia-smi  # If using GPU

# Monitor Ollama logs
docker logs ollama

# Adjust model parameters
ollama run llama3.1:8b --num_ctx 2048
```

#### Connection Problems
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Check firewall settings
sudo ufw status

# Verify port binding
netstat -tlnp | grep 11434
```

### Debug Mode
```bash
# Enable debug logging
export OLLAMA_DEBUG=1

# Run with verbose output
ollama serve --verbose

# Check model loading
ollama show llama3.1:8b
```

## Best Practices

### Model Selection
- **Production**: Use stable, tested models
- **Development**: Use smaller models for faster iteration
- **Specialized Tasks**: Use domain-specific models (code, chat, etc.)

### Server Management
- **Monitoring**: Set up health checks and logging
- **Backup**: Regularly backup model configurations
- **Updates**: Keep Ollama updated for latest features

### Performance
- **Quantization**: Use quantized models for better performance
- **Context Length**: Optimize context length for your use case
- **Batch Processing**: Use batch inference for multiple requests

## Advanced Features

### Custom Model Training

```bash
# Fine-tune existing model
ollama create my-finetuned -f Modelfile

# Modelfile for fine-tuning:
# FROM llama3.1:8b
# PARAMETER temperature 0.7
# SYSTEM "You are a specialized assistant for..."
# TEMPLATE "{{.System}}\n\n{{.Prompt}}"
```

### Model Merging

```bash
# Create model from multiple sources
cat > Modelfile << EOF
FROM llama3.1:8b
FROM mistral:7b
PARAMETER temperature 0.7
SYSTEM "You are a helpful assistant."
EOF

ollama create merged-model -f Modelfile
```

### Multi-model Deployment

```bash
# Run multiple Ollama instances
docker run -d -p 11434:11434 --name ollama-main ollama/ollama:latest
docker run -d -p 11435:11434 --name ollama-secondary ollama/ollama:latest

# Load different models on each instance
docker exec ollama-main ollama pull llama3.1:8b
docker exec ollama-secondary ollama pull mistral:7b
```

## Security Considerations

### Network Security
- **HTTPS**: Use SSL/TLS for production deployments
- **Firewall**: Restrict access to Ollama server
- **Authentication**: Implement API key authentication if needed

### Model Security
- **Validation**: Validate all input prompts for malicious content
- **Rate Limiting**: Implement request rate limiting
- **Monitoring**: Log all generation requests for audit

### Data Privacy
- **Local Deployment**: Run Ollama locally for sensitive data
- **Model Isolation**: Use separate models for different user groups
- **Data Retention**: Implement data retention policies

## Monitoring & Logging

### Health Checks
```bash
# Basic health check
curl http://localhost:11434/api/tags

# Detailed status
curl http://localhost:11434/api/show -d '{"name":"llama3.1:8b"}'
```

### Logging
```bash
# View Ollama logs
docker logs ollama

# Set log level
export OLLAMA_LOG_LEVEL=DEBUG
```

### Metrics
- **Request Count**: Total generation requests
- **Response Time**: Average generation time
- **Error Rate**: Failed requests percentage
- **Model Usage**: Most popular models

## Support & Resources

### Official Documentation
- [Ollama Website](https://ollama.ai)
- [Ollama GitHub](https://github.com/ollama/ollama)
- [Ollama Models](https://ollama.ai/library)

### Community
- [Ollama Discord](https://discord.gg/ollama)
- [Ollama Discussions](https://github.com/ollama/ollama/discussions)

### Model Resources
- [Hugging Face Models](https://huggingface.co/models)
- [Ollama Model Library](https://ollama.ai/library)
- [GGUF Model Hub](https://huggingface.co/TheBloke)

---

*This documentation is part of the Best Friend AI Companion project. For more information, see the main [README.md](../README.md) file.*
