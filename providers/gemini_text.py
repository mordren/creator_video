# providers/gemini_text.py
import os
import google.generativeai as genai
from typing import Dict, Any

# Import relativo corrigido
from .base_texto import TextoProvider, ModelParams, register_provider

# Import do utils
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils import extract_json_maybe


@register_provider("gemini_text")
class GeminiTextProvider(TextoProvider):
    """Provider para Google Gemini"""
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não encontrada nas variáveis de ambiente")
        
        genai.configure(api_key=self.api_key)
        self.model_name = model or "gemini-2.0-flash"
    
    def generate(self, prompt: str, params: ModelParams) -> Dict[str, Any]:
        """Gera conteúdo usando Gemini"""
        try:
            # Cria modelo (não criar no init para evitar problemas com diferentes params)
            model = genai.GenerativeModel(self.model_name)
            
            # Configura geração
            generation_config = {
                "temperature": params.temperature,
                "top_p": params.top_p,
                "max_output_tokens": params.max_output_tokens,
            }
            
            if params.seed:
                generation_config["seed"] = params.seed
            
            print(f"🔧 Enviando prompt para Gemini...")
            print(f"📝 Prompt preview: {prompt[:200]}...")
            
            # Gera conteúdo
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Verifica se há resposta
            if not response or not response.text:
                raise ValueError("Resposta vazia do Gemini")
            
            # Processa resposta para extrair JSON
            resultado = extract_json_maybe(response.text)
            
            if not resultado:
                raise ValueError("Não foi possível extrair JSON da resposta do Gemini")
                
            return resultado
            
        except Exception as e:
            # ✅ CORREÇÃO: Não tenta acessar response.text se response não foi definida
            error_msg = f"Erro no Gemini: {e}"
            print(f"❌ {error_msg}")
            
            # Debug adicional para entender o erro
            if hasattr(e, 'details'):
                print(f"🔍 Detalhes do erro: {e.details}")
            
            raise RuntimeError(error_msg)