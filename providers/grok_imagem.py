# providers/xai_image.py
import os
import requests
from datetime import datetime
from pathlib import Path
from .base_imagem import ImageProvider, register_image_provider, ImageParams


@register_image_provider("grok_imagem")
class XAIImageProvider(ImageProvider):
    """Provider para geração de imagens usando xAI"""
    
    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("❌ XAI_API_KEY não encontrada nas variáveis de ambiente")
        
        self.endpoint = "https://api.x.ai/v1/images/generations"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate_image(self, prompt: str, params: ImageParams = None, pasta_video: Path = None) -> dict:
        """Gera imagem usando API xAI - corrigido sem parâmetro quality"""
        
        if params is None:
            params = ImageParams()
        
        # ✅ CORREÇÃO: Removido o parâmetro 'quality' que não é suportado
        payload = {
            "model": "grok-2-image",
            "prompt": prompt,            
            "image_format": "url"
        }
        
        try:
            print(f"🖼️ Enviando prompt para geração de imagem...")
            response = requests.post(self.endpoint, headers=self.headers, json=payload, timeout=60)
            
            if response.status_code != 200:
                raise RuntimeError(f"API retornou {response.status_code}: {response.text}")
            
            data = response.json()
            image_url = data['data'][0]['url']
            
            # Baixar e salvar a imagem na pasta do vídeo
            return self._download_image(image_url, pasta_video)
            
        except Exception as e:
            print(f"❌ Erro ao gerar imagem: {e}")
            raise

    def _download_image(self, image_url: str, pasta_video: Path) -> dict:
        """Baixa a imagem e salva na pasta do vídeo"""
        
        # Criar subpasta para imagens dentro da pasta do vídeo
        images_dir = pasta_video / "images"
        images_dir.mkdir(exist_ok=True)
        
        # Gerar nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"background_{timestamp}.jpg"
        filepath = images_dir / filename
        
        # Baixar imagem
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Salvar arquivo
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Imagem salva em: {filepath}")
        
        return {
            "filepath": str(filepath),
            "filename": filename,
            "url": image_url,
            "size": len(response.content),
            "resolution": "1280x720"
        }