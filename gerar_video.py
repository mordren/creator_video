# test_template.py
from video_maker.templates.short_filosofia import render

# Teste básico
config = {
    'images_dir': r'C:\Users\mordren\Documents\Foocus\imagens geradas\out_short_segundos',
    'titulo': 'Filosofia Teste',
    'num_imagens': 8
}

resultado = render('./21.mp3', config)
print(f"Vídeo gerado: {resultado}")