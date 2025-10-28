# efeitos/pan.py
import os, subprocess
from pathlib import Path

def criar_video_pan(img_path: str, temp: float):
    Path('./renders/temp/').mkdir(parents=True, exist_ok=True)
    nome_base = os.path.splitext(os.path.basename(img_path))[0]
    saida = os.path.join('./renders/temp/', f"{nome_base}_camera_pan.mp4")

    filtro = (
        "[0:v]"
        "scale=720:-1:force_original_aspect_ratio=decrease,"
        "pad=720:1280:(720-iw)/2:(1280-ih)/2,"
        "split=2[bg][src];"
        "[bg]gblur=sigma=32[blur];"
        "[src]"
        "zoompan=z='pow(1.015, on)':"
        "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        "d=1:s=720x1280:fps=60[sharp];"
        "[blur][sharp]overlay=(W-w)/2:(H-h)/2,"
        "vignette=PI/3:eval=frame"
    )

    cmd = [
        "ffmpeg","-nostdin","-y","-hide_banner","-loglevel","error",
        "-loop","1","-i", img_path,
        "-t", str(temp),
        "-filter_complex", filtro,
        "-r","60",
        "-c:v","libx264","-preset","veryfast","-crf","21",
        "-pix_fmt","yuv420p",
        saida
    ]
    subprocess.run(cmd, check=True)
    class Sucesso: filename = saida
    return Sucesso()

def criar_video_pan_horizontal(img_path: str, temp: float):
    """Versão horizontal 16:9 para vídeos longos"""
    Path('./renders/temp/').mkdir(parents=True, exist_ok=True)
    nome_base = os.path.splitext(os.path.basename(img_path))[0]
    saida = os.path.join('./renders/temp/', f"{nome_base}_camera_pan_horizontal.mp4")

    filtro = (
        "[0:v]"
        "scale=1280:-1:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(1280-iw)/2:(720-ih)/2,"
        "split=2[bg][src];"
        "[bg]gblur=sigma=32[blur];"
        "[src]"
        "zoompan=z='pow(1.015, on)':"
        "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        "d=1:s=1280x720:fps=60[sharp];"
        "[blur][sharp]overlay=(W-w)/2:(H-h)/2,"
        "vignette=PI/3:eval=frame"
    )

    cmd = [
        "ffmpeg","-nostdin","-y","-hide_banner","-loglevel","error",
        "-loop","1","-i", img_path,
        "-t", str(temp),
        "-filter_complex", filtro,
        "-r","60",
        "-c:v","libx264","-preset","veryfast","-crf","21",
        "-pix_fmt","yuv420p",
        saida
    ]
    subprocess.run(cmd, check=True)
    class Sucesso: filename = saida
    return Sucesso()