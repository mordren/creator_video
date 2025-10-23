# efeitos/efeito_vertigo.py
import subprocess

def aplicar(video_input: str, video_output: str) -> bool:
    """Aplica efeito vertigo (zoom com desfoque)"""
    try:
        filtro = 'zoompan=z="min(zoom+0.0015,1.5)":d=1:x="iw/2-(iw/zoom/2)":y="ih/2-(ih/zoom/2)",boxblur=2'
        
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
            print(f"✅ Efeito efeito_vertigo aplicado com sucesso")
            return True
        else:
            print(f"❌ Erro FFmpeg: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao aplicar efeito_vertigo: {e}")
        return False