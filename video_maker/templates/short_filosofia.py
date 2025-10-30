# short_filosofia.py - template com transições (xfade) entre clipes
import json
import random
import re
import shutil
import subprocess
from pathlib import Path

from video_maker.subtitle_tools import srt_to_ass_karaoke
from video_maker.video_engine import aplicar_efeito
from video_maker.video_utils import (
    get_media_duration, listar_imagens, quebrar_texto,
    criar_frame_estatico, normalizar_duracao, gerar_capa_pillow,
    preparar_diretorios_trabalho, limpar_diretorio_temp
)

def render(audio_path: str, config: dict, roteiro) -> Path:

    audio = Path(audio_path)

    # Configurações básicas
    images_dir = Path(config.get('IMAGES_DIR_SHORT') or config.get('IMAGE_DIR') or "./imagens")
    hook = roteiro.thumb
    num_imagens = config.get('num_imagens', 12)
    dur_fade = float(config.get('duracao_transicao', 0.8))  # duração da transição (s)
    width = int(config.get('largura', 720))
    height = int(config.get('altura', 1280))
    fps = int(config.get('fps', 30))

    output_dir, temp_dir = preparar_diretorios_trabalho(
        config.get('PASTA_VIDEOS') or config.get('output_dir', "./renders")
    )

    print(f"🎯 Hook: {hook}")
    print(f"📁 Imagens: {images_dir}")
    print(f"📁 Saída: {output_dir}")
    print(f"✨ Transição: xfade 'fade' ({dur_fade:.2f}s)")
    print(f"📐 Tamanho: {width}x{height} @ {fps}fps")

    try:
        imagens = listar_imagens(images_dir)
        if not imagens:
            raise ValueError(f"Nenhuma imagem encontrada em: {images_dir}")
        
        audio_duration = get_media_duration(audio)
        print(f"⏱️ Duração do áudio: {audio_duration:.2f}s")

        ass_path = temp_dir / "legenda.ass"
        tem_legenda = False

        srt_name = re.sub(r'^(.*?)(?:_com_musica)?\.[^.]+$', r'\1.srt', audio.name, flags=re.IGNORECASE)
        srt_path = audio.with_name(srt_name)
        
        if srt_path.exists():
            try:
                srt_to_ass_karaoke(str(srt_path), str(ass_path), "vertical")
                tem_legenda = ass_path.exists() and ass_path.stat().st_size > 100
                print("✅ Legenda processada" if tem_legenda else "⚠️ Legenda vazia")
            except Exception as e:
                print(f"❌ Erro na legenda: {e}")
        
        imagens = listar_imagens(images_dir)
        random.shuffle(imagens)
        imagens_selecionadas = imagens[:min(num_imagens, len(imagens))]    
        
        capa_path = temp_dir / "capa_com_hook.png"
        if imagens_selecionadas:
            primeira_imagem = imagens_selecionadas[0]
            gerar_capa_pillow(primeira_imagem, hook, capa_path)
            print(f"📝 Capa com hook gerada a partir de: {Path(primeira_imagem).name}")

        # 5. CRIAR CLIPES (CAPA + OUTRAS IMAGENS) COM DURAÇÕES CONTROLADAS
        video_id = audio.stem
        output_path = output_dir / f"{video_id}.mp4"

        # Guardaremos os clipes finais (no temp_dir) e suas durações
        clip_files = []
        clip_durations = []

        # Apenas para debug opcional
        lista_clips = temp_dir / "lista_clips.txt"
        open(lista_clips, "w", encoding="utf-8").close()

        # CAPA com efeito especial (3-4s ou 10% do áudio)
        duracao_capa = min(4.0, max(2.0, audio_duration * 0.10))

        try:            
            capa_com_efeito = aplicar_efeito('camera_instavel', str(capa_path), duracao_capa)

            if capa_com_efeito and hasattr(capa_com_efeito, 'filename') and Path(capa_com_efeito.filename).exists():
                norm_capa = normalizar_duracao(capa_com_efeito.filename, duracao_capa, fps=fps)
                if norm_capa and Path(norm_capa).exists():
                    nome_capa = "capa_com_efeito.mp4"
                    destino_capa = temp_dir / nome_capa
                    shutil.copy2(norm_capa, destino_capa)
                    clip_files.append(destino_capa)
                    clip_durations.append(duracao_capa)
                    with open(lista_clips, "a", encoding="utf-8") as f:
                        f.write(f"file '{nome_capa}'\n")
                    # Limpar temporários
                    Path(norm_capa).unlink(missing_ok=True)
                    Path(capa_com_efeito.filename).unlink(missing_ok=True)
                    print("✅ Capa com hook e efeito criada")
        except Exception as e:
            print(f"❌ Erro na capa com hook: {e}")
            # Fallback: capa estática
            try:
                fallback_capa = temp_dir / "capa_estatica.mp4"
                criar_frame_estatico(capa_path, duracao_capa, fallback_capa)
                clip_files.append(fallback_capa)
                clip_durations.append(duracao_capa)
                with open(lista_clips, "a", encoding="utf-8") as f:
                    f.write(f"file 'capa_estatica.mp4'\n")
                print("✅ Fallback: capa estática criada")
            except Exception as e2:
                print(f"❌ Fallback da capa também falhou: {e2}")

        # Demais imagens (excluindo a primeira já usada na capa)
        rest = audio_duration - (clip_durations[0] if clip_durations else 0.0)
        imgs_restantes = imagens_selecionadas[1:] if len(imagens_selecionadas) > 1 else []

        if imgs_restantes and rest > 0:
            n_total = len(imgs_restantes)
            duracao_minima = 2.0

            # Ajustar número de imagens conforme duração restante
            if rest < n_total * duracao_minima:
                n_total = max(1, int(rest / duracao_minima))
                imgs_restantes = imgs_restantes[:n_total]
                rest = min(rest, n_total * duracao_minima)

            # Calcular durações
            base = rest / n_total if n_total > 0 else rest
            durs = [max(duracao_minima, base) for _ in range(n_total)]
            if n_total > 0:
                durs[-1] += (rest - sum(durs))

            # Sistema de efeitos (rotação para variar)
            efeitos = ['camera_instavel', 'pan', 'zoom_invertido', 'panoramica_vertical', 'zoom_pulse']

            for i, (img, seg) in enumerate(zip(imgs_restantes, durs)):
                efeito = efeitos[i % len(efeitos)]
                try:
                    print(f"🎬 [{i+1}/{n_total}] {Path(img).name} → {efeito} ({seg:.1f}s)...")
                    raw = aplicar_efeito(efeito, img, seg)

                    if raw and hasattr(raw, 'filename') and Path(raw.filename).exists():
                        norm = normalizar_duracao(raw.filename, seg, fps=fps)
                        if norm and Path(norm).exists():
                            nome_arquivo = f"clip_{i:03d}.mp4"
                            destino = temp_dir / nome_arquivo
                            shutil.copy2(norm, destino)
                            clip_files.append(destino)
                            clip_durations.append(float(seg))
                            with open(lista_clips, "a", encoding="utf-8") as f:
                                f.write(f"file '{nome_arquivo}'\n")
                            # Limpar temporários
                            Path(norm).unlink(missing_ok=True)
                            Path(raw.filename).unlink(missing_ok=True)
                except Exception as e:
                    print(f"   ❌ Erro no efeito {efeito}: {e}")
                    # Fallback: criar clipe estático
                    try:
                        nome_arquivo = f"fallback_{i:03d}.mp4"
                        fallback_path = temp_dir / nome_arquivo
                        criar_frame_estatico(img, seg, fallback_path)
                        clip_files.append(fallback_path)
                        clip_durations.append(float(seg))
                        with open(lista_clips, "a", encoding="utf-8") as f:
                            f.write(f"file '{nome_arquivo}'\n")
                        print(f"   ✅ Fallback estático criado")
                    except Exception as fallback_error:
                        print(f"   ❌ Fallback também falhou: {fallback_error}")
        else:
            print("⚠️  Não há imagens suficientes para continuar após a capa")

        if not clip_files:
            raise RuntimeError("Nenhum clipe foi gerado para montar o vídeo final.")

        # 6. RENDER FINAL COM XFADE (vídeo) + ÁUDIO principal separado
        print("🎥 Montando com transições (xfade)...")

        # Copiar áudio para temp_dir
        audio_temp = temp_dir / audio.name
        if not audio_temp.exists():
            shutil.copy2(audio, audio_temp)

        # Construir comando FFmpeg
        cmd_final = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning"]

        # Adicionar cada clipe como input
        for cf in clip_files:
            cmd_final += ["-i", cf.name]  # como estamos usando cwd=temp_dir, podemos passar apenas o nome

        # Adicionar o áudio como último input
        cmd_final += ["-i", audio_temp.name]

        # Construir filter_complex
        # Pré-processamento de cada vídeo: scale -> fps -> format -> setpts
        fc_parts = []
        for idx in range(len(clip_files)):
            fc_parts.append(f"[{idx}:v]scale={width}:{height}:flags=lanczos,fps={fps},format=yuv420p,setpts=PTS-STARTPTS[v{idx}]")

        # Encadear as transições xfade
        # Fórmula do offset para a transição i (combinando o resultado acumulado com o clipe i):
        # offset_i = sum(durs[0..i-1]) - i * dur_fade
        if len(clip_files) == 1:
            current = "v0"
        else:
            current = "v0"
            soma_prev = 0.0
            for i in range(1, len(clip_files)):
                soma_prev += float(clip_durations[i-1])
                offset = max(0.0, soma_prev - i * dur_fade)
                out_lbl = f"x{i}"
                fc_parts.append(f"[{current}][v{i}]xfade=transition=fade:duration={dur_fade:.3f}:offset={offset:.3f}[{out_lbl}]")
                current = out_lbl

        # Aplicar legenda no final, se existir
        video_out = current
        if tem_legenda:
            fc_parts.append(f"[{video_out}]ass=legenda.ass[vout]")
            video_out = "vout"

        filter_complex = "; ".join(fc_parts)

        # Mapear saídas
        # - Vídeo: label do último estágio do filter_complex
        # - Áudio: do último input (o arquivo de áudio original)
        cmd_final += [
            "-filter_complex", filter_complex,
            "-map", f"[{video_out}]",
            "-map", f"{len(clip_files)}:a?",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path)
        ]

        # Executar render
        try:            
            result = subprocess.run(cmd_final, check=True, cwd=temp_dir, capture_output=True, text=True, timeout=600)
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro no FFmpeg (xfade): {e}")
            if e.stderr:
                print(f"🔍 Detalhes do erro: {e.stderr[:800]}...")
            # Fallback: tentar sem legenda se existia
            if tem_legenda:
                print("🔄 Tentando novamente sem legenda...")
                # Recriar filter_complex sem 'ass'
                fc_no_sub = "; ".join([p for p in fc_parts if "ass=legenda.ass" not in p])
                cmd_sem_legenda = cmd_final[:]  # copia
                # Encontrar o índice de "-filter_complex" para substituir o grafo
                try:
                    fc_idx = cmd_sem_legenda.index("-filter_complex")
                    cmd_sem_legenda[fc_idx + 1] = fc_no_sub
                    # Ajustar mapeamento de vídeo (label pode mudar)
                    # Se removemos a legenda, o vídeo_out volta a ser 'current'
                    map_idx = cmd_sem_legenda.index("-map")
                    # O primeiro -map é o de vídeo
                    cmd_sem_legenda[map_idx + 1] = f"[{current}]"
                except ValueError:
                    pass
                try:
                    subprocess.run(cmd_sem_legenda, check=True, cwd=temp_dir, capture_output=True, text=True, timeout=600)
                except subprocess.CalledProcessError as e2:
                    print(f"❌ Também falhou sem legenda: {e2}")
                    if e2.stderr:
                        print(f"🔍 Detalhes do erro: {e2.stderr[:800]}...")
                    return None

        if output_path.exists():
            duracao_final = get_media_duration(output_path)
            print(f"✅ Vídeo final gerado: {output_path}")
            print(f"⏱️ Duração (vídeo): {duracao_final:.2f}s")
            print(f"🔗 Clipes: {len(clip_files)}")
            print(f"✨ Transições aplicadas: {max(0, len(clip_files)-1)} xfade(s) de {dur_fade:.2f}s")
            return output_path
        else:
            raise Exception("Vídeo final não foi criado")

    except Exception as e:
        print(f"❌ Erro crítico no template: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        try:
            limpar_diretorio_temp(temp_dir)
        except Exception:
            pass
