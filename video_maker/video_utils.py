"""
UTILITÁRIOS DE VÍDEO - COMPARTILHÁVEIS ENTRE TODOS OS CANAIS
"""
import subprocess
import shutil
import json, re
from pathlib import Path
from typing import Any, Dict
from PIL import Image, ImageDraw, ImageFont

# =============================================================================
# FUNÇÕES DE ARQUIVO E SISTEMA
# =============================================================================

def safe_copy(src, dst):
    """Copia arquivo com verificação de segurança"""
    src = Path(src).resolve()
    dst = Path(dst).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Arquivo não existe: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))

def safe_move(src, dst):
    """Move arquivo com verificação de segurança"""
    src = Path(src).resolve()
    dst = Path(dst).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Arquivo não existe: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    shutil.move(str(src), str(dst))

def preparar_diretorios_trabalho(output_dir):
    """Prepara diretórios de trabalho e retorna paths"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    temp_dir = output_dir / "temp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(exist_ok=True)
    
    return output_dir, temp_dir

def limpar_diretorio_temp(temp_dir):
    """Limpa diretório temporário"""
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"⚠️ Erro na limpeza: {e}")

# =============================================================================
# FUNÇÕES DE MÍDIA E DURAÇÃO
# =============================================================================

def get_media_duration(path):
    """Obtém a duração de um arquivo de mídia de forma robusta"""
    try:
        path = Path(path)
        if not path.exists():
            return 0.0
            
        resultado = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if resultado.returncode != 0:
            return 0.0
            
        duration = resultado.stdout.strip()
        return float(duration) if duration else 0.0
            
    except Exception as e:
        print(f"Erro ao obter duração de {path}: {e}")
        return 0.0

def listar_imagens(diretorio):
    """Lista imagens de um diretório"""
    exts = ('.jpg', '.jpeg', '.png', '.bmp')
    path = Path(diretorio)
    return sorted([str(f) for f in path.iterdir() if f.suffix.lower() in exts]) if path.exists() else []

def listar_videos(diretorio):
    """Lista vídeos de um diretório"""
    exts = ('.mp4', '.mov', '.mkv', '.m4v', '.webm', '.avi')
    path = diretorio
    return sorted([str(f) for f in path.iterdir() if f.suffix.lower() in exts]) if path.exists() else []

# =============================================================================
# FUNÇÕES DE TEXTO
# =============================================================================

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

def quebrar_texto(texto, max_caracteres=25):
    """Quebra o texto em múltiplas linhas de forma inteligente"""
    palavras = texto.split()
    if not palavras:
        return texto
    
    linhas = []
    linha_atual = []
    
    for palavra in palavras:
        linha_teste = ' '.join(linha_atual + [palavra])
        
        if len(linha_teste) <= max_caracteres:
            linha_atual.append(palavra)
        else:
            if linha_atual:
                linhas.append(' '.join(linha_atual))
            
            if len(palavra) > max_caracteres:
                partes = [palavra[i:i+max_caracteres-3] + "..." for i in range(0, len(palavra), max_caracteres-3)]
                linha_atual = [partes[0]]
                linhas.extend(partes[1:])
            else:
                linha_atual = [palavra]
    
    if linha_atual:
        linhas.append(' '.join(linha_atual))
    
    return '\n'.join([linha.strip() for linha in linhas if linha.strip()])

# =============================================================================
# FUNÇÕES DE PROCESSAMENTO DE VÍDEO
# =============================================================================

def criar_frame_estatico(imagem_path: Path, duracao: float, output_path: Path):
    """Cria um vídeo com frame estático a partir de uma imagem"""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(imagem_path),
        "-t", str(duracao),
        "-r", "30",
        "-vf", "scale=720:1280:force_original_aspect_ratio=decrease:flags=lanczos,pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "21",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

def criar_frame_estatico_long(imagem_path: Path, duracao: float, output_path: Path):
    """Cria um vídeo com frame estático a partir de uma imagem"""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(imagem_path),
        "-t", str(duracao),
        "-r", "30",
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease:flags=lanczos,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "21",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def normalizar_duracao(in_path, target_s, fps=30):
    """Normaliza a duração de um vídeo para o tempo exato"""
    in_path = Path(in_path)
    if not in_path.exists():
        return None
    
    out_path = in_path.with_name(in_path.stem + "_norm.mp4")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(in_path),
        "-t", f"{target_s:.3f}",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "21",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        str(out_path)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return str(out_path)
    except subprocess.CalledProcessError:
        return None

# =============================================================================
# FUNÇÕES DE CAPA/IMAGEM
# =============================================================================

def gerar_capa_pillow(imagem_path, texto, output_path, largura=720, altura=1280):
    """Gera capa usando Pillow - função compartilhável entre templates"""
    with Image.open(imagem_path) as img:
        img = img.convert('RGB')
        img.thumbnail((largura, altura), Image.Resampling.LANCZOS)
        background = Image.new('RGB', (largura, altura), (0, 0, 0))
        offset = ((largura - img.width) // 2, (altura - img.height) // 2)
        background.paste(img, offset)
        img = background

    draw = ImageDraw.Draw(img)
    
    # Configurações
    tamanho_fonte = 52
    margem = 60
    
    # Carregar fonte
    try:
        font = ImageFont.truetype("assets/Montserrat-Black.ttf", tamanho_fonte)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", tamanho_fonte)
        except:
            font = ImageFont.load_default()

    # Quebrar texto
    palavras = texto.split()
    linhas = []
    linha_atual = []
    
    for palavra in palavras:
        linha_teste = ' '.join(linha_atual + [palavra])
        bbox = draw.textbbox((0, 0), linha_teste, font=font)
        if (bbox[2] - bbox[0]) <= (largura - margem):
            linha_atual.append(palavra)
        else:
            if linha_atual:
                linhas.append(' '.join(linha_atual))
            linha_atual = [palavra]
    
    if linha_atual:
        linhas.append(' '.join(linha_atual))

    # Desenhar texto
    altura_linha = tamanho_fonte + 15
    y_inicio = (altura // 3) - (len(linhas) * altura_linha // 2)
    
    for i, linha in enumerate(linhas):
        y_pos = y_inicio + (i * altura_linha)
        bbox = draw.textbbox((0, 0), linha, font=font)
        x_pos = (largura - (bbox[2] - bbox[0])) // 2
        
        # Borda branca
        for dx, dy in [(-2,-2), (-2,2), (2,-2), (2,2)]:
            draw.text((x_pos + dx, y_pos + dy), linha, font=font, fill=(255,255,255))
        
        # Texto roxo
        draw.text((x_pos, y_pos), linha, font=font, fill=(106, 16, 211))

    img.save(output_path, "PNG")
    return True

def gerar_capa(imagem, titulo, output_path=None, largura=720, altura=1280, cor_texto="#6B10D3", cor_borda="#FFFFFF"):
    """Gera capa com fonte específica usando FFmpeg"""
    if output_path is None:
        saida = Path("capa.png")
    else:
        saida = Path(output_path)
    
    # Escapar caracteres especiais no texto
    txt = str(titulo).replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'")
    
    # Especificar fonte de forma robusta
    vf = (
        f"scale={largura}:{altura}:force_original_aspect_ratio=decrease,"
        f"pad={largura}:{altura}:(ow-iw)/2:(oh-ih)/2,"
        f"drawtext=text='{txt}':font='Montserrat Black':fontsize=40:"
        f"fontcolor={cor_texto}:borderw=3:bordercolor={cor_borda}:"
        f"x=(w-text_w)/2:y=(h-text_h)/2-50"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(imagem),
        "-vf", vf,
        "-frames:v", "1",
        "-update", "1",
        str(saida)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return saida

def gerarCapaPNG(imagem, titulo, w=720, h=1280, usar_fontfile=False, fontfile_path=r"C:\Windows\Fonts\Montserrat-Black.ttf"):
    """Gera capa PNG com opções de fonte"""
    saida = Path("capa.png")
    cor_titulo = "#6B10D3"
    cor_borda = "#FFFFFF"
    txt = str(titulo).replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'")
    font_opt = f"fontfile='{fontfile_path}'" if usar_fontfile else "font='Montserrat Black'"

    vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,"
        f"drawtext=text='{txt}':{font_opt}:fontsize=34:"
        f"fontcolor={cor_titulo}:borderw=3:bordercolor={cor_borda}:"
        f"x=(w-text_w)/2:y=(h-text_h)/2-50"
    )
    comando = ["ffmpeg", "-y", "-i", str(imagem), "-vf", vf, "-frames:v", "1", "-update", "1", str(saida)]
    subprocess.run(comando, check=True)
    return saida

# =============================================================================
# FUNÇÕES DE ÁUDIO
# =============================================================================

def mixar_audio_com_musica(audio_voz, musica_path, ganho_musica=-19):
    """Mixa áudio de voz com música de fundo"""
    audio_path = Path(audio_voz)
    musica = Path(musica_path)
    
    if not audio_path.exists():
        raise FileNotFoundError(f"Áudio não encontrado: {audio_path}")
    if not musica.exists():
        raise FileNotFoundError(f"Música não encontrada: {musica}")

    saida = audio_path.with_name(f"{audio_path.stem}_com_musica.mp3")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(audio_path),
        "-i", str(musica),
        "-filter_complex",
        f"[0:a]volume=0dB[a0];"
        f"[1:a]volume={ganho_musica}dB,aloop=loop=-1:size=2e+09[a1];"
        f"[a0][a1]amix=inputs=2:duration=first:dropout_transition=2,"
        f"dynaudnorm=f=250:g=3[a]",
        "-map", "[a]",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        "-ar", "48000",
        str(saida)
    ]

    subprocess.run(cmd, check=True, capture_output=True)
    return saida

def mixar_audio_voz_trilha(audio_voz, trilha_path, ganho_voz=0, ganho_musica=-15):
    """
    Mixa a narração (voz) com a trilha musical, normalizando o volume final.
    Salva o arquivo mixado no mesmo diretório do áudio original.
    """
    audio_path = Path(audio_voz)
    trilha = Path(trilha_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Arquivo de voz não encontrado: {audio_path}")
    if not trilha.exists():
        raise FileNotFoundError(f"Trilha musical não encontrada: {trilha}")

    # define saída
    saida = audio_path.with_name(f"{audio_path.stem}_mixado.mp3")

    # comando ffmpeg
    cmd = [
        "ffmpeg", "-y",
        "-i", str(audio_path),
        "-i", str(trilha),
        "-filter_complex",
        (
            f"[0:a]volume={ganho_voz}dB[a0];"
            f"[1:a]volume={ganho_musica}dB[a1];"
            f"[a0][a1]amix=inputs=2:duration=first:dropout_transition=2,"
            f"dynaudnorm=f=250:g=3[a]"
        ),
        "-map", "[a]",
        "-c:a", "libmp3lame",   # codec seguro para MP3
        "-b:a", "192k",
        "-ar", "48000",
        str(saida)
    ]

    print(f"🎧 Mixando: {audio_path.name} + {trilha.name}")
    subprocess.run(cmd, check=True)
    print(f"✅ Áudio mixado salvo em: {saida}")
    return saida

# =============================================================================
# FUNÇÕES DE JSON E PROCESSAMENTO DE TEXTO
# =============================================================================

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

# =============================================================================
# FUNÇÕES DE AJUSTE DE TIMESTAMPS (NOVAS)
# =============================================================================

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