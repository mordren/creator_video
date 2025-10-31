from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any

class TTSProvider(ABC):
    """Interface base para provedores de TTS"""
    
    @abstractmethod
    def sintetizar(self, texto: str, output_path: Path, config: Dict[str, Any],  is_short = bool) -> bool:
        """
        Sintetiza texto em áudio
        
        Args:
            texto: Texto para sintetizar
            output_path: Caminho onde salvar o arquivo de áudio
            config: Configurações do canal
            
        Returns:
            True se bem-sucedido, False caso contrário
        """
        pass