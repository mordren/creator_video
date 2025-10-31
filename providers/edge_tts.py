import asyncio
from pathlib import Path
from typing import Dict, Any
import edge_tts

from .base_audio import TTSProvider
# CORREÇÃO: Importar do video_utils (que está no diretório raiz)
from video_maker.video_utils import ajustar_timestamps_srt, analisar_gaps_srt

class EdgeTTSProvider(TTSProvider):
    """Provedor Microsoft Edge TTS - Gratuito e com suporte a legendas SRT"""
    
    def sintetizar(self, texto: str, output_path: Path, config: Dict[str, Any], is_short = bool) -> bool:
        try:
            voice = config.get('EDGE_TTS_VOICE', 'pt-BR-AntonioNeural')

            if is_short:
                rate = config.get('EDGE_TTS_RATE', '0%')
            else:
                rate = "-5%"

            pitch = config.get('EDGE_TTS_PITCH', '0Hz')
            gerar_legendas = config.get('EDGE_TTS_LEGENDAS', True)
            ajustar_timestamps = config.get('EDGE_TTS_AJUSTAR_TIMESTAMPS', True)  # Nova configuração
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            

            if gerar_legendas:
                srt_path = output_path.with_suffix('.srt')
                success = loop.run_until_complete(
                    self._gerar_audio_e_legendas(texto, output_path, srt_path, voice, rate, pitch)
                )
                
                # Ajustar timestamps se configurado
                if success and ajustar_timestamps:
                    self._ajustar_legendas_apos_geracao(srt_path)
            else:
                success = loop.run_until_complete(
                    self._gerar_apenas_audio(texto, output_path, voice, rate, pitch)
                )
            
            loop.close()
            
            if success:
                print(f"✅ Áudio Edge TTS gerado: {output_path}")
                if gerar_legendas:
                    print(f"✅ Legendas SRT geradas: {srt_path}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Erro no Edge TTS: {e}")
            return False
    
    async def _gerar_audio_e_legendas(self, texto: str, mp3_path: Path, srt_path: Path, 
                                    voice: str, rate: str, pitch: str) -> bool:
        communicate = edge_tts.Communicate(texto, voice=voice, rate=rate, pitch=pitch)
        sub = edge_tts.SubMaker()
        
        with open(mp3_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                    sub.feed(chunk)
        
        srt_content = sub.get_srt()
        srt_path.write_text(srt_content, encoding="utf-8")
        return True
    
    async def _gerar_apenas_audio(self, texto: str, mp3_path: Path, 
                                voice: str, rate: str, pitch: str) -> bool:
        communicate = edge_tts.Communicate(texto, voice=voice, rate=rate, pitch=pitch)
        
        with open(mp3_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
        return True
    
    def _ajustar_legendas_apos_geracao(self, srt_path: Path):
        """
        Ajusta os timestamps das legendas após a geração para remover gaps
        e limita a 10 palavras por linha mantendo os timestamps
        """
        try:
            if not srt_path.exists():
                print(f"❌ Arquivo de legenda não encontrado: {srt_path}")
                return
            
            # Primeiro, limitar palavras por linha
            print("🔧 Limitando legendas a 10 palavras por linha...")
            srt_limitado = self._limitar_palavras_por_linha(srt_path)
            
            # Depois, ajustar gaps
            print("🔧 Analisando gaps nas legendas geradas...")
            analise = analisar_gaps_srt(str(srt_limitado))
            
            if analise['total_gaps'] > 0:
                print(f"📊 Detectados {analise['total_gaps']} gaps totalizando {analise['tempo_total_gaps_segundos']:.2f}s")
                
                # Criar backup antes de ajustar
                backup_path = srt_path.with_suffix('.srt.backup')
                import shutil
                shutil.copy2(srt_path, backup_path)
                
                # Ajustar timestamps
                arquivo_ajustado = ajustar_timestamps_srt(str(srt_path), str(srt_path))
                
                print(f"✅ Legendas ajustadas: {arquivo_ajustado}")
                print(f"💾 Backup salvo em: {backup_path}")
            else:
                print("✅ Nenhum gap significativo detectado nas legendas")
                
        except Exception as e:
            print(f"❌ Erro ao ajustar legendas: {e}")

    def _limitar_palavras_por_linha(self, srt_path: Path, max_palavras: int = 10) -> Path:
        """
        Limita o número de palavras por linha em legendas SRT, mantendo os timestamps
        e distribuindo o texto em múltiplas linhas quando necessário
        """
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
            
            novo_conteudo = []
            i = 0
            total_linhas_quebradas = 0
            
            while i < len(linhas):
                linha = linhas[i].strip()
                
                # Se for número da legenda ou timestamp, mantém como está
                if not linha or linha.isdigit() or '-->' in linha:
                    novo_conteudo.append(linhas[i])
                    i += 1
                    continue
                
                # Se for texto da legenda
                palavras = linha.split()
                if len(palavras) <= max_palavras:
                    # Mantém a linha original se já estiver dentro do limite
                    novo_conteudo.append(linhas[i])
                    i += 1
                else:
                    # Quebra a linha em múltiplas linhas
                    linhas_quebradas = self._quebrar_linha_legenda(palavras, max_palavras)
                    
                    # Adiciona as linhas quebradas
                    for linha_quebrada in linhas_quebradas:
                        novo_conteudo.append(linha_quebrada + '\n')
                    
                    total_linhas_quebradas += len(linhas_quebradas)
                    i += 1
            
            # Salva o arquivo modificado
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.writelines(novo_conteudo)
            
            if total_linhas_quebradas > 0:
                print(f"✅ {total_linhas_quebradas} linhas quebradas para máximo de {max_palavras} palavras")
            
            return srt_path
            
        except Exception as e:
            print(f"❌ Erro ao limitar palavras por linha: {e}")
            return srt_path

    def _quebrar_linha_legenda(self, palavras: list, max_palavras: int) -> list:
        """
        Quebra uma linha de legenda em múltiplas linhas respeitando o limite de palavras
        e tentando manter a coesão do texto
        """
        linhas_quebradas = []
        linha_atual = []
        
        for palavra in palavras:
            linha_atual.append(palavra)
            
            # Quebra quando atingir o limite máximo
            if len(linha_atual) >= max_palavras:
                # Tenta quebrar em ponto natural (final de frase)
                if palavra.endswith(('.', '!', '?', ',', ';', ':')):
                    linhas_quebradas.append(' '.join(linha_atual))
                    linha_atual = []
                else:
                    # Se não encontrou ponto natural, quebra mesmo assim
                    linhas_quebradas.append(' '.join(linha_atual))
                    linha_atual = []
        
        # Adiciona as palavras restantes
        if linha_atual:
            linhas_quebradas.append(' '.join(linha_atual))
        
        return linhas_quebradas

    # Alternativa mais sofisticada que tenta quebrar em pontos lógicos
    def _quebrar_linha_inteligente(self, palavras: list, max_palavras: int) -> list:
        """
        Versão mais inteligente que tenta quebrar as linhas em pontos lógicos
        para melhor legibilidade
        """
        if len(palavras) <= max_palavras:
            return [' '.join(palavras)]
        
        linhas_quebradas = []
        inicio = 0
        
        while inicio < len(palavras):
            # Tenta encontrar o melhor ponto para quebrar
            fim = min(inicio + max_palavras, len(palavras))
            
            # Se não é o final, tenta ajustar o ponto de quebra
            if fim < len(palavras):
                # Procura por pontuação para quebra natural
                melhor_quebra = fim
                for i in range(fim - 1, inicio, -1):
                    if palavras[i].endswith(('.', '!', '?', ',', ';', ':')):
                        melhor_quebra = i + 1
                        break
                
                # Se não encontrou pontuação, procura por conjunções
                if melhor_quebra == fim:
                    for i in range(fim - 1, inicio, -1):
                        if palavras[i].lower() in ['e', 'mas', 'porém', 'contudo', 'entretanto', 'pois']:
                            melhor_quebra = i + 1
                            break
                
                fim = melhor_quebra
            
            linha = ' '.join(palavras[inicio:fim])
            linhas_quebradas.append(linha)
            inicio = fim
        
        return linhas_quebradas