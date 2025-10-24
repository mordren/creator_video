# efeitos/efeito_hook_visual.py
import os, subprocess
from pathlib import Path
from efeitos.zoom_pulse import criar_video_pulse
from efeitos.camera_instavel import criar_video_camera_instavel

def criar_video_hook_visual(img1, img2, temp_total=3.0):
    Path("./outs").mkdir(parents=True, exist_ok=True)
    seg = 0.75  # 0,75s por efeito

    c1 = criar_video_pulse(img1, seg).filename
    c2 = criar_video_camera_instavel(img1, seg).filename
    c3 = criar_video_pulse(img2, seg).filename
    c4 = criar_video_camera_instavel(img2, seg).filename

    # normaliza FPS/parametros pra concat (60 fps, yuv420p, libx264)
    norm = []
    for idx, clip in enumerate([c1, c2, c3, c4], 1):
        outn = os.path.splitext(clip)[0] + f"_norm.mp4"
        subprocess.run([
            "ffmpeg","-nostdin","-y","-hide_banner","-loglevel","error",
            "-i", clip, "-r","60", "-vf","format=yuv420p",
            "-c:v","libx264","-preset","veryfast","-crf","21",
            "-pix_fmt","yuv420p", outn
        ], check=True)
        norm.append(outn)

    # concatena os 4 segmentos
    lista = os.path.join("outs", "hook_concat.txt")
    with open(lista, "w", encoding="utf-8") as f:
        for n in norm:
            f.write(f"file '{os.path.abspath(n)}'\n")

    base = f"hook_{Path(img1).stem}_{Path(img2).stem}.mp4"
    saida = os.path.join("outs", base)

    subprocess.run([
        "ffmpeg","-nostdin","-y","-hide_banner","-loglevel","error",
        "-f","concat","-safe","0","-i", lista,
        "-c","copy", saida
    ], check=True)

    class Sucesso: filename = saida
    return Sucesso()
