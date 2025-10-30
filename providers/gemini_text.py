# providers/gemini_text.py
import os
import json
import google.generativeai as genai
from typing import Dict, Any
from .base_texto import TextoProvider, register_provider

@register_provider("gemini_text")
class GeminiTextProvider(TextoProvider):
    """Provider para Google Gemini com JSON Schema nativo"""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não encontrada nas variáveis de ambiente")
        genai.configure(api_key=self.api_key)
        self.model_name = model or "gemini-2.5-flash"

    def generate(self, prompt: str, json_schema: Dict = None) -> Dict[str, Any]:
        """Gera texto com o Gemini usando JSON Schema"""
        try:
            model = genai.GenerativeModel(self.model_name)
            
            # Se tem schema, usa generation config com JSON
            if json_schema:
                # 🔥 CORREÇÃO: Import correto para GenerationConfig
                from google.generativeai.types import GenerationConfig
                
                generation_config = GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=json_schema
                )
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
            else:
                # Fallback sem schema
                response = model.generate_content(prompt)
            
            if not response or not response.text:
                raise ValueError("Resposta vazia do Gemini")

            # Parse direto - já vem como JSON válido
            result = json.loads(response.text)
            print("✅ JSON válido recebido via Gemini Schema")
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON inválido mesmo com schema: {e}")
            if 'response' in locals():
                print(f"📝 Resposta: {response.text[:500]}...")
            raise
        except Exception as e:
            print(f"❌ Erro na geração: {e}")
            raise