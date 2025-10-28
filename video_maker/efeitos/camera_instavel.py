# efeitos/efeito_camera_instavel.py
import os, subprocess
from pathlib import Path

def criar_video_camera_instavel(img_path, temp=5):
    Path('./renders/temp/').mkdir(parents=True, exist_ok=True)
    nome_base = os.path.splitext(os.path.basename(img_path))[0]
    saida = os.path.join('./renders/temp/', f"{nome_base}_camera_instavel.mp4")

    # Pipeline:
    # 1) Trabalha em canvas maior (900x1600) para margem de movimento
    # 2) CROP animado (shake) -> 720x1280
    # 3) Fundo borrado + vinheta arredondada
    filtro = (
        "[0:v]"
        "scale=900:-1:force_original_aspect_ratio=decrease,"
        "pad=900:1600:(900-iw)/2:(1600-ih)/2,split=2[big][big2];"
        "[big]"
        "crop=720:1280:"
        "x='(in_w-720)/2 + 60*sin(t*2)':"
        "y='(in_h-1280)/2 + 40*cos(t*1.6)',"
        "scale=720:1280[sharp];"
        "[big2]scale=720:1280,gblur=sigma=32[blur];"
        "[blur][sharp]overlay=(W-w)/2:(H-h)/2,vignette=PI/3:eval=frame"
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

def criar_video_camera_instavel_horizontal(img_path, temp=5):
    """Versão horizontal 16:9 para vídeos longos"""
    Path('./renders/temp/').mkdir(parents=True, exist_ok=True)
    nome_base = os.path.splitext(os.path.basename(img_path))[0]
    saida = os.path.join('./renders/temp/', f"{nome_base}_camera_instavel_horizontal.mp4")

    # Pipeline para formato 16:9 (1280x720)
    filtro = (
        "[0:v]"
        "scale=1400:-1:force_original_aspect_ratio=decrease,"
        "pad=1400:800:(1400-iw)/2:(800-ih)/2,split=2[big][big2];"
        "[big]"
        "crop=1280:720:"
        "x='(in_w-1280)/2 + 80*sin(t*2)':"
        "y='(in_h-720)/2 + 30*cos(t*1.6)',"
        "scale=1280:720[sharp];"
        "[big2]scale=1280:720,gblur=sigma=32[blur];"
        "[blur][sharp]overlay=(W-w)/2:(H-h)/2,vignette=PI/3:eval=frame"
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