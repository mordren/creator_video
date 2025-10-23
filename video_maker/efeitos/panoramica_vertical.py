# efeitos/panoramica_vertical.py
import subprocess

def aplicar(video_input: str, video_output: str) -> bool:
    """Aplica efeito de panorâmica vertical"""
    try:
        filtro = 'crop=ih*9/16:ih,scale=1920:1080'
        
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
            print(f"✅ Efeito panoramica_vertical aplicado com sucesso")
            return True
        else:
            print(f"❌ Erro FFmpeg: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao aplicar panoramica_vertical: {e}")
        return False