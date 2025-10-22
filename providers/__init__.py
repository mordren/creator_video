from .edge_tts import EdgeTTSProvider

def create_tts_provider(provider_name: str):
    """
    Factory function para criar instâncias de provedores TTS
    
    Args:
        provider_name: Nome do provedor ('edge')
    
    Returns:
        Instância do provedor TTS
        
    Raises:
        ValueError: Se o provedor não for suportado
    """
    providers = {
        'edge': EdgeTTSProvider,
    }
    
    provider_name = provider_name.lower().strip()
    
    if provider_name not in providers:
        supported = ", ".join(f"'{p}'" for p in providers.keys())
        raise ValueError(f"Provedor TTS não suportado: '{provider_name}'. Provedores disponíveis: {supported}")
    
    return providers[provider_name]()

# Exportações públicas
__all__ = ['create_tts_provider', 'EdgeTTSProvider']