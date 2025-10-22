# providers/__init__.py
import os
from .base_texto import make_provider, ModelParams

def create_text_provider(provider_name: str = None, **kwargs):
    """Factory compatível com o sistema de registry"""
    provider_name = (provider_name or "gemini").lower()
    
    # Usa o sistema de registry existente
    return make_provider(provider_name, **kwargs)

def create_tts_provider(provider_name: str = None, **kwargs):
    """Factory simples para providers de TTS"""
    provider_name = (provider_name or "edge").lower()
    
    if provider_name == "edge":
        from .edge_tts import EdgeTTSProvider
        return EdgeTTSProvider()
    
    if provider_name == "gemini":
        from .gemini_tts import GeminiTTSProvider
        api_key = kwargs.get('api_key') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada para TTS")
        return GeminiTTSProvider()
    
    raise ValueError(f"TTS Provider '{provider_name}' não suportado")

# Exporta também as funções do sistema de registry
from .base_texto import register_provider, TextoProvider

__all__ = [
    'create_text_provider', 
    'create_tts_provider',
    'make_provider',
    'register_provider', 
    'TextoProvider',
    'ModelParams'
]