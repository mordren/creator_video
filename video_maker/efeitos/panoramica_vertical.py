# efeitos/panoramica_vertical.py
import os, subprocess
from pathlib import Path

def criar_video_panoramica_vertical(img_path, temp=5):
    Path('./renders/temp/').mkdir(parents=True, exist_ok=True)

    nome_base = os.path.splitext(os.path.basename(img_path))[0]
    nome_limpo = nome_base.replace('(', '').replace(')', '').replace(' ', '_')
    saida = os.path.join('./renders/temp/', f'{nome_limpo}_panoramica_vertical.mp4')
    
    filtro = "zoompan=z=1.5:x='iw/2-(iw/zoom/2)':y='if(lte(on,25),0,on)':d=1:s=720x1280:fps=30"
    cmd = [
        "ffmpeg","-nostdin","-y","-hide_banner","-loglevel","error",
        "-loop","1","-i", img_path,
        "-t", str(temp),
        "-vf", filtro,
        "-r","30",
        "-c:v","libx264","-preset","veryfast","-crf","21",
        "-pix_fmt","yuv420p",
        saida
    ]
    subprocess.run(cmd, check=True)
    class Sucesso: filename = saida
    return Sucesso()