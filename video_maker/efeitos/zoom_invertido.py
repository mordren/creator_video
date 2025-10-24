import os, subprocess
from pathlib import Path

def criar_video_zoom_invertido(img_path, temp=5):
    Path('./renders/temp/').mkdir(parents=True, exist_ok=True)
    nome_base = os.path.splitext(os.path.basename(img_path))[0]
    saida = os.path.join('./renders/temp/', f"{nome_base}_zoom.mp4")

    # Zoom invertido (afasta aos poucos)
    filtro = (
        "scale=iw*2.4:ih*2.4,"
        "zoompan=z='2.4-0.008*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        "d=1:s=720x1280:fps=60,format=yuv420p"
    )

    comando = [
        "ffmpeg","-y",
        "-loop","1",
        "-i", str(img_path),
        "-filter_complex", filtro,
        "-t", str(temp),
        "-r","60",
        "-c:v","libx264",
        "-preset","veryfast",
        "-crf","21",
        "-pix_fmt","yuv420p",
        str(saida)
    ]
    result = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        class Sucesso:
            filename = saida
        return Sucesso()
    else:
        print(f"❌ Erro ao processar {img_path}:\n{result.stderr.decode()}")
        return None
