"""
UTILITÁRIOS DE VÍDEO - COMPARTILHÁVEIS ENTRE TODOS OS CANAIS
"""
import subprocess
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Funções básicas de mídia
def get_media_duration(path):
    """Obtém a duração de um arquivo de mídia de forma robusta"""
    try:
        path = Path(path)
        if not path.exists():
            return 0.0
            
        if path.suffix.lower() not in ['.mp3', '.wav', '.m4a', '.aac', '.flac']:
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

# Funções de processamento de vídeo
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

# Funções de imagem com Pillow
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