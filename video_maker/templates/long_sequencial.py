import subprocess
import sys
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from roteiro_manager import RoteiroManager
from video_maker.subtitle_tools import srt_to_ass_karaoke
from video_maker.efeitos.depth_3d import criar_video_depth_3d

from video_maker.video_utils import (
    listar_imagens, get_media_duration, preparar_diretorios_trabalho, safe_copy
)

def render(audio_path: str, config: dict, roteiro) -> Path:

    audio = Path(audio_path)
    audio_dir = audio.parent
    images_dir = listar_imagens(audio_dir)

    output_dir, temp_dir = preparar_diretorios_trabalho(
        config.get('PASTA_VIDEOS', "./renders")
    )

    audio_duration = get_media_duration(audio_path)

    dur = audio_duration // len(images_dir)
    print(f"Duração do áudio: {audio_duration}s, Imagens: {len(images_dir)}, Duração por imagem: {dur}s")

    videos_files = []

    for img_path in images_dir:
        video = criar_video_depth_3d(img_path, temp=dur)
        videos_files.append(video.filename)
        print(f"Vídeo criado em: {video.filename}")

     # Criar lista de vídeos com caminhos absolutos
    lista_videos = temp_dir / "lista_videos.txt"
    with open(lista_videos, "w", encoding="utf-8") as f:
        for video in videos_files:
            if video and Path(video).exists():
                # Usar caminho absoluto para evitar problemas
                f.write(f"file '{Path(video).resolve()}'\n")
                print(f"   ✅ Adicionado: {Path(video).name}")
            else:
                print(f"⚠️  Arquivo de vídeo não encontrado: {video}")

    video_id = audio.stem

    saida_conteudo = temp_dir / f"{video_id}_conteudo.mp4"

    cmd_concat = [
            "ffmpeg", "-y", 
            "-f", "concat", 
            "-safe", "0",
            "-i", str(lista_videos.resolve()),
            "-c:v", "libx264", 
            "-preset", "fast", 
            "-crf", "23",
            "-c:a", "aac", 
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            str(saida_conteudo.resolve())
        ]
        
    print(f"🎥 Executando concatenação...")
    result = subprocess.run(cmd_concat, capture_output=True, text=True)

    srt_path = Path(audio).with_suffix('.srt')
    ass_path = temp_dir / "legenda.ass"
    legenda_temp = srt_to_ass_karaoke(str(srt_path), str(ass_path), "horizontal")

    legenda_path_abs = legenda_temp.resolve().as_posix()                # E:/Canal Terror/Vídeos/temp/legenda.ass
    # escapar o ":" do drive (E:)
    legenda_esc = legenda_path_abs.replace(':', r'\:')              
    audio_temp = temp_dir / audio.name
    safe_copy(audio, audio_temp)
    output_path = output_dir / f"{video_id}.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(saida_conteudo),
        "-i", str(audio_temp),
        "-vf", f"ass='{legenda_esc}'",  # ↩️ aspas dentro do valor do filtro (por causa do espaço em 'Canal Terror')
        "-c:v", "libx264", "-preset", "fast", "-crf", "21",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_path)
    ]
    print("🔧 Comando FFmpeg:", ' '.join(cmd))
    subprocess.run(cmd, check=True, capture_output=True)


    #video = criar_video_depth_3d(images_dir[0], temp=40)
    #print(f"Vídeo criado em: {video.filename}")
    
    # Retorna o caminho do vídeo criado
    #return Path(video.filename)

if __name__ == '__main__':
    roteiro_manager = RoteiroManager()
    roteiro = roteiro_manager.buscar_por_id(126)

    result = render(, {}, "teste")
    print(f"Resultado: {result}")