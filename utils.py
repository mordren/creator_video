from pathlib import Path
import json, re
from typing import Any, Dict
import subprocess
import tempfile  # ✅ ADICIONAR ESTA LINHA
import os

import pysrt

# tokenização de "palavra" robusta (acentos + hífen/contração)
_WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+(?:[-''][A-Za-zÀ-ÖØ-öø-ÿ0-9]+)?", re.UNICODE)

def count_words(s: str) -> int:
    """Conta palavras de forma robusta, incluindo acentos e hífens"""
    return len(_WORD.findall(re.sub(r"\s+", " ", s.strip())))

def truncate_words(s: str, n: int) -> str:
    """Trunca texto por número de palavras"""
    out, seen = [], 0
    for chunk in re.split(r"(\W+)", s):
        if _WORD.fullmatch(chunk):
            if seen >= n: 
                break
            seen += 1
        out.append(chunk)
    return "".join(out).strip()

def extract_json_maybe(text: str) -> dict:
    """
    Função simplificada apenas para compatibilidade
    O processamento principal agora está no gemini_text.py
    """
    if isinstance(text, dict):
        return text
    
    # Se for string, tenta fazer parse direto (para outros providers)
    try:
        return json.loads(text)
    except:
        # Fallback básico
        return {
            "texto": str(text)[:1000],
            "titulo": "Generated Content",
            "descricao": "Automatically generated content",
            "hook": "Default hook",
            "hook_pt": "Hook padrão", 
            "thumb": "default",
            "tags": ["#default"]
        }

def save_json(dados: Dict[str, Any], out_dir: Path) -> Path:
    """Salva dados em arquivo JSON"""
    out_dir.mkdir(parents=True, exist_ok=True)
    _id = (dados.get("id") or "tmp").lstrip("#") or "tmp"
    path = out_dir / f"{_id}.json"
    path.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return path

def criar_pasta_roteiro(pasta_base: Path, id_video: str) -> Path:
    pasta_roteiro = pasta_base / id_video
    pasta_roteiro.mkdir(parents=True, exist_ok=True)
    return pasta_roteiro

def save_json_completo(dados: dict, pasta_roteiro: Path):
    id_video = dados["id_video"]
    
    caminho_json = pasta_roteiro / f"{id_video}.json"
    with open(caminho_json, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    
    caminho_txt = pasta_roteiro / f"{id_video}.txt"
    texto_pt = dados.get("texto_pt", dados.get("texto", ""))
    with open(caminho_txt, 'w', encoding='utf-8') as f:
        f.write(texto_pt)
    
    return caminho_json, caminho_txt

def obter_proximo_id(pasta_base: Path) -> str:
    """Obtém o próximo ID sequencial baseado nas pastas existentes"""
    if not pasta_base.exists():
        return "1"
    
    ids_existentes = []
    for item in pasta_base.iterdir():
        if item.is_dir() and item.name.isdigit():
            try:
                ids_existentes.append(int(item.name))
            except ValueError:
                continue
    
    proximo_id = max(ids_existentes) + 1 if ids_existentes else 1
    return str(proximo_id)

def vertical_horizontal(resolucao: str) -> str:
    """Determina se a resolução é vertical ou horizontal"""
    return "vertical" if resolucao == "720x1280" else "horizontal"

def clean_json_response(text: str) -> Dict[str, Any]:
    import ast
    
    text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"```$", "", text)
    text = re.sub(r"[\x00-\x1f\x7f]", "", text)  # remove caracteres de controle
    text = text.strip()
    text = re.sub(r"(?<!\\)\\'", "'", text)
    text = re.sub(r'(?<![\\"])"(?![\\"])', '"', text)
    text = text.replace('\\\\', '\\')

    # Caso 1: JSON puro
    try:
        return json.loads(text)
    except Exception:
        pass

    # Caso 2: JSON dentro de aspas
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        unquoted_text = text[1:-1]
        unquoted_text = unquoted_text.replace('\\"', '"').replace("\\'", "'").replace("\\n", "\n")
        try:
            return json.loads(unquoted_text)
        except Exception:
            try:
                return json.loads(unquoted_text)
            except Exception:
                pass

    # Caso 3: JSON dentro de string Python
    try:
        maybe = ast.literal_eval(text)
        if isinstance(maybe, str):
            cleaned_str = re.sub(r"(?<!\\)\\'", "'", maybe)
            try:
                return json.loads(cleaned_str)
            except Exception:
                match = re.search(r'\{[\s\S]*\}', cleaned_str)
                if match:
                    return json.loads(match.group(0))
        elif isinstance(maybe, dict):
            return maybe
    except Exception:
        pass

    # Caso 4: Reparação avançada
    try:
        repaired = re.sub(r"'([^']*)'", r'"\1"', text)
        repaired = re.sub(r"\[\s*'([^']*)'\s*\]", r'["\1"]', repaired)
        repaired = re.sub(r"\[\s*'([^']*)',\s*'([^']*)'\s*\]", r'["\1", "\2"]', repaired)
        return json.loads(repaired)
    except Exception:
        pass

    # Caso 5: Extração por regex
    try:
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                cleaned_match = re.sub(r"(?<!\\)\\'", "'", match)
                cleaned_match = re.sub(r'\s+', ' ', cleaned_match)
                return json.loads(cleaned_match)
            except Exception:
                continue
    except Exception:
        pass

    # Caso 6: Extração por linhas
    try:
        lines = text.split('\n')
        json_lines = []
        in_json = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('{') or in_json:
                json_lines.append(line)
                in_json = True
            if line.endswith('}'):
                break
        
        if json_lines:
            json_text = ' '.join(json_lines)
            json_text = re.sub(r"(?<!\\)\\'", "'", json_text)
            return json.loads(json_text)
    except Exception:
        pass

    raise ValueError(f"Não foi possível extrair JSON válido da resposta: {text[:200]}...")
    
