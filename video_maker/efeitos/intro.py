# efeitos/intro.py
import subprocess

def aplicar(video_input: str, video_output: str) -> bool:
    """Aplica efeito de introdução/abertura"""
    try:
        # Efeito de fade in e zoom suave
        filtro = 'fade=in:0:30,zoompan=z="zoom+0.002":d=1:x="iw/2-(iw/zoom/2)":y="ih/2-(ih/zoom/2)"'
        
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
            print(f"✅ Efeito intro aplicado com sucesso")
            return True
        else:
            print(f"❌ Erro FFmpeg: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao aplicar intro: {e}")
        return False