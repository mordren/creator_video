# providers/stable_imagem.py
import os
import requests
import json
from datetime import datetime
from pathlib import Path
import google.generativeai as genai
from .base_imagem import ImageProvider, register_image_provider, ImageParams

@register_image_provider("stable_imagem")
class StableImageProvider(ImageProvider):
    def __init__(self):
        self.stability_key = os.getenv("STABILITY_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        
        if not self.stability_key:
            raise ValueError("❌ STABILITY_API_KEY não encontrada")
        if not self.gemini_key:
            raise ValueError("❌ GEMINI_API_KEY não encontrada")
        
        self.stability_endpoint = "https://api.stability.ai/v2beta/stable-image/generate/core"
        self.gemini_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.gemini_key}"
        
        self.stability_headers = {
            "authorization": f"Bearer {self.stability_key}",
            "accept": "image/*"
        }
        self.gemini_headers = {
            "Content-Type": "application/json"
        }

    def generate_image(self, prompt_pt: str, params: ImageParams = None, pasta_video: Path = None) -> dict:
        """Recebe prompt em português, converte com Gemini e gera imagem com Stability AI"""
        
        if params is None:
            params = ImageParams()
        
        print(f"🔄 Convertendo prompt com Gemini...")
        prompt_en = self._convert_prompt_with_gemini(prompt_pt)
        
        print(f"🎯 Prompt em inglês: {prompt_en}")
        print(f"🖼️ Gerando imagem com Stability AI...")
        
        data = {
            "prompt": prompt_en,
            "output_format": "png",
            "aspect_ratio": "16:9"
        }
        
        if params.style and params.style != "natural":
            data["style"] = params.style
        
        try:
            response = requests.post(
                self.stability_endpoint,
                headers=self.stability_headers,
                files={"none": ''},
                data=data,
                timeout=120
            )
            
            if response.status_code != 200:
                error_msg = response.json() if response.content else "Unknown error"
                raise RuntimeError(f"Stability AI retornou {response.status_code}: {error_msg}")
            
            return self._save_image(response.content, pasta_video, prompt_en)
            
        except Exception as e:
            print(f"❌ Erro ao gerar imagem: {e}")
            raise

    def _convert_prompt_with_gemini(self, prompt_pt: str) -> str:
        """Converte prompt PT→EN usando Gemini"""
        
        system_prompt = f"""Convert this Portuguese image description into a professional, detailed Stable Diffusion prompt in English.

    PORTUGUESE INPUT: {prompt_pt}

    CRITICAL RULES - YOU MUST FOLLOW THESE:
    - Return ONLY the final English prompt, nothing else
    - Use specific, concrete visual details - not generic terms
    - Focus on: composition, lighting, style, colors, mood, details
    - Format: descriptive phrases separated by commas
    - Maximum 400 characters
    - Avoid abstract concepts - describe what we actually see
    - Make it visually specific and cinematic
    - Use professional photography/cinematography terms
    - Include technical details like lighting, camera angles, style

    EXAMPLES OF GOOD PROMPTS:
    - "Cinematic wide shot of a serene mountain landscape at golden hour, soft volumetric lighting, misty atmosphere, photorealistic, 8K, professional photography, shallow depth of field"
    - "Dark moody interior scene, dramatic chiaroscuro lighting, suspenseful atmosphere, cinematic, film noir style, high contrast, professional cinematography"
    - "Peaceful meditation scene in a minimalist room, soft natural lighting, warm color palette, shallow depth of field, photorealistic, 4K"

    NOW CREATE THE ENGLISH PROMPT:"""

        try:

            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(system_prompt)                      
            return response.text.strip()
            
        except Exception as e:
            print(f"❌ Erro na conversão Gemini: {e}")
            # Fallback: tradução simples

    def _clean_gemini_response(self, text: str) -> str:
        """Limpa a resposta do Gemini para pegar apenas o prompt"""
        import re
        
        # Remove possíveis explicações do Gemini
        lines = text.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            # Pega apenas linhas que parecem ser o prompt (não começam com explicações)
            if line and not line.lower().startswith(('here is', 'the prompt', 'prompt:', 'i have', 'sure', 'of course')):
                clean_lines.append(line)
        
        clean_text = ' '.join(clean_lines)
        
        # Remove aspas se existirem
        clean_text = re.sub(r'^["\']|["\']$', '', clean_text)
        
        # Limita tamanho
        if len(clean_text) > 300:
            clean_text = clean_text[:297] + "..."
            
        return clean_text

  

    def _save_image(self, image_data: bytes, pasta_video: Path, prompt_en: str) -> dict:
        """Salva a imagem e informações do prompt"""
        images_dir = pasta_video / "images"
        images_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"background_{timestamp}.png"
        filepath = images_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        # Salvar informações do prompt em um arquivo de metadados
        metadata = {
            "prompt_original": prompt_en,
            "generated_at": datetime.now().isoformat(),
            "filepath": str(filepath),
            "size_bytes": len(image_data),
            "resolution": "16:9 vertical",
            "provider": "stability_ai"
        }
        
        metadata_file = images_dir / f"metadata_{timestamp}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Imagem salva em: {filepath}")
        print(f"📏 Tamanho: {len(image_data)} bytes")
        print(f"📝 Prompt usado: {prompt_en[:100]}...")
        
        return {
            "filepath": str(filepath),
            "filename": filename,
            "size": len(image_data),
            "resolution": "1024x1792",
            "format": "png",
            "prompt_en": prompt_en,
            "metadata_file": str(metadata_file)
        }