def ajustar_timestamps_srt(arquivo_entrada: str, arquivo_saida: str = None) -> str:
    """
    Ajusta os timestamps de um arquivo SRT removendo gaps entre legendas
    
    Args:
        arquivo_entrada: Caminho para o arquivo SRT original
        arquivo_saida: Caminho para o arquivo SRT ajustado (opcional)
    
    Returns:
        str: Caminho do arquivo ajustado
    """
    def time_to_ms(time_str):
        hours, minutes, seconds = time_str.split(':')
        seconds, ms = seconds.split(',')
        return (int(hours) * 3600 + int(minutes) * 60 + int(seconds)) * 1000 + int(ms)

    def ms_to_time(ms):
        hours = ms // 3600000
        ms %= 3600000
        minutes = ms // 60000
        ms %= 60000
        seconds = ms // 1000
        ms %= 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"

    def parse_srt(content):
        blocks = content.strip().split('\n\n')
        subtitles = []
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                try:
                    index = int(lines[0])
                    time_match = re.match(r'(\d+:\d+:\d+,\d+) --> (\d+:\d+:\d+,\d+)', lines[1])
                    if time_match:
                        start = time_match.group(1)
                        end = time_match.group(2)
                        text = '\n'.join(lines[2:])
                        subtitles.append({
                            'index': index,
                            'start': start,
                            'end': end,
                            'text': text
                        })
                except ValueError:
                    continue
        return subtitles

    def save_srt(subtitles, output_path):
        with open(output_path, 'w', encoding='utf-8') as file:
            for sub in subtitles:
                file.write(f"{sub['index']}\n")
                file.write(f"{sub['start']} --> {sub['end']}\n")
                file.write(f"{sub['text']}\n\n")

    # Processamento principal
    if arquivo_saida is None:
        arquivo_saida = arquivo_entrada.replace('.srt', '_ajustado.srt')
    
    # Ler arquivo original
    with open(arquivo_entrada, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    subtitles = parse_srt(conteudo)
    
    if not subtitles:
        raise ValueError("Nenhuma legenda válida encontrada no arquivo")
    
    # Ajustar timestamps
    total_correction = 0
    previous_end = None
    
    for i, subtitle in enumerate(subtitles):
        start_ms = time_to_ms(subtitle['start'])
        end_ms = time_to_ms(subtitle['end'])
        
        if previous_end is not None:
            gap = start_ms - previous_end
            if gap > 0:
                total_correction += gap
                print(f"Ajustando gap de {gap}ms entre as legendas {i} e {i+1}")
        
        start_ms -= total_correction
        end_ms -= total_correction
        
        subtitle['start'] = ms_to_time(start_ms)
        subtitle['end'] = ms_to_time(end_ms)
        previous_end = end_ms + total_correction  # Usar o valor original para cálculo do próximo gap
    
    # Salvar arquivo ajustado
    save_srt(subtitles, arquivo_saida)
    
    tempo_total_original = time_to_ms(subtitles[-1]['end']) + total_correction
    tempo_total_ajustado = time_to_ms(subtitles[-1]['end'])
    
    print(f"\nArquivo ajustado salvo como: {arquivo_saida}")
    print(f"Tempo total corrigido: {total_correction/1000:.2f} segundos")
    print(f"Tempo original: {tempo_total_original/1000:.2f}s → Tempo ajustado: {tempo_total_ajustado/1000:.2f}s")
    
    return arquivo_saida


def srt_to_seconds(timestamp):
    """Converte timestamp SRT para segundos"""
    time_part, ms = timestamp.split(',')
    h, m, s = time_part.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

def seconds_to_srt(seconds):
    """Converte segundos para formato SRT"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def ajustar_legenda_srt(srt_original, srt_ajustado, cortes):
    """Ajusta timestamps do SRT baseado nos cortes aplicados - VERSÃO CORRIGIDA"""
    try:
        with open(srt_original, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Processa cada bloco de legenda
        blocks = content.strip().split('\n\n')
        output_blocks = []
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                # Linha 1: número
                # Linha 2: timestamp
                num_line = lines[0]
                time_line = lines[1]
                
                if '-->' in time_line:
                    start_str, end_str = time_line.split(' --> ')
                    start_sec = srt_to_seconds(start_str)
                    end_sec = srt_to_seconds(end_str)
                    
                    # ✅ CORREÇÃO: Calcula offset total acumulado de todos os cortes anteriores
                    offset_total = 0
                    for corte in cortes:
                        corte_start = corte['start'] + 0.1
                        corte_end = corte['end'] - 0.1
                        duracao_cortada = corte_end - corte_start
                        
                        # Se o corte aconteceu ANTES do início desta legenda, aplica offset
                        if corte_end < start_sec:
                            offset_total += duracao_cortada
                    
                    # Aplica offset total
                    new_start_sec = max(0, start_sec - offset_total)
                    new_end_sec = max(0, end_sec - offset_total)
                    
                    # ✅ CORREÇÃO ADICIONAL: Garante que não há sobreposição entre legendas
                    if output_blocks:
                        # Pega o último bloco para verificar o fim da legenda anterior
                        last_block = output_blocks[-1].split('\n')
                        if len(last_block) >= 2 and '-->' in last_block[1]:
                            last_end_str = last_block[1].split(' --> ')[1]
                            last_end_sec = srt_to_seconds(last_end_str)
                            
                            # Se há sobreposição, ajusta o início para depois do fim da anterior
                            if new_start_sec < last_end_sec:
                                new_start_sec = last_end_sec + 0.001  # Pequeno gap de 1ms
                    
                    # Converte de volta para formato SRT
                    new_start = seconds_to_srt(new_start_sec)
                    new_end = seconds_to_srt(new_end_sec)
                    
                    new_time_line = f"{new_start} --> {new_end}"
                    new_block = f"{num_line}\n{new_time_line}\n" + '\n'.join(lines[2:])
                    output_blocks.append(new_block)
        
        # Salva arquivo ajustado
        with open(srt_ajustado, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(output_blocks))
            
        print(f"✅ Legendas ajustadas: {len(output_blocks)} blocos processados")
        
    except Exception as e:
        print(f"⚠️  Erro ao ajustar legenda: {e}")
        # Se der erro, copia o original para o ajustado
        import shutil
        shutil.copy2(srt_original, srt_ajustado)


def otimizar_audio_e_legenda(audio_path: str, srt_path: str = None) -> tuple:
    """
    Otimiza áudio cortando pausas longas e ajusta legenda SRT correspondente
    Retorna: (audio_otimizado_path, srt_ajustado_path)
    """
    try:
        audio_file = Path(audio_path)
        srt_file = Path(srt_path) if srt_path else None
        
        # Arquivos de saída
        audio_otimizado = audio_file.parent / f"{audio_file.stem}_otimizado{audio_file.suffix}"
        
        # ✅ CORREÇÃO: SRT mantém o nome original, não cria "_ajustado"
        srt_ajustado = srt_file  # Usa o mesmo arquivo original
        
        # 1. Detectar silêncios
        print("🔍 Detectando pausas longas no áudio...")
        cmd_detect = [
            'ffmpeg',
            '-i', str(audio_file),
            '-af', 'silencedetect=noise=-40dB:d=0.5',
            '-f', 'null',
            '-'
        ]
        
        result = subprocess.run(cmd_detect, capture_output=True, text=True)
        silencios = []
        lines = result.stderr.split('\n')
        
        for i, line in enumerate(lines):
            if 'silence_start:' in line:
                start = float(line.split('silence_start:')[1].strip())
            elif 'silence_end:' in line and '|' in line:
                end = float(line.split('silence_end:')[1].split('|')[0].strip())
                duration = end - start
                if duration > 0.5:  # Só pausas longas
                    silencios.append({'start': start, 'end': end, 'duration': duration})
        
        if not silencios:
            print("ℹ️  Nenhuma pausa longa encontrada para cortar")
            return str(audio_file), str(srt_file) if srt_file else None
        
        print(f"✂️  Encontradas {len(silencios)} pausas longas para otimizar")
        
        # 2. Cortar áudio
        with tempfile.TemporaryDirectory() as temp_dir:
            # Cria arquivo de cortes para ffmpeg
            filter_script = os.path.join(temp_dir, 'filter_script.txt')
            with open(filter_script, 'w', encoding='utf-8') as f:
                f.write("ffconcat version 1.0\n")
                
                current_pos = 0
                for silencio in silencios:
                    # Mantém 0.1s no início e fim da pausa
                    corte_start = silencio['start'] + 0.1
                    corte_end = silencio['end'] - 0.1
                    
                    if current_pos < corte_start:
                        f.write(f"file '{audio_file}'\n")
                        f.write(f"inpoint {current_pos}\n")
                        f.write(f"outpoint {corte_start}\n")
                    
                    current_pos = corte_end
                
                # Último segmento
                f.write(f"file '{audio_file}'\n")
                f.write(f"inpoint {current_pos}\n")
            
            # Aplica cortes
            cmd_cortar = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', filter_script,
                '-c', 'copy',
                str(audio_otimizado)
            ]
            
            subprocess.run(cmd_cortar, check=True, capture_output=True)
        
        print(f"✅ Áudio otimizado: {audio_otimizado}")
        
        # 3. Ajustar legenda SRT se existir (SOBRESCREVE o arquivo original)
        if srt_file and srt_file.exists():
            # ✅ NOVO: Verifica problemas antes de ajustar
            print("🔍 Verificando problemas no SRT original...")
            problemas = verificar_problemas_srt(srt_file)
            
            # ✅ CORREÇÃO: Cria arquivo temporário, ajusta, depois substitui o original
            srt_temp = srt_file.parent / f"{srt_file.stem}_temp{srt_file.suffix}"
            ajustar_legenda_srt(srt_file, srt_temp, silencios)
            
            # ✅ NOVO: Verifica problemas após ajuste
            print("🔍 Verificando problemas no SRT ajustado...")
            problemas_apos = verificar_problemas_srt(srt_temp)
            
            # Substitui o arquivo original pelo ajustado
            srt_file.unlink()  # Remove original
            srt_temp.rename(srt_file)  # Renomeia temp para original
            
            print(f"✅ Legenda SRT ajustada e sobrescrita: {srt_file}")
        else:
            srt_ajustado = None
        
        return str(audio_otimizado), str(srt_ajustado) if srt_ajustado else None
        
    except Exception as e:
        print(f"⚠️  Erro na otimização de áudio: {e}")
        return audio_path, srt_path

def analisar_gaps_srt(arquivo_srt: str) -> Dict[str, Any]:
    """
    Analisa os gaps entre legendas SRT sem modificar o arquivo
    
    Args:
        arquivo_srt: Caminho para o arquivo SRT
    
    Returns:
        Dict com informações sobre os gaps
    """
    def time_to_ms(time_str):
        hours, minutes, seconds = time_str.split(':')
        seconds, ms = seconds.split(',')
        return (int(hours) * 3600 + int(minutes) * 60 + int(seconds)) * 1000 + int(ms)

    def parse_srt(content):
        blocks = content.strip().split('\n\n')
        subtitles = []
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                try:
                    index = int(lines[0])
                    time_match = re.match(r'(\d+:\d+:\d+,\d+) --> (\d+:\d+:\d+,\d+)', lines[1])
                    if time_match:
                        start = time_match.group(1)
                        end = time_match.group(2)
                        text = '\n'.join(lines[2:])
                        subtitles.append({
                            'index': index,
                            'start': start,
                            'end': end,
                            'text': text,
                            'start_ms': time_to_ms(start),
                            'end_ms': time_to_ms(end)
                        })
                except ValueError:
                    continue
        return subtitles

    # Ler e analisar arquivo
    with open(arquivo_srt, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    subtitles = parse_srt(conteudo)
    gaps = []
    total_gap = 0
    
    for i in range(len(subtitles) - 1):
        current_end = subtitles[i]['end_ms']
        next_start = subtitles[i + 1]['start_ms']
        gap = next_start - current_end
        
        if gap > 0:
            gaps.append({
                'entre_legendas': f"{i+1} → {i+2}",
                'gap_ms': gap,
                'gap_segundos': gap / 1000,
                'legenda_anterior': subtitles[i]['text'][:50] + "...",
                'proxima_legenda': subtitles[i + 1]['text'][:50] + "..."
            })
            total_gap += gap
    
    return {
        'total_legendas': len(subtitles),
        'total_gaps': len(gaps),
        'tempo_total_gaps_ms': total_gap,
        'tempo_total_gaps_segundos': total_gap / 1000,
        'gaps_detectados': gaps,
        'duracao_total_original_ms': subtitles[-1]['end_ms'] if subtitles else 0,
        'duracao_total_ajustada_ms': (subtitles[-1]['end_ms'] - total_gap) if subtitles else 0
    }

def verificar_problemas_srt(srt_path: str):
    """
    Verifica problemas comuns no arquivo SRT
    """
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        blocks = content.strip().split('\n\n')
        problemas = []
        
        for i, block in enumerate(blocks):
            lines = block.split('\n')
            if len(lines) >= 3:
                try:
                    num = int(lines[0])
                    time_line = lines[1]
                    
                    if '-->' in time_line:
                        start_str, end_str = time_line.split(' --> ')
                        start_sec = srt_to_seconds(start_str)
                        end_sec = srt_to_seconds(end_str)
                        
                        # Verifica duração muito curta
                        if end_sec - start_sec < 0.1:
                            problemas.append(f"Legenda {num}: Duração muito curta ({end_sec - start_sec:.2f}s)")
                        
                        # Verifica sobreposição com próximo bloco
                        if i < len(blocks) - 1:
                            next_block = blocks[i + 1].split('\n')
                            if len(next_block) >= 3 and '-->' in next_block[1]:
                                next_start_str = next_block[1].split(' --> ')[0]
                                next_start_sec = srt_to_seconds(next_start_str)
                                
                                if end_sec > next_start_sec:
                                    problemas.append(f"Legenda {num}: Sobreposição com próxima ({end_sec - next_start_sec:.2f}s)")
                        
                        # Verifica ordem cronológica
                        if end_sec < start_sec:
                            problemas.append(f"Legenda {num}: Fim antes do início")
                            
                except (ValueError, IndexError) as e:
                    problemas.append(f"Bloco {i+1}: Formato inválido - {e}")
        
        if problemas:
            print("⚠️  Problemas detectados no SRT:")
            for problema in problemas:
                print(f"   - {problema}")
        else:
            print("✅ SRT sem problemas detectados")
            
        return problemas
        
    except Exception as e:
        print(f"❌ Erro ao verificar SRT: {e}")
        return []

def limitar_srt_10_palavras(srt_file):
    """
    Limita o arquivo SRT a no máximo 10 palavras por legenda
    Retorna o caminho do arquivo SRT modificado
    """
    try:
        subs = pysrt.open(srt_file)
        novos_subs = []
        
        for sub in subs:
            texto = sub.text
            palavras = texto.split()
            
            if len(palavras) <= 10:
                # Se já tem 10 palavras ou menos, mantém como está
                novos_subs.append(sub)
            else:
                # Divide em grupos de até 10 palavras
                grupos = [palavras[i:i+10] for i in range(0, len(palavras), 10)]
                duracao_total = sub.end.ordinal - sub.start.ordinal
                duracao_por_grupo = duracao_total // len(grupos)
                
                for i, grupo in enumerate(grupos):
                    inicio = sub.start.ordinal + (i * duracao_por_grupo)
                    fim = inicio + duracao_por_grupo
                    
                    # Para o último grupo, usar o tempo final original
                    if i == len(grupos) - 1:
                        fim = sub.end.ordinal
                    
                    novo_sub = pysrt.SubRipItem(
                        index=len(novos_subs) + 1,
                        start=pysrt.SubRipTime(milliseconds=inicio),
                        end=pysrt.SubRipTime(milliseconds=fim),
                        text=' '.join(grupo)
                    )
                    novos_subs.append(novo_sub)
        
        # Salva o arquivo modificado
        novo_srt = pysrt.SubRipFile(items=novos_subs)
        novo_srt.save(srt_file, encoding='utf-8')
        return srt_file
        
    except Exception as e:
        print(f"❌ Erro ao limitar SRT a 10 palavras: {e}")
        return None