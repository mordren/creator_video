# providers/__init__.py
import os
from .base_texto import make_provider, ModelParams
from .base_imagem import make_image_provider, ImageParams

def create_text_provider(provider_name: str = None, **kwargs):
    """Factory compatível com o sistema de registry"""
    provider_name = (provider_name or "gemini").lower()
    
    # Usa o sistema de registry existente (que já tem os aliases)
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

def create_image_provider(provider_name: str = None, **kwargs):
    """Factory para providers de imagem - mesma lógica do texto"""
    provider_name = (provider_name or "grok").lower()
    
    # Usa o sistema de registry de imagens (com aliases)
    return make_image_provider(provider_name, **kwargs)

# Exporta também as funções do sistema de registry
from .base_texto import register_provider, TextoProvider
from .base_imagem import register_image_provider, ImageProvider

__all__ = [
    'create_text_provider', 
    'create_tts_provider',
    'create_image_provider',
    'make_provider',
    'make_image_provider',
    'register_provider', 
    'register_image_provider',
    'TextoProvider',
    'ImageProvider',
    'ModelParams',
    'ImageParams'
]

# Precarrega providers para registro automático
try:
    from . import claude_text
except Exception:
    pass

try:
    from . import gemini_text
except Exception:
    pass

try:
    from . import grok_text
except Exception:
    pass

try:
    from . import stable_imagem  
except Exception as e:
    print(f"⚠️ Aviso: Não foi possível importar stable_image: {e}")
    
try:
    from . import grok_imagem
except Exception as e:
    print(f"⚠️ Aviso: Não foi possível importar xai_image: {e}")

