# utils.py
from pathlib import Path
import json, re
from typing import Any, Dict

# tokenização de "palavra" robusta (acentos + hífen/contração)
_WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+(?:[-''][A-Za-zÀ-ÖØ-öø-ÿ0-9]+)?", re.UNICODE)

def count_words(s: str) -> int:
    """Conta palavras de forma robusta, incluindo acentos e hífens"""
    return len(_WORD.findall(re.sub(r"\s+", " ", s.strip())))

def truncate_words(s: str, n: int) -> str:
    """Trunca texto por número de palavras"""
    out, seen = [], 0
    for chunk in re.split(r"(\W+)", s):
        if _WORD.fullmatch(chunk):
            if seen >= n: 
                break
            seen += 1
        out.append(chunk)
    return "".join(out).strip()

def extract_json_maybe(text: str) -> dict:
    """
    Função simplificada apenas para compatibilidade
    O processamento principal agora está no gemini_text.py
    """
    if isinstance(text, dict):
        return text
    
    # Se for string, tenta fazer parse direto (para outros providers)
    try:
        return json.loads(text)
    except:
        # Fallback básico
        return {
            "texto": str(text)[:1000],
            "titulo": "Generated Content",
            "descricao": "Automatically generated content",
            "hook": "Default hook",
            "hook_pt": "Hook padrão", 
            "thumb": "default",
            "tags": ["#default"]
        }

def save_json(dados: Dict[str, Any], out_dir: Path) -> Path:
    """Salva dados em arquivo JSON"""
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

def save_json_completo(dados: dict, pasta_roteiro: Path):
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
    texto_pt = dados.get("texto_pt", dados.get("texto", ""))
    with open(caminho_txt, 'w', encoding='utf-8') as f:
        f.write(texto_pt)
    
    return caminho_json, caminho_txt

def obter_proximo_id(pasta_base: Path) -> str:
    """Obtém o próximo ID sequencial baseado nas pastas existentes"""
    if not pasta_base.exists():
        return "1"
    
    ids_existentes = []
    for item in pasta_base.iterdir():
        if item.is_dir() and item.name.isdigit():
            try:
                ids_existentes.append(int(item.name))
            except ValueError:
                continue
    
    proximo_id = max(ids_existentes) + 1 if ids_existentes else 1
    return str(proximo_id)

def vertical_horizontal(resolucao: str) -> str:
    """Determina se a resolução é vertical ou horizontal"""
    return "vertical" if resolucao == "720x1280" else "horizontal"

def clean_json_response(text: str) -> Dict[str, Any]:
    """
    Limpa e extrai JSON da resposta do modelo (robusto para Gemini, Grok, etc.)
    Versão standalone da função que estava no gemini_text.py
    """
    import ast
    
    # Remove blocos ```json e ``` simples
    text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"```$", "", text)
    text = re.sub(r"[\x00-\x1f\x7f]", "", text)  # remove caracteres de controle
    text = text.strip()

    # PRÉ-PROCESSAMENTO: Corrige escapes problemáticos
    text = re.sub(r"(?<!\\)\\'", "'", text)
    text = re.sub(r'(?<![\\"])"(?![\\"])', '"', text)
    text = text.replace('\\\\', '\\')

    # Caso 1: JSON puro
    try:
        return json.loads(text)
    except Exception:
        pass

    # Caso 2: JSON dentro de aspas
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        unquoted_text = text[1:-1]
        unquoted_text = unquoted_text.replace('\\"', '"').replace("\\'", "'").replace("\\n", "\n")
        try:
            return json.loads(unquoted_text)
        except Exception:
            try:
                return json.loads(unquoted_text)
            except Exception:
                pass

    # Caso 3: JSON dentro de string Python
    try:
        maybe = ast.literal_eval(text)
        if isinstance(maybe, str):
            cleaned_str = re.sub(r"(?<!\\)\\'", "'", maybe)
            try:
                return json.loads(cleaned_str)
            except Exception:
                match = re.search(r'\{[\s\S]*\}', cleaned_str)
                if match:
                    return json.loads(match.group(0))
        elif isinstance(maybe, dict):
            return maybe
    except Exception:
        pass

    # Caso 4: Reparação avançada
    try:
        repaired = re.sub(r"'([^']*)'", r'"\1"', text)
        repaired = re.sub(r"\[\s*'([^']*)'\s*\]", r'["\1"]', repaired)
        repaired = re.sub(r"\[\s*'([^']*)',\s*'([^']*)'\s*\]", r'["\1", "\2"]', repaired)
        return json.loads(repaired)
    except Exception:
        pass

    # Caso 5: Extração por regex
    try:
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                cleaned_match = re.sub(r"(?<!\\)\\'", "'", match)
                cleaned_match = re.sub(r'\s+', ' ', cleaned_match)
                return json.loads(cleaned_match)
            except Exception:
                continue
    except Exception:
        pass

    # Caso 6: Extração por linhas
    try:
        lines = text.split('\n')
        json_lines = []
        in_json = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('{') or in_json:
                json_lines.append(line)
                in_json = True
            if line.endswith('}'):
                break
        
        if json_lines:
            json_text = ' '.join(json_lines)
            json_text = re.sub(r"(?<!\\)\\'", "'", json_text)
            return json.loads(json_text)
    except Exception:
        pass

    raise ValueError(f"Não foi possível extrair JSON válido da resposta: {text[:200]}...")
    
def ajustar_timestamps_srt(arquivo_entrada: str, arquivo_saida: str = None) -> str:
    """
    Ajusta os timestamps de um arquivo SRT removendo gaps entre legendas
    
    Args:
        arquivo_entrada: Caminho para o arquivo SRT original
        arquivo_saida: Caminho para o arquivo SRT ajustado (opcional)
    
    Returns:
        str: Caminho do arquivo ajustado
    """
    def time_to_ms(time_str):
        hours, minutes, seconds = time_str.split(':')
        seconds, ms = seconds.split(',')
        return (int(hours) * 3600 + int(minutes) * 60 + int(seconds)) * 1000 + int(ms)

    def ms_to_time(ms):
        hours = ms // 3600000
        ms %= 3600000
        minutes = ms // 60000
        ms %= 60000
        seconds = ms // 1000
        ms %= 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"

    def parse_srt(content):
        blocks = content.strip().split('\n\n')
        subtitles = []
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                try:
                    index = int(lines[0])
                    time_match = re.match(r'(\d+:\d+:\d+,\d+) --> (\d+:\d+:\d+,\d+)', lines[1])
                    if time_match:
                        start = time_match.group(1)
                        end = time_match.group(2)
                        text = '\n'.join(lines[2:])
                        subtitles.append({
                            'index': index,
                            'start': start,
                            'end': end,
                            'text': text
                        })
                except ValueError:
                    continue
        return subtitles

    def save_srt(subtitles, output_path):
        with open(output_path, 'w', encoding='utf-8') as file:
            for sub in subtitles:
                file.write(f"{sub['index']}\n")
                file.write(f"{sub['start']} --> {sub['end']}\n")
                file.write(f"{sub['text']}\n\n")

    # Processamento principal
    if arquivo_saida is None:
        arquivo_saida = arquivo_entrada.replace('.srt', '_ajustado.srt')
    
    # Ler arquivo original
    with open(arquivo_entrada, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    subtitles = parse_srt(conteudo)
    
    if not subtitles:
        raise ValueError("Nenhuma legenda válida encontrada no arquivo")
    
    # Ajustar timestamps
    total_correction = 0
    previous_end = None
    
    for i, subtitle in enumerate(subtitles):
        start_ms = time_to_ms(subtitle['start'])
        end_ms = time_to_ms(subtitle['end'])
        
        if previous_end is not None:
            gap = start_ms - previous_end
            if gap > 0:
                total_correction += gap
                print(f"Ajustando gap de {gap}ms entre as legendas {i} e {i+1}")
        
        start_ms -= total_correction
        end_ms -= total_correction
        
        subtitle['start'] = ms_to_time(start_ms)
        subtitle['end'] = ms_to_time(end_ms)
        previous_end = end_ms + total_correction  # Usar o valor original para cálculo do próximo gap
    
    # Salvar arquivo ajustado
    save_srt(subtitles, arquivo_saida)
    
    tempo_total_original = time_to_ms(subtitles[-1]['end']) + total_correction
    tempo_total_ajustado = time_to_ms(subtitles[-1]['end'])
    
    print(f"\nArquivo ajustado salvo como: {arquivo_saida}")
    print(f"Tempo total corrigido: {total_correction/1000:.2f} segundos")
    print(f"Tempo original: {tempo_total_original/1000:.2f}s → Tempo ajustado: {tempo_total_ajustado/1000:.2f}s")
    
    return arquivo_saida

def analisar_gaps_srt(arquivo_srt: str) -> Dict[str, Any]:
    """
    Analisa os gaps entre legendas SRT sem modificar o arquivo
    
    Args:
        arquivo_srt: Caminho para o arquivo SRT
    
    Returns:
        Dict com informações sobre os gaps
    """
    def time_to_ms(time_str):
        hours, minutes, seconds = time_str.split(':')
        seconds, ms = seconds.split(',')
        return (int(hours) * 3600 + int(minutes) * 60 + int(seconds)) * 1000 + int(ms)

    def parse_srt(content):
        blocks = content.strip().split('\n\n')
        subtitles = []
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                try:
                    index = int(lines[0])
                    time_match = re.match(r'(\d+:\d+:\d+,\d+) --> (\d+:\d+:\d+,\d+)', lines[1])
                    if time_match:
                        start = time_match.group(1)
                        end = time_match.group(2)
                        text = '\n'.join(lines[2:])
                        subtitles.append({
                            'index': index,
                            'start': start,
                            'end': end,
                            'text': text,
                            'start_ms': time_to_ms(start),
                            'end_ms': time_to_ms(end)
                        })
                except ValueError:
                    continue
        return subtitles

    # Ler e analisar arquivo
    with open(arquivo_srt, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    subtitles = parse_srt(conteudo)
    gaps = []
    total_gap = 0
    
    for i in range(len(subtitles) - 1):
        current_end = subtitles[i]['end_ms']
        next_start = subtitles[i + 1]['start_ms']
        gap = next_start - current_end
        
        if gap > 0:
            gaps.append({
                'entre_legendas': f"{i+1} → {i+2}",
                'gap_ms': gap,
                'gap_segundos': gap / 1000,
                'legenda_anterior': subtitles[i]['text'][:50] + "...",
                'proxima_legenda': subtitles[i + 1]['text'][:50] + "..."
            })
            total_gap += gap
    
    return {
        'total_legendas': len(subtitles),
        'total_gaps': len(gaps),
        'tempo_total_gaps_ms': total_gap,
        'tempo_total_gaps_segundos': total_gap / 1000,
        'gaps_detectados': gaps,
        'duracao_total_original_ms': subtitles[-1]['end_ms'] if subtitles else 0,
        'duracao_total_ajustada_ms': (subtitles[-1]['end_ms'] - total_gap) if subtitles else 0
    }