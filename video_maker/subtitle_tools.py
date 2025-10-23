# subtitle_tools.py
import re
import unicodedata
import pysrt

def format_time_ass(time_obj):
    """Formata tempo para formato ASS (Advanced SubStation Alpha)"""
    total_seconds = (
        time_obj.hours * 3600 + time_obj.minutes * 60 +
        time_obj.seconds + time_obj.milliseconds / 1000
    )
    h = int(total_seconds // 3600)
    m = int((total_seconds % 3600) // 60)
    s = int(total_seconds % 60)
    cs = int((total_seconds * 100) % 100)
    return f"{h:01}:{m:02}:{s:02}.{cs:02}"

def to_plain_upper(token: str) -> str:
    """Normaliza texto: remove acentos, mantém apenas letras/números, converte para maiúsculo"""
    # Remove acentos
    t = unicodedata.normalize("NFD", token)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    # Remove tudo que não for letra ou número
    t = re.sub(r"[^0-9A-Za-z]+", "", t)
    # Converte para MAIÚSCULAS
    return t.upper()

def clean_text(text):
    """Remove tags HTML/XML do texto"""
    return re.sub(r'<[^>]+>', '', text).strip()

def srt_to_ass_karaoke(srt_file, ass_file, orientacao="vertical", font_name="Arial"):
    """
    Converte SRT em ASS karaokê com opções de orientação
    
    Args:
        srt_file: Arquivo SRT de entrada
        ass_file: Arquivo ASS de saída  
        orientacao: "vertical" (1 palavra/linha) ou "horizontal" (10 palavras/linha)
        font_name: Nome da fonte a ser usada (padrão: Arial)
    """
    
    try:
        subs = pysrt.open(srt_file, encoding="utf-8")
    except Exception as e:
        print(f"❌ Erro ao abrir arquivo SRT: {e}")
        return False

    # Header do arquivo ASS com fonte configurável
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Normal,{font_name},90,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,1,0,5,10,10,120,1
Style: Highlight,{font_name},99,&H00FFFFFF,&H000000FF,&H00E31378,&H00E31378,-1,0,0,0,100,100,0,0.2,3,4,0,5,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]

    # Configura palavras por bloco baseado na orientação
    palavras_por_bloco = 1 if orientacao == "vertical" else 10

    for sub in subs:
        duracao_total_ms = sub.end.ordinal - sub.start.ordinal
        texto_limpo = clean_text(sub.text)
        todas_palavras = texto_limpo.split()
        
        if not todas_palavras:
            continue

        # Divide em blocos de palavras
        blocos = [
            todas_palavras[i:i + palavras_por_bloco] 
            for i in range(0, len(todas_palavras), palavras_por_bloco)
        ]
        
        if not blocos:
            continue
            
        duracao_por_bloco = duracao_total_ms // len(blocos)

        for bloco_idx, bloco in enumerate(blocos):
            inicio_bloco = sub.start.ordinal + (bloco_idx * duracao_por_bloco)
            duracao_por_palavra = duracao_por_bloco // len(bloco)

            for palavra_idx, palavra in enumerate(bloco):
                inicio_palavra = inicio_bloco + (palavra_idx * duracao_por_palavra)
                fim_palavra = inicio_palavra + duracao_por_palavra

                start_ass = format_time_ass(pysrt.SubRipTime(milliseconds=int(inicio_palavra)))
                end_ass = format_time_ass(pysrt.SubRipTime(milliseconds=int(fim_palavra)))

                # Constrói o texto com highlight para a palavra atual
                texto = []
                for j, w in enumerate(bloco):
                    texto.append(f"{{\\rHighlight}}{to_plain_upper(w)}{{\\r}}")

                linha = f"Dialogue: 0,{start_ass},{end_ass},Normal,,0,0,0,,{' '.join(texto)}\n"
                lines.append(linha)

    try:
        with open(ass_file, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"✅ Arquivo ASS gerado com sucesso: {ass_file}")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo ASS: {e}")
        return False

# Função de teste
def testar_conversao():
    """Testa a conversão SRT para ASS"""
    try:
        # Exemplo de uso
        resultado = srt_to_ass_karaoke(
            srt_file="legenda.srt", 
            ass_file="legenda.ass",
            orientacao="vertical",
            font_name="Arial"
        )
        return resultado
    except Exception as e:
        print(f"Erro no teste: {e}")
        return False

if __name__ == "__main__":
    print("=== Teste Subtitle Tools ===")
    testar_conversao()