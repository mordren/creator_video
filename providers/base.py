from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any

class TTSProvider(ABC):
    """Interface base para provedores de TTS"""
    
    @abstractmethod
    def sintetizar(self, texto: str, output_path: Path, config: Dict[str, Any]) -> bool:
        pass