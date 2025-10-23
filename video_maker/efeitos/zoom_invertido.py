# efeitos/zoom_invertido.py
import subprocess

def aplicar(video_input: str, video_output: str) -> bool:
    """Aplica efeito de zoom invertido (zoom out)"""
    try:
        filtro = 'zoompan=z="if(lte(zoom,1.0),1.5,max(1.001,zoom-0.0015))":d=1:x="iw/2-(iw/zoom/2)":y="ih/2-(ih/zoom/2)"'
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video_input,
            '-vf', filtro,
            '-c:a', 'copy',
            '-preset', 'medium',
            video_output
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Efeito zoom_invertido aplicado com sucesso")
            return True
        else:
            print(f"❌ Erro FFmpeg: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao aplicar zoom_invertido: {e}")
        return False