# utils.py
from pathlib import Path
import json, re
from typing import Any, Dict

# tokenização de "palavra" robusta (acentos + hífen/contração)
_WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+(?:[-’'][A-Za-zÀ-ÖØ-öø-ÿ0-9]+)?", re.UNICODE)

def count_words(s: str) -> int:
    return len(_WORD.findall(re.sub(r"\s+", " ", s.strip())))

def truncate_words(s: str, n: int) -> str:
    out, seen = [], 0
    for chunk in re.split(r"(\W+)", s):
        if _WORD.fullmatch(chunk):
            if seen >= n: break
            seen += 1
        out.append(chunk)
    return "".join(out).strip()

# Em utils.py - função EXTRA ROBUSTA
def extract_json_maybe(text: str) -> dict:
    """
    Tenta extrair JSON de uma string, lidando com blocos de código markdown.
    Versão ULTRA-ROBUSTA.
    """
    import json
    import re
    
    # Se já for um dicionário, retorna diretamente
    if isinstance(text, dict):
        return text
    
    # Limpa a string
    text = text.strip()
    
    print(f"🔍 Texto recebido para extração JSON: {text[:200]}...")
    
    # CASO 1: É um bloco de código markdown com JSON
    if text.startswith('```json'):
        # Extrai o JSON do bloco de código
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            json_text = match.group(1).strip()
            print(f"✅ Encontrado bloco JSON markdown: ")
            try:
                data = json.loads(json_text)
                if isinstance(data, dict):
                    print(f"✅ JSON extraído do bloco markdown:")
                    return data
            except json.JSONDecodeError as e:
                print(f"❌ Erro ao decodificar JSON do bloco: {e}")
    
    # CASO 2: É um bloco de código genérico
    elif text.startswith('```'):
        match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            json_text = match.group(1).strip()
            print(f"✅ Encontrado bloco de código genérico: {json_text[:100]}...")
            try:
                data = json.loads(json_text)
                if isinstance(data, dict):
                    print(f"✅ JSON extraído do bloco genérico: {list(data.keys())}")
                    return data
            except json.JSONDecodeError:
                # Pode não ser JSON, então trata como texto normal
                pass
    
    # CASO 3: Tenta encontrar JSON com regex
    json_pattern = r'\{[^{}]*\{[^{}]*\}[^{}]*\}'  # Captura objetos JSON aninhados
    matches = re.findall(json_pattern, text, re.DOTALL)
    
    for match in matches:
        try:
            data = json.loads(match)
            if isinstance(data, dict) and data:
                print(f"✅ JSON extraído via regex: {list(data.keys())}")
                return data
        except json.JSONDecodeError:
            continue
    
    # CASO 4: Tenta parsear a string inteira como JSON
    try:
        data = json.loads(text)
        if isinstance(data, dict) and data:
            print(f"✅ JSON parseado diretamente: {list(data.keys())}")
            return data
    except json.JSONDecodeError:
        pass
    
    # CASO 5: Fallback - se parece ser um objeto JSON mas falhou, tenta corrigir
    if '{' in text and '}' in text:
        # Tenta encontrar o primeiro { e o último }
        start = text.find('{')
        end = text.rfind('}') + 1
        if start < end:
            json_candidate = text[start:end]
            try:
                data = json.loads(json_candidate)
                if isinstance(data, dict) and data:
                    print(f"✅ JSON extraído via fallback: {list(data.keys())}")
                    return data
            except json.JSONDecodeError:
                pass
    
    # CASO 6: Fallback final - cria estrutura básica com o texto completo
    print("⚠️ Nenhum JSON válido encontrado, usando fallback com texto completo")
    return {
        "roteiro": text,  # Usa o texto completo como roteiro
        "titulo_youtube": "Reflexão Filosófica",
        "descricao_curta": "Uma reflexão sobre temas profundos",
        "thumbnail_palavras": ["filosofia", "reflexão", "pensamento"],
        "tags_virais": ["#Filosofia", "#Reflexão", "#Pensamento"]
    }

def save_json(dados: Dict[str, Any], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    _id = (dados.get("id") or "tmp").lstrip("#") or "tmp"
    path = out_dir / f"{_id}.json"
    path.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return path

def criar_pasta_roteiro(pasta_base: Path, id_video: str) -> Path:
    """
    Cria pasta para o roteiro baseado no ID do vídeo
    
    Args:
        pasta_base: Pasta base dos vídeos (ex: E:\Canal Dark\Vídeos Automáticos)
        id_video: ID único do vídeo
    
    Returns:
        Path: Caminho da pasta criada
    """
    pasta_roteiro = pasta_base / id_video
    pasta_roteiro.mkdir(parents=True, exist_ok=True)
    return pasta_roteiro

def save_json(dados: dict, pasta_roteiro: Path):
    """
    Salva arquivos JSON e TXT do roteiro na pasta especificada
    
    Args:
        dados: Dados do roteiro
        pasta_roteiro: Pasta onde salvar os arquivos
    
    Returns:
        tuple: (caminho_json, caminho_txt)
    """
    id_video = dados["id_video"]
    
    # Salva JSON com metadados
    caminho_json = pasta_roteiro / f"{id_video}.json"
    with open(caminho_json, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    
    # Salva texto em arquivo .txt
    caminho_txt = pasta_roteiro / f"{id_video}.txt"
    with open(caminho_txt, 'w', encoding='utf-8') as f:
        f.write(dados.get("texto_pt", ""))
    
    return caminho_json, caminho_txt