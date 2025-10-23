# efeitos/zoom_pulse.py
import subprocess

def aplicar(video_input: str, video_output: str) -> bool:
    """Aplica efeito de zoom pulsante a um vídeo existente"""
    try:
        # Efeito de zoom pulsante suave - CORRIGIDO
        filtro = 'zoompan=z="min(zoom+0.0015,1.5)":d=1:x="iw/2-(iw/zoom/2)":y="ih/2-(ih/zoom/2)"'
        
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
            print(f"✅ Efeito zoom_pulse aplicado com sucesso")
            return True
        else:
            print(f"❌ Erro FFmpeg: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao aplicar zoom pulse: {e}")
        return False