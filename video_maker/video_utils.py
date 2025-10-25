"""
UTILITÁRIOS DE VÍDEO - COMPARTILHÁVEIS ENTRE TODOS OS CANAIS
"""
import subprocess
import shutil
from pathlib import Path

# Funções que ambos os sistemas usam
def get_media_duration(path):
    """Obtém a duração de um arquivo de mídia de forma robusta"""
    try:
        path = Path(path)
        if not path.exists():
            return 0.0
            
        # Primeiro verifica se é um arquivo de áudio válido
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
        if not duration:
            return 0.0
            
        return float(duration)
    except Exception as e:
        print(f"Erro ao obter duração de {path}: {e}")
        return 0.0

def safe_copy(src, dst):
    src = Path(src).resolve()
    dst = Path(dst).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Arquivo não existe: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))

def safe_move(src, dst):
    src = Path(src).resolve()
    dst = Path(dst).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Arquivo não existe: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    shutil.move(str(src), str(dst))


def listar_imagens(diretorio):
    exts = ('.jpg', '.jpeg', '.png', '.bmp')
    path = Path(diretorio)
    if not path.exists():
        return []
    return sorted([str(f) for f in path.iterdir() if f.suffix.lower() in exts])


def gerar_capa(imagem, titulo, output_path=None, largura=720, altura=1280, cor_texto="#6B10D3", cor_borda="#FFFFFF"):
    """Gera capa com fonte específica"""
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

def quebrar_texto(texto, max_caracteres=18):
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
    
    linhas = [linha.strip() for linha in linhas if linha.strip()]
    return '\n'.join(linhas)