# short_filosofia.py - versão corrigida
import random
import shutil
import subprocess
from pathlib import Path

from video_maker.subtitle_tools import srt_to_ass_karaoke
from video_maker.video_engine import aplicar_efeito
from video_maker.video_utils import gerar_capa, get_media_duration, listar_imagens, quebrar_texto
from PIL import Image, ImageDraw, ImageFont


def criar_frame_estatico(imagem_path: Path, duracao: float, output_path: Path):
    """Cria um vídeo com frame estático a partir de uma imagem"""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(imagem_path),
        "-t", str(duracao),
        "-r", "30",
        "-vf", "scale=720:1280:force_original_aspect_ratio=decrease:flags=lanczos,pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "21",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

def normalizar_duracao(in_path, target_s, fps=60):
    """Normaliza a duração de um vídeo para o tempo exato"""
    in_path = Path(in_path)
    if not in_path.exists():
        return None
    
    out_path = in_path.with_name(in_path.stem + "_norm.mp4")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(in_path),
        "-t", f"{target_s:.3f}",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "21",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        str(out_path)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return str(out_path)
    except subprocess.CalledProcessError:
        return None

def gerar_capa_pillow(imagem_path, texto, output_path, largura=720, altura=1280):
    """Gera capa de forma direta"""
    # Abre e prepara a imagem
    with Image.open(imagem_path) as img:
        img = img.convert('RGB')
        img.thumbnail((largura, altura), Image.Resampling.LANCZOS)
        background = Image.new('RGB', (largura, altura), (0, 0, 0))
        offset = ((largura - img.width) // 2, (altura - img.height) // 2)
        background.paste(img, offset)
        img = background

    draw = ImageDraw.Draw(img)
    
    # Configurações
    tamanho_fonte = 52
    margem = 60
    
    # CORREÇÃO: Caminho relativo para a fonte
    try:
        font = ImageFont.truetype("assets/Montserrat-Black.ttf", tamanho_fonte)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", tamanho_fonte)
        except:
            font = ImageFont.load_default()

    # Quebra texto
    palavras = texto.split()
    linhas = []
    linha_atual = []
    
    for palavra in palavras:
        linha_teste = ' '.join(linha_atual + [palavra])
        bbox = draw.textbbox((0, 0), linha_teste, font=font)
        if (bbox[2] - bbox[0]) <= (largura - margem):
            linha_atual.append(palavra)
        else:
            if linha_atual:
                linhas.append(' '.join(linha_atual))
            linha_atual = [palavra]
    
    if linha_atual:
        linhas.append(' '.join(linha_atual))

    # Desenha
    altura_linha = tamanho_fonte + 15
    y_inicio = (altura // 3) - (len(linhas) * altura_linha // 2)
    
    for i, linha in enumerate(linhas):
        y_pos = y_inicio + (i * altura_linha)
        bbox = draw.textbbox((0, 0), linha, font=font)
        x_pos = (largura - (bbox[2] - bbox[0])) // 2
        
        # Borda branca
        for dx, dy in [(-2,-2), (-2,2), (2,-2), (2,2)]:
            draw.text((x_pos + dx, y_pos + dy), linha, font=font, fill=(255,255,255))
        
        # Texto roxo
        draw.text((x_pos, y_pos), linha, font=font, fill=(106, 16, 211))

    img.save(output_path, "PNG")
    return True

def quebrar_texto_pillow(draw, texto, font, largura_maxima):
    """Quebra texto considerando a largura real na imagem - versão melhorada"""
    palavras = texto.split()
    
    if not palavras:
        return [""]
    
    linhas = []
    linha_atual = []
    
    for palavra in palavras:
        # Testa a linha atual com a nova palavra
        linha_teste = ' '.join(linha_atual + [palavra])
        
        try:
            # Método moderno do Pillow
            bbox = draw.textbbox((0, 0), linha_teste, font=font)
            largura_linha = bbox[2] - bbox[0]
        except:
            # Fallback para cálculo aproximado
            largura_linha = len(linha_teste) * 20  # Aproximação conservadora
        
        if largura_linha <= largura_maxima:
            linha_atual.append(palavra)
        else:
            if linha_atual:
                linhas.append(' '.join(linha_atual))
            linha_atual = [palavra]
    
    if linha_atual:
        linhas.append(' '.join(linha_atual))
    
    # Se ainda tiver linhas muito largas, força a quebra
    linhas_quebradas = []
    for linha in linhas:
        try:
            bbox = draw.textbbox((0, 0), linha, font=font)
            if (bbox[2] - bbox[0]) > largura_maxima:
                # Quebra manual pela metade
                metade = len(linha) // 2
                parte1 = linha[:metade].rsplit(' ', 1)[0]
                parte2 = linha[metade:].strip()
                linhas_quebradas.extend([parte1, parte2])
            else:
                linhas_quebradas.append(linha)
        except:
            linhas_quebradas.append(linha)
    
    return linhas_quebradas

def render(audio_path: str, config: dict) -> Path:
    """
    Template para vídeos curtos de filosofia VERTICAL (720x1280)
    Versão com capa corrigida - texto quebrado e posicionado superiormente
    """
    audio = Path(audio_path)
    
    # Configurações
    images_dir = config.get('IMAGES_DIR_SHORT') or config.get('IMAGE_DIR') or "./imagens"
    images_dir = Path(images_dir)
    
    # CORREÇÃO: Usar hook se disponível, senão usar título
    hook = config.get('hook', config.get('titulo', "REFLEXÕES FILOSÓFICAS"))
    titulo = config.get('titulo', "REFLEXÕES FILOSÓFICAS")
    
    print(f"🎯 Hook para capa: {hook}")
    print(f"📝 Título: {titulo}")
    
    # CORREÇÃO: Quebrar o texto do hook se for muito longo
    hook_quebrado = quebrar_texto(hook, max_caracteres=25)
    print(f"📝 Hook quebrado: {hook_quebrado}")
    
    # Usa PASTA_VIDEOS do config
    pasta_videos = config.get('PASTA_VIDEOS')
    if pasta_videos:
        output_dir = Path(pasta_videos)
        print(f"📁 Salvando vídeo em: {output_dir}")
    else:
        output_dir = Path(config.get('output_dir', "./renders"))
        print(f"⚠️ PASTA_VIDEOS não definida, usando: {output_dir}")
    
    num_imagens = config.get('num_imagens', 18)
    
    # 1. Preparar diretórios
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = output_dir / "temp"
    
    # Limpar diretório temp se existir
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(exist_ok=True)
    
    # 2. Selecionar imagens
    imagens = listar_imagens(images_dir)
    if not imagens:
        raise ValueError(f"Nenhuma imagem encontrada em: {images_dir}")
    
    random.shuffle(imagens)
    num_imagens = min(num_imagens, len(imagens))
    imagens_selecionadas = imagens[:num_imagens]
    
    print(f"🎞️ Usando {len(imagens_selecionadas)} imagens")
    
    # 3. Obter duração do áudio
    audio_duration = get_media_duration(audio)
    print(f"⏱️ Duração do áudio: {audio_duration:.2f}s")
    
    # 4. Gerar capa VERTICAL - CORREÇÃO: texto quebrado e posicionado superiormente
    capa_path = temp_dir / "capa.png"
    if imagens_selecionadas:
        imagem_capa = imagens_selecionadas[0]
        
        print(f"🎯 Hook para capa: {hook}")
        
    
        # Usa Pillow para gerar capa de forma confiável
        sucesso = gerar_capa_pillow(imagem_capa, hook, capa_path)    

    # 5. Processar legendas
    srt_path = audio.with_suffix('.srt')
    ass_path = temp_dir / "legenda.ass"
    tem_legenda = False
    
    if srt_path.exists():
        try:
            print("📝 Convertendo SRT para ASS...")
            srt_to_ass_karaoke(str(srt_path), str(ass_path), "vertical")
            
            if ass_path.exists() and ass_path.stat().st_size > 100:
                tem_legenda = True
                print("✅ Legenda ASS gerada com sucesso")
            else:
                print("⚠️ Arquivo ASS vazio ou inválido")
        except Exception as e:
            print(f"❌ Erro ao gerar legenda ASS: {e}")
    else:
        print("⚠️ Arquivo SRT não encontrado")
    
    # 6. CRIAR FRAME ESTÁTICO DA CAPA
    video_id = audio.stem
    output_path = output_dir / f"{video_id}.mp4"
    frame_capa_path = temp_dir / "000_capa.mp4"
    criar_frame_estatico(capa_path, 3.0, frame_capa_path)
    
    # 7. CONFIGURAR E VERIFICAR EFEITOS
    efeitos_disponiveis = [
        'panoramica_vertical',
        'zoom_invertido',
        'pan',
        'zoom_pulse',
        'camera_instavel',
    ]

    # Verificar quais efeitos estão funcionando
    efeitos_ativos = []
    print("🔍 Verificando efeitos...")
    for efeito in efeitos_disponiveis:
        try:
            teste = aplicar_efeito(efeito, imagens_selecionadas[0], 2.0)  # Teste com 2 segundos
            if teste and hasattr(teste, 'filename') and Path(teste.filename).exists() and Path(teste.filename).stat().st_size > 1024:
                efeitos_ativos.append(efeito)
                print(f"✅ {efeito}")
                # Limpar arquivo de teste
                Path(teste.filename).unlink(missing_ok=True)
            else:
                print(f"❌ {efeito} - Falhou no teste")
        except Exception as e:
            print(f"❌ {efeito} - {str(e)[:100]}")

    if not efeitos_ativos:
        raise Exception("❌ Nenhum efeito funcionando!")
    print(f"🎯 Efeitos ativos: {len(efeitos_ativos)}")

    # 8. PROCESSAR IMAGENS COM EFEITOS - CORREÇÃO CRÍTICA
    rest = max(0.0, float(audio_duration) - 3.0)  # Subtrair duração da capa
    imgs_restantes = imagens_selecionadas[1:]  # Pular a primeira (usada na capa)
    
    n = len(imgs_restantes)
    clips_norm = []
    
    if n > 0 and rest > 0:
        # Calcular durações
        duracao_minima = 2.0  # Aumentei para 2 segundos mínimo
        if rest < n * duracao_minima:
            # Ajustar número de imagens se áudio for muito curto
            n = max(1, int(rest / duracao_minima))
            imgs_restantes = imgs_restantes[:n]
            print(f"🔄 Ajustando para {n} imagens devido ao áudio curto")
            rest = min(rest, n * duracao_minima)
        
        base = rest / n
        durs = [max(duracao_minima, base)] * n
        
        # Ajuste fino para fechar no total exato
        soma = sum(durs)
        if soma != rest:
            durs[-1] += (rest - soma)
        
        print(f"📊 Durações calculadas: {durs}")
        print(f"📊 Total: {sum(durs):.2f}s (deveria ser {rest:.2f}s)")
        
        # Criar lista de concatenação
        lista_clips = temp_dir / "lista_clips.txt"
        
        with open(lista_clips, "w", encoding="utf-8") as f:
            f.write(f"file '{frame_capa_path.name}'\n")  # Capa primeiro
            
            for i, (img, seg) in enumerate(zip(imgs_restantes, durs)):
                nome_efeito = efeitos_ativos[i % len(efeitos_ativos)]
                
                try:
                    print(f"🎬 [{i+1}/{n}] {nome_efeito} ({seg:.1f}s)...")
                    
                    raw = aplicar_efeito(nome_efeito, img, seg)
                    
                    if raw and hasattr(raw, 'filename') and Path(raw.filename).exists() and Path(raw.filename).stat().st_size > 1024:
                        norm = normalizar_duracao(raw.filename, seg, fps=30)
                        if norm and Path(norm).exists():
                            # Copiar o arquivo normalizado para o temp_dir
                            nome_arquivo = f"clip_{i:03d}.mp4"
                            destino = temp_dir / nome_arquivo
                            shutil.copy2(norm, destino)
                            
                            f.write(f"file '{nome_arquivo}'\n")
                            clips_norm.append(norm)
                            print(f"   ✅ {nome_arquivo}")
                            
                            # Limpar arquivo temporário
                            Path(norm).unlink(missing_ok=True)
                            Path(raw.filename).unlink(missing_ok=True)
                        else:
                            print(f"   ⚠️ Falha na normalização")
                    else:
                        print(f"   ⚠️ Efeito falhou - arquivo não gerado")
                        
                except Exception as e:
                    print(f"   ❌ Erro: {e}")
    
    # Verificar se temos clipes suficientes
    if not clips_norm:
        print("⚠️ Nenhum clipe foi gerado, usando apenas a capa")
    
    # 9. RENDER FINAL
    print("🎥 Renderizando vídeo final...")
    
    # Preparar arquivos necessários no temp_dir
    audio_temp = temp_dir / audio.name
    if not audio_temp.exists():
        shutil.copy2(audio, audio_temp)
    
    # Configurar filtro de vídeo
    vf_filter = "ass=legenda.ass" if tem_legenda else "scale=720:1280:flags=lanczos"
    
    # Comando final - CORREÇÃO: garantir que use o áudio correto
    cmd_final = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", "lista_clips.txt",
        "-i", str(audio_temp),
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",  # Termina quando o áudio ou vídeo acabar
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]

    try:
        # Executar no temp_dir
        print("🚀 Executando render final...")
        result = subprocess.run(cmd_final, check=True, cwd=temp_dir, capture_output=True, text=True)
        
        # Verificar se o vídeo foi criado
        if output_path.exists():
            duracao_final = get_media_duration(output_path)
            print(f"✅ Vídeo final salvo em: {output_path}")
            print(f"⏱️ Duração do vídeo: {duracao_final:.2f}s")
            
            # Verificar se a duração está próxima do esperado
            if abs(duracao_final - audio_duration) > 2.0:
                print(f"⚠️ Atenção: duração do vídeo ({duracao_final:.2f}s) difere significativamente do áudio ({audio_duration:.2f}s)")
        else:
            raise Exception("Vídeo final não foi criado")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro no render: {e}")
        print(f"Stderr: {e.stderr}")
        
        # Fallback: tentar sem legenda
        if tem_legenda:
            print("🔄 Tentando sem legenda...")
            cmd_final[cmd_final.index("-vf") + 1] = "scale=720:1280:flags=lanczos"
            try:
                subprocess.run(cmd_final, check=True, cwd=temp_dir, capture_output=True)
                
                if output_path.exists():
                    duracao_final = get_media_duration(output_path)
                    print(f"✅ Vídeo final salvo (sem legenda): {output_path}")
                    print(f"⏱️ Duração do vídeo: {duracao_final:.2f}s")
            except subprocess.CalledProcessError as e2:
                print(f"❌ Erro mesmo sem legenda: {e2}")
    
    # Limpeza
    try:
        # Remove diretório temp
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"⚠️ Erro na limpeza: {e}")
    
    return output_path