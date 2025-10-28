#!/usr/bin/env python3
# short_sequencial.py - Template para vídeos shorts sequenciais de terror
import shutil
import subprocess
from pathlib import Path

from video_maker.video_engine import aplicar_efeito
from video_maker.subtitle_tools import srt_to_ass_karaoke
from video_maker.video_utils import (
    get_media_duration, listar_imagens, 
    criar_frame_estatico, gerar_capa_pillow,
    preparar_diretorios_trabalho, limpar_diretorio_temp, safe_copy
)

def render(audio_path: str, config: dict, roteiro) -> Path:
    """
    Template para vídeos curtos sequenciais de terror VERTICAL (720x1280)
    """
    audio = Path(audio_path)
    
    # CORREÇÃO: Imagens estão na pasta "imagens" no mesmo diretório do áudio
    audio_dir = audio.parent
    images_dir = audio_dir / "imagens"
    
    # Fallback para configuração se a pasta local não existir
    if not images_dir.exists():
        images_dir = Path(config.get('IMAGES_DIR_SHORT', config.get('IMAGES_DIR', './imagens')))
    
    # Configurações básicas
    hook = roteiro.thumb
    num_imagens = 18
    width, height = 720, 1280
    fps = 30
    
    # Preparar diretórios
    output_dir, temp_dir = preparar_diretorios_trabalho(
        config.get('PASTA_VIDEOS', "./renders")
    )
    
    print(f"🎯 Hook: {hook}")
    print(f"📁 Diretório do áudio: {audio_dir}")
    print(f"📁 Procurando imagens em: {images_dir}")

    try:
        # 1. Selecionar imagens
        todas_imagens = listar_imagens(images_dir)
        if not todas_imagens:
            # Listar o conteúdo do diretório para debug
            print(f"📂 Conteúdo do diretório {images_dir}:")
            for item in images_dir.iterdir():
                print(f"   - {item.name} ({'pasta' if item.is_dir() else 'arquivo'})")
            raise ValueError(f"Nenhuma imagem encontrada em: {images_dir}")
        
        print(f"📸 Encontradas {len(todas_imagens)} imagens")
        print(f"📸 Primeiras imagens: {[Path(img).name for img in todas_imagens[:3]]}...")

        # Ciclar pelas imagens para completar 18
        imagens_selecionadas = []
        for i in range(num_imagens):
            img_index = i % len(todas_imagens)
            imagens_selecionadas.append(todas_imagens[img_index])
        
        print(f"🎞️ Usando {len(imagens_selecionadas)} imagens em sequência")

        # 2. Obter duração do áudio
        audio_duration = get_media_duration(audio)
        print(f"⏱️ Áudio: {audio_duration:.2f}s")

        # 3. Processar legenda (se existir)
        srt_path = Path(audio_dir, roteiro.id_video).with_suffix('.srt')
        ass_path = temp_dir / "legenda.ass"
        tem_legenda = False
                
        if srt_path.exists():
            print("📝 Processando legenda...")
            try:
                srt_to_ass_karaoke(str(srt_path), str(ass_path), "vertical")
                tem_legenda = ass_path.exists()
                if tem_legenda:
                    print("✅ Legenda processada e convertida para ASS")
                else:
                    print("❌ Legenda ASS não foi criada após conversão")
            except Exception as e:
                print(f"❌ Erro ao processar legenda: {e}")
                tem_legenda = False
        else:
            print("📝 Nenhuma legenda .srt encontrada")

        # 4. Gerar capa
        capa_path = temp_dir / "capa.png"
        gerar_capa_pillow(imagens_selecionadas[0], hook, capa_path)
        print("🖼️ Capa gerada")

        # 5. Criar clipes
        video_files = []
        
        # Intro com capa (3 segundos)
        try:
            print("🎬 Criando intro com capa...")
            intro = aplicar_efeito('zoom_pulse', str(capa_path), 3.0)
            if intro and hasattr(intro, 'filename'):
                video_files.append(intro.filename)
                print("✅ Intro criada")
        except Exception as e:
            print(f"❌ Erro na intro: {e}")
            criar_frame_estatico(capa_path, 3.0, temp_dir / "intro_fallback.mp4")
            video_files.append(temp_dir / "intro_fallback.mp4")

        # Clipes das imagens restantes
        rest_duration = max(0.0, audio_duration - 3.0)
        remaining_images = imagens_selecionadas[1:]
        
        if remaining_images and rest_duration > 0:
            segment_duration = rest_duration / len(remaining_images)
            efeitos = ['camera_instavel', 'pan', 'zoom_invertido']

            print(f"⏱️ Duração por imagem: {segment_duration:.2f}s")
            
            for i, img in enumerate(remaining_images):
                efeito = efeitos[i % len(efeitos)]
                try:
                    print(f"🎬 [{i+1}/{len(remaining_images)}] {Path(img).name} → {efeito} ({segment_duration:.2f}s)")
                    raw_video = aplicar_efeito(efeito, img, segment_duration)
                    
                    if raw_video and hasattr(raw_video, 'filename'):
                        video_files.append(raw_video.filename)
                        print(f"   ✅ {efeito} aplicado")
                    else:
                        raise Exception("Efeito não retornou arquivo")
                        
                except Exception as e:
                    print(f"❌ Erro em {img}: {e}")
                    # Fallback estático
                    fallback_path = temp_dir / f"fallback_{i:02d}.mp4"
                    criar_frame_estatico(img, segment_duration, fallback_path)
                    video_files.append(fallback_path)
                    print(f"   ✅ Fallback estático criado")

        print(f"📊 Total de clipes gerados: {len(video_files)}")

        # 6. Concatenar vídeos
        print("🔗 Concatenando vídeos...")
        video_id = audio.stem
        saida_conteudo = temp_dir / f"{video_id}_conteudo.mp4"
        
        # Criar lista de vídeos com caminhos absolutos
        lista_videos = temp_dir / "lista_videos.txt"
        with open(lista_videos, "w", encoding="utf-8") as f:
            for video in video_files:
                if video and Path(video).exists():
                    # Usar caminho absoluto para evitar problemas
                    f.write(f"file '{Path(video).resolve()}'\n")
                    print(f"   ✅ Adicionado: {Path(video).name}")
                else:
                    print(f"⚠️  Arquivo de vídeo não encontrado: {video}")

        # Concatenação com re-encode para compatibilidade
        cmd_concat = [
            "ffmpeg", "-y", 
            "-f", "concat", 
            "-safe", "0",
            "-i", str(lista_videos.resolve()),
            "-c:v", "libx264", 
            "-preset", "fast", 
            "-crf", "23",
            "-c:a", "aac", 
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            str(saida_conteudo.resolve())
        ]
        
        print(f"🎥 Executando concatenação...")
        result = subprocess.run(cmd_concat, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Erro na concatenação: {result.stderr}")
            # Tentar método alternativo
            print("🔄 Tentando método alternativo de concatenação...")
            saida_conteudo = _concatenar_metodo_alternativo(video_files, saida_conteudo, fps)
            if not saida_conteudo or not saida_conteudo.exists():
                raise Exception("Todos os métodos de concatenação falharam")
        
        print("✅ Vídeos concatenados")

        # 7. Adicionar áudio e legenda ao vídeo final
        output_path = output_dir / f"{video_id}.mp4"

        # Verificar se a legenda existe e copiar para temp
        legenda_temp = temp_dir / "legenda.ass"
        if tem_legenda and ass_path.exists() and not legenda_temp.exists():
            shutil.copy2(ass_path, legenda_temp)
            print(f"📝 Legenda copiada para: {legenda_temp}")

        audio_temp = temp_dir / audio.name
        safe_copy(audio, audio_temp)

        # Comando final com ou sem legenda
        if tem_legenda and legenda_temp.exists():
            print("🔤 Queimando legenda no vídeo...")
                        
            # caminho absoluto → em formato POSIX
            legenda_path_abs = legenda_temp.resolve().as_posix()                # E:/Canal Terror/Vídeos/temp/legenda.ass
            # escapar o ":" do drive (E:)
            legenda_esc = legenda_path_abs.replace(':', r'\:')                  # E\:/Canal Terror/Vídeos/temp/legenda.ass

            cmd = [
                "ffmpeg", "-y",
                "-i", str(saida_conteudo),
                "-i", str(audio_temp),
                "-vf", f"ass='{legenda_esc}'",  # ↩️ aspas dentro do valor do filtro (por causa do espaço em 'Canal Terror')
                "-c:v", "libx264", "-preset", "fast", "-crf", "21",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(output_path)
            ]
            print("🔧 Comando FFmpeg:", ' '.join(cmd))
            subprocess.run(cmd, check=True, capture_output=True)
        try:
            print("🎬 Renderizando vídeo final...")
            #result = subprocess.run(, capture_output=True, text=True, check=True)
            print("✅ Vídeo final renderizado com sucesso")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao renderizar vídeo final: {e}")
            print(f"📋 Stderr: {e.stderr}")
            
            # Tentar fallback sem legenda se houver erro
            if tem_legenda:
                print("🔄 Tentando fallback sem legenda...")
                cmd_fallback = [
                    "ffmpeg", "-y",
                    "-i", str(saida_conteudo.resolve()),
                    "-i", str(audio.resolve()),
                    "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k",
                    "-shortest",
                    "-movflags", "+faststart",
                    str(output_path.resolve())
                ]
                subprocess.run(cmd_fallback, capture_output=True, check=True)
        
        if output_path.exists():
            duracao_final = get_media_duration(output_path)
            duracao_audio = get_media_duration(audio)
            print(f"✅ Vídeo finalizado: {output_path}")
            print(f"⏱️ Duração vídeo: {duracao_final:.2f}s")
            print(f"⏱️ Duração áudio: {duracao_audio:.2f}s")
            
            if tem_legenda:
                print("🔤 Legenda queimada com sucesso")
            
            # Verificar sincronização
            diferenca = abs(duracao_final - duracao_audio)
            if diferenca > 0.5:
                print(f"⚠️  Atenção: Diferença de {diferenca:.2f}s entre vídeo e áudio")
            
            return output_path
        else:
            raise Exception("Vídeo final não foi criado")
            
    except Exception as e:
        print(f"❌ Erro no template: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        limpar_diretorio_temp(temp_dir)


def _concatenar_metodo_alternativo(video_files, saida_conteudo, fps):
    """Método alternativo para concatenação quando o primeiro falha"""
    try:
        # Criar arquivo de lista temporário
        lista_temp = saida_conteudo.parent / "lista_alternativa.txt"
        with open(lista_temp, "w", encoding="utf-8") as f:
            for video in video_files:
                if Path(video).exists():
                    f.write(f"file '{Path(video).resolve()}'\n")
        
        # Método alternativo com diferentes parâmetros
        cmd_alt = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0", 
            "-i", str(lista_temp.resolve()),
            "-c:v", "libx264",
            "-preset", "superfast",
            "-crf", "25",
            "-r", str(fps),
            "-pix_fmt", "yuv420p",
            "-an",  # Sem áudio por enquanto
            str(saida_conteudo.resolve())
        ]
        
        result = subprocess.run(cmd_alt, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Concatenação alternativa bem-sucedida")
            return saida_conteudo
        else:
            print(f"❌ Método alternativo também falhou: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Erro no método alternativo: {e}")
        return None