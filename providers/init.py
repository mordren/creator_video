from .edge_tts import EdgeTTSProvider

def create_tts_provider(provider_name: str):
    providers = {
        'edge': EdgeTTSProvider,
    }
    
    if provider_name not in providers:
        raise ValueError(f"Provedor TTS não suportado: {provider_name}")
    
    return providers[provider_name]()

__all__ = ['create_tts_provider', 'EdgeTTSProvider']