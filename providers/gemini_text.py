# providers/gemini_text.py
import os
import google.generativeai as genai
from typing import Dict, Any
import json
import re

# Import relativo corrigido
from .base_texto import TextoProvider, ModelParams, register_provider

@register_provider("gemini_text")
class GeminiTextProvider(TextoProvider):
    """Provider para Google Gemini com garantia de JSON perfeito"""
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não encontrada nas variáveis de ambiente")
        
        genai.configure(api_key=self.api_key)
        self.model_name = model or "gemini-2.0-flash"
    
    def _clean_json_response(self, text: str) -> Dict[str, Any]:
        """
        Limpa e extrai JSON da resposta do Gemini de forma ultra-robusta
        """
        print(f"🧹 Iniciando limpeza do JSON... Tamanho: {len(text)} chars")
        
        # Remove todos os caracteres de controle problemáticos
        def remove_control_chars(s: str) -> str:
            # Mantém apenas: tab (0x09), newline (0x0A), carriage return (0x0D)
            # Remove outros caracteres de controle (0x00-0x08, 0x0B-0x0C, 0x0E-0x1F, 0x7F)
            return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', s)
        
        # Estratégia 1: Tenta encontrar JSON entre ```json ```
        if '```json' in text:
            print("📦 Tentando extrair de bloco markdown JSON...")
            match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
            if match:
                json_text = match.group(1).strip()
                json_text = remove_control_chars(json_text)
                print(f"✅ JSON extraído do markdown: {len(json_text)} chars")
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError as e:
                    print(f"❌ Falha no parsing do markdown: {e}")
        
        # Estratégia 2: Tenta encontrar qualquer objeto JSON
        print("📦 Buscando padrão JSON no texto...")
        json_patterns = [
            r'\{[\s\S]*\}',  # Qualquer objeto JSON
            r'\{.*\}',       # Objeto JSON simples
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                clean_match = remove_control_chars(match)
                try:
                    data = json.loads(clean_match)
                    if isinstance(data, dict) and data:
                        print(f"✅ JSON extraído via padrão: {list(data.keys())}")
                        return data
                except json.JSONDecodeError:
                    continue
        
        # Estratégia 3: Primeiro { até último }
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            json_candidate = text[start:end]
            json_candidate = remove_control_chars(json_candidate)
            try:
                data = json.loads(json_candidate)
                if isinstance(data, dict):
                    print(f"✅ JSON extraído via primeiro-último: {list(data.keys())}")
                    return data
            except json.JSONDecodeError as e:
                print(f"❌ Falha no primeiro-último: {e}")
        
        # Se tudo falhar, levanta exceção
        raise ValueError(f"Não foi possível extrair JSON válido. Texto recebido: {text[:500]}...")
    
    def _create_fallback_structure(self, raw_text: str, prompt: str) -> Dict[str, Any]:
        """
        Cria estrutura de fallback quando o JSON não pode ser extraído
        """
        print("🛡️  Criando estrutura de fallback...")
        
        # Extrai informações úteis do texto bruto
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        
        # Tenta encontrar um título nas primeiras linhas
        titulo = "Spiritual Reflection"
        for line in lines[:3]:
            if line and len(line) > 10 and len(line) < 100 and not line.startswith('{'):
                clean_line = re.sub(r'[`*_{}\[\]()]', '', line)
                if clean_line:
                    titulo = clean_line[:60]
                    break
        
        # Determina se é morning ou night prayer baseado no tema
        is_night = any(word in prompt.lower() for word in ['night', 'evening', 'sleep', 'rest', 'end'])
        prayer_type = "Night Prayer" if is_night else "Morning Prayer"
        
        return {
            "texto": raw_text[:2000],  # Limita o tamanho
            "titulo": f"{titulo} | {prayer_type}",
            "descricao": "A moment of prayer and spiritual reflection",
            "hook": "Find peace in God's presence",
            "hook_pt": "Encontre paz na presença de Deus",
            "thumb": "prayer peace god",
            "tags": ["#prayer", "#faith", "#christian", "#peace", "#god"]
        }
    
    def generate(self, prompt: str) -> Dict[str, Any]:
        """Gera conteúdo usando Gemini com garantia de JSON perfeito"""
        try:
            # Cria modelo
            model = genai.GenerativeModel(self.model_name)
            
            # Gera conteúdo
            response = model.generate_content(
                prompt,                
            )
            
            # Verifica se há resposta
            if not response or not response.text:
                raise ValueError("Resposta vazia do Gemini")
            
            # Tenta extrair JSON da resposta
            try:
                resultado = self._clean_json_response(response.text)                
                return resultado
                
            except Exception as json_error:
                print(f"⚠️ Falha na extração JSON: {json_error}")
                print("🔄 Usando fallback...")
                
                # Cria estrutura de fallback
                fallback_data = self._create_fallback_structure(response.text, prompt)
                print(f"🛡️  Fallback criado: {list(fallback_data.keys())}")
                return fallback_data
            
        except Exception as e:
            error_msg = f"Erro no Gemini: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Debug adicional
            if hasattr(e, 'details'):
                print(f"🔍 Detalhes do erro: {e.details}")
            
            raise RuntimeError(error_msg)