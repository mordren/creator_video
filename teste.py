import os
from pathlib import Path

# --- Configurações ---
OUTPUT_DIR = Path("./renders_test/efeitos_ass")
ASS_FILENAME = "legendas_teste.ass"
OUTPUT_FILE = OUTPUT_DIR / ASS_FILENAME
PASTA_IMAGENS_TEMPLATE = Path(__file__).parent / "assets" / "imagens_template"

def format_time_ass(ms: int) -> str:
    """Converte milissegundos para o formato H:MM:SS.CC do ASS (H:MM:SS.cs)."""
    total_seconds = ms / 1000
    h = int(total_seconds // 3600)
    m = int((total_seconds % 3600) // 60)
    s = int(total_seconds % 60)
    cs = int((total_seconds * 100) % 100)
    # Formato ASS é H:MM:SS.cc (centissegundos)
    return f"{h:01}:{m:02}:{s:02}.{cs:02}"

# Define o cabeçalho e os estilos (V4+ Styles) do arquivo ASS
ASS_HEADER_AND_STYLES = f"""[Script Info]
Title: Teste de Efeitos ASS
ScriptType: v4.00+
Collisions: Normal
PlayResX: 720
PlayResY: 1280
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,60,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,2,2,30,30,40,1
Style: Digitacao,Arial,72,&H00E6FF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,4,3,2,50,50,80,1
Style: Transformacao,Arial,80,&H0000FFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,5,4,2,30,30,40,1
"""
# Cores: &H00BBGGRR (PrimaryColour é a cor da letra. SecondaryColour é a cor do efeito \k)

def gerar_ass_efeitos():
    """Gera o arquivo ASS com os três exemplos de efeitos."""
    
    lines_ass = []
    
    # 1. Efeito Padrão (Sem tags de transformação)
    start_ms = 500
    end_ms = 2000
    lines_ass.append(
        f"Dialogue: 0,{format_time_ass(start_ms)},{format_time_ass(end_ms)},Default,,0,0,0,,Esta é a primeira linha de teste.\n"
    )

    # 2. Efeito de Digitação (Karaoke/Highlight)
    # Usa a tag {\kN}, onde N é a duração em centissegundos (1/100s)
    start_ms = 2500
    end_ms = 4500
    texto_base = "O efeito de digitação é aplicado aqui!"
    palavras = texto_base.split(' ')
    duracao_total = end_ms - start_ms # 2000ms
    
    # Distribui a duração uniformemente por palavra
    duracao_por_palavra_cs = int((duracao_total / len(palavras)) / 10) 
    
    texto_karaoke = []
    for palavra in palavras:
        # A tag {\k...} fará a cor mudar da PrimaryColour para a SecondaryColour
        # palavra por palavra.
        texto_karaoke.append(f"{{\\k{duracao_por_palavra_cs}}}{palavra}")

    lines_ass.append(
        f"Dialogue: 0,{format_time_ass(start_ms)},{format_time_ass(end_ms)},Digitacao,,0,0,0,,{' '.join(texto_karaoke)}\n"
    )
    
    # 3. Efeito de Transformação (Zoom Pulsante + Cor)
    # Usa a tag \t(\tag), que anima uma propriedade durante o tempo da legenda.
    start_ms = 5000
    end_ms = 6500
    # Tags:
    # \fscx/y: Altera a escala da fonte (horizontal/vertical)
    # \t(t1,t2,\tag): Transforma a tag entre t1 e t2 (em ms)
    # \bordN: Altera a espessura da borda
    
    # Exemplo de Transformação: Aumenta a escala e volta (efeito de "pulse")
    texto_transformado = (
        r"{\t(0, 750, \fscx115\fscy115)\t(750, 1500, \fscx100\fscy100)\bord5}AQUI TEM OUTRO ESTILO."
    )

    lines_ass.append(
        f"Dialogue: 0,{format_time_ass(start_ms)},{format_time_ass(end_ms)},Transformacao,,0,0,0,,{texto_transformado}\n"
    )
    
    # --- Salvar o Arquivo ---
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(ASS_HEADER_AND_STYLES + "\n")
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            f.writelines(lines_ass)
        print(f"✅ Arquivo ASS de teste gerado com sucesso em: {OUTPUT_FILE.resolve()}")
        print("\nPara visualizar o efeito, você pode usar um comando FFmpeg:")
        print("  (Aviso: Você precisará de um arquivo de vídeo/imagem de fundo)")
        print(f'  ffmpeg -i fundo.jpg -vf "ass={ASS_FILENAME}" -t 6.5 -y video_com_efeito.mp4')
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo ASS: {e}")
        return False

if __name__ == "__main__":
    gerar_ass_efeitos()