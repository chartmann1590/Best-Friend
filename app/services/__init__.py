from .ollama_client import OllamaClient
from .memory import MemoryService
from .stt import STTService
from .tts import TTSService
from .prompts import PromptService
from .security import SecurityService
from .content_filter import ContentFilterService

def init_services(app):
    """Initialize all services with the Flask app context."""
    app.ollama_client = OllamaClient(app)
    app.memory_service = MemoryService(app)
    app.stt_service = STTService(app)
    app.tts_service = TTSService(app)
    app.prompt_service = PromptService(app)
    app.security_service = SecurityService(app)
    app.content_filter = ContentFilterService(app)
