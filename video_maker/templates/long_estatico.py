# long_estatico.py - template para vídeos longos 16:9 com imagem estática
import re
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from video_maker.subtitle_tools import srt_to_ass_karaoke
from video_maker.video_utils import (
    criar_frame_estatico_long, get_media_duration, criar_frame_estatico,
    preparar_diretorios_trabalho, limpar_diretorio_temp
)

def adicionar_marca_dagua(imagem_path: Path, texto: str, output_path: Path):
    """Adiciona marca d'água com o @ do canal na imagem"""
    with Image.open(imagem_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("assets/Montserrat-Black.ttf", 30)
        
        bbox = draw.textbbox((0, 0), texto, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        margin = 20
        x = img.width - text_width - margin
        y = img.height - text_height - margin
        
        padding = 5
        draw.rectangle(
            [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
            fill=(0, 0, 0, 128)
        )
        
        draw.text((x, y), texto, font=font, fill=(255, 255, 255))
        img.save(output_path)

def encontrar_imagem_na_pasta_audio(audio_path: Path) -> Path:
    pasta_audio = audio_path.parent
    
    # 1. Busca imagem com mesmo nome do áudio
    nome_base = audio_path.stem
    extensoes_imagem = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
    
    for ext in extensoes_imagem:
        caminho_imagem = pasta_audio / f"{nome_base}{ext}"
        if caminho_imagem.exists():
            return caminho_imagem
    
    # 2. Busca qualquer imagem na pasta
    for ext in extensoes_imagem:
        imagens = list(pasta_audio.glob(f"*{ext}"))
        if imagens:
            return imagens[0]
    
    return None

def render(audio_path: str, config: dict, roteiro) -> Path:
    """
    Template para vídeos LONGOS (16:9) com imagem estática
    - SEM FALLBACKS - Falha imediatamente se faltar qualquer recurso
    """
    audio = Path(audio_path)

    # Verificações obrigatórias
    if not audio.exists():
        raise FileNotFoundError(f"Áudio não encontrado: {audio_path}")
    
    link_canal = config.get('LINK')
    if not link_canal:
        raise ValueError("Configuração 'link' não encontrada - @ do canal é obrigatório")

    # Configurações
    width = 1280
    height = 720
    fps = int(config.get('fps_long', 30))

    # Configurar diretórios
    output_dir, temp_dir = preparar_diretorios_trabalho(
        config.get('PASTA_VIDEOS') or "./renders_long"
    )

    print(f"📺 Canal: {link_canal}")
    print(f"📁 Áudio: {audio}")
    print(f"📁 Saída: {output_dir}")
    print(f"📐 Tamanho: {width}x{height} @ {fps}fps")

    # 1. Encontrar imagem na pasta do áudio
    imagem_path = encontrar_imagem_na_pasta_audio(audio)
    print(f"🖼️ Imagem: {imagem_path}")

    # 2. Obter duração do áudio
    audio_duration = get_media_duration(audio)
    print(f"⏱️ Duração do áudio: {audio_duration:.2f}s")

    # 3. Processar legendas - OBRIGATÓRIO
    srt_name = re.sub(r'^(.*?)(?:_com_musica)?\.[^.]+$', r'\1.srt', audio.name, flags=re.IGNORECASE)
    srt_path = audio.with_name(srt_name)
    
    if not srt_path.exists():
        raise FileNotFoundError(f"Legenda SRT não encontrada: {srt_path}")
    
    ass_path = temp_dir / "legenda.ass"
    srt_to_ass_karaoke(str(srt_path), str(ass_path), "horizontal")
    
    if not ass_path.exists() or ass_path.stat().st_size <= 100:
        raise ValueError("Legenda ASS não foi gerada corretamente")
    
    print("✅ Legenda processada")

    # 4. Preparar imagem final com marca d'água
    imagem_final_path = temp_dir / "imagem_final.jpg"
    
    with Image.open(imagem_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensionar para 16:9 exato
        img_ratio = img.width / img.height
        target_ratio = width / height
        
        if img_ratio > target_ratio:
            new_height = height
            new_width = int(height * img_ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            left = (new_width - width) // 2
            img = img.crop((left, 0, left + width, height))
        else:
            new_width = width
            new_height = int(width / img_ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            top = (new_height - height) // 2
            img = img.crop((0, top, width, top + height))
        
        # Adicionar marca d'água
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("assets/Montserrat-Black.ttf", 30)
        
        bbox = draw.textbbox((0, 0), link_canal, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        margin = 20
        x = img.width - text_width - margin
        y = img.height - text_height - margin
        
        padding = 5
        draw.rectangle(
            [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
            fill=(0, 0, 0, 128)
        )
        
        draw.text((x, y), link_canal, font=font, fill=(255, 255, 255))
        img.save(imagem_final_path)

    print(f"🖼️ Imagem com marca d'água preparada")

    # 5. Criar vídeo estático
    video_id = audio.stem
    output_path = output_dir / f"{video_id}.mp4"
    video_estatico_path = temp_dir / "video_estatico.mp4"
    
    criar_frame_estatico_long(imagem_final_path, audio_duration, video_estatico_path)
    print(f"🎬 Vídeo estático criado")

    # 6. Render final COM LEGENDA
    print("🎥 Montando vídeo final...")

    audio_temp = temp_dir / audio.name
    shutil.copy2(audio, audio_temp)

    cmd_final = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
        "-i", str(video_estatico_path.name),
        "-i", str(audio_temp.name),
        "-vf", f"ass={ass_path.name}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        "-r", str(fps),
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]

    # Executar render - SEM FALLBACK
    print("🔧 Executando FFmpeg...")
    result = subprocess.run(
        cmd_final, 
        check=True, 
        cwd=temp_dir, 
        capture_output=True, 
        text=True, 
        timeout=300
    )

    # Verificar se o vídeo foi criado
    if not output_path.exists():
        raise Exception("Vídeo final não foi criado")

    duracao_final = get_media_duration(output_path)
    tamanho_mb = output_path.stat().st_size / (1024 * 1024)
    
    print(f"✅ VÍDEO ESTÁTICO gerado: {output_path}")
    print(f"⏱️  Duração: {duracao_final:.2f}s")
    print(f"💾 Tamanho: {tamanho_mb:.1f} MB")
    print(f"📺 Marca d'água: {link_canal}")
    
    return output_path

# Para uso como template independente
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        config = {
            'PASTA_VIDEOS': './renders_long',
            'fps_long': 30,
            'link': '@meucanal'
        }
        
        class RoteiroMock:
            def __init__(self):
                self.thumb = "Título do Vídeo"
        
        roteiro = RoteiroMock()
        
        resultado = render(audio_path, config, roteiro)
        print(f"🎉 Vídeo criado com sucesso: {resultado}")
    else:
        print("Uso: python long_estatico.py <caminho_do_audio>")