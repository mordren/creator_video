# efeitos/efeito_pulse.py
import os, subprocess
from pathlib import Path

def criar_video_pulse(img_path, temp=3, fps=30):
    Path('./renders/temp/').mkdir(parents=True, exist_ok=True)
    nome_base = os.path.splitext(os.path.basename(img_path))[0]
    saida = os.path.join('./renders/temp/', f"{nome_base}_camera_pulse.mp4")

    # Filtro corrigido - usando 'on' corretamente
    filtro = (
        "scale=720:1280:force_original_aspect_ratio=increase,"
        "crop=720:1280,"
        "zoompan="
            "z='1.05+0.08*sin(0.5*on)':"
            "d=1:"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            "s=720x1280"
    )

    cmd = [
        "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-i", img_path,
        "-t", str(temp),
        "-vf", filtro,
        "-r", str(fps),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
        "-pix_fmt", "yuv420p",
        saida
    ]
    
    try:
        subprocess.run(cmd, check=True)
        class Sucesso: filename = saida
        return Sucesso()
    except subprocess.CalledProcessError as e:
        print(f"Erro ao criar vídeo pulse: {e}")
        return None

def criar_video_pulse_horizontal(img_path, temp=3, fps=30):
    """Versão horizontal 16:9 para vídeos longos"""
    Path('./renders/temp/').mkdir(parents=True, exist_ok=True)
    nome_base = os.path.splitext(os.path.basename(img_path))[0]
    saida = os.path.join('./renders/temp/', f"{nome_base}_camera_pulse_horizontal.mp4")

    # Filtro para formato 16:9
    filtro = (
        "scale=1280:720:force_original_aspect_ratio=increase,"
        "crop=1280:720,"
        "zoompan="
            "z='1.05+0.08*sin(0.5*on)':"
            "d=1:"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            "s=1280x720"
    )

    cmd = [
        "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-i", img_path,
        "-t", str(temp),
        "-vf", filtro,
        "-r", str(fps),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
        "-pix_fmt", "yuv420p",
        saida
    ]
    
    try:
        subprocess.run(cmd, check=True)
        class Sucesso: filename = saida
        return Sucesso()
    except subprocess.CalledProcessError as e:
        print(f"Erro ao criar vídeo pulse horizontal: {e}")
        return None