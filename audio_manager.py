import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Corrige imports
sys.path.append(str(Path(__file__).parent))

try:
    from read_config import carregar_config_canal
    from providers import create_tts_provider
    from crud import DatabaseManager  # ← Import limpo!
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    sys.exit(1)

class AudioManager:
    def __init__(self):
        self.db = DatabaseManager()
    
    def _carregar_texto_do_roteiro(self, roteiro_path: Path, config: Dict[str, Any]) -> tuple:
        try:
            with open(roteiro_path, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            idioma = dados.get('idioma', config.get('IDIOMA', 'pt'))
            chave_texto = f"texto_{idioma}"
            
            if chave_texto not in dados:
                for chave in ['texto_pt', 'texto_en', 'texto']:
                    if chave in dados:
                        chave_texto = chave
                        break
            
            if chave_texto not in dados:
                print(f"❌ Texto não encontrado. Chaves: {list(dados.keys())}")
                return None, None
            
            texto = dados[chave_texto]
            if not texto or len(texto.strip()) < 10:
                print("❌ Texto muito curto")
                return None, None
            
            return texto, dados
            
        except Exception as e:
            print(f"❌ Erro ao carregar roteiro: {e}")
            return None, None
    
    def gerar_audio(self, roteiro_path: Path, canal: str, provider: str = None) -> bool:
        try:
            config = carregar_config_canal(canal)
        except Exception as e:
            print(f"❌ Erro ao carregar canal '{canal}': {e}")
            return False
        
        texto, dados = self._carregar_texto_do_roteiro(roteiro_path, config)
        if not texto:
            return False
        
        if not provider:
            provider = config.get('TTS_PROVIDER', 'edge')
        
        try:
            provider_instance = create_tts_provider(provider)
        except ValueError as e:
            print(f"❌ {e}")
            return False
        
        pasta_roteiro = roteiro_path.parent
        video_id = dados.get('Id', roteiro_path.stem)
        arquivo_audio = pasta_roteiro / f"{video_id}.mp3"
        
        print(f"🎵 Gerando áudio com {provider.upper()}...")
        print(f"📝 Texto: {len(texto)} caracteres")
        print(f"🎯 Idioma: {dados.get('idioma', 'N/A')}")
        
        if provider == 'gemini':
            print(f"🔊 Voz: {config.get('GEMINI_TTS_VOICE', 'N/A')}")
        else:
            print(f"🔊 Voz: {config.get('EDGE_TTS_VOICE', 'N/A')}")
            
        print(f"💾 Saída: {arquivo_audio}")
        
        success = provider_instance.sintetizar(texto, arquivo_audio, config)
        
        if success:
            # Salva no banco de dados
            self._salvar_no_banco(dados, str(arquivo_audio), provider, canal, config)
            
            # Atualiza JSON local
            dados['audio_gerado'] = True
            dados['arquivo_audio'] = str(arquivo_audio)
            dados['tts_provider'] = provider
            dados['voz_tts'] = config.get('EDGE_TTS_VOICE', 'N/A')
            
            if provider == 'edge' and config.get('EDGE_TTS_LEGENDAS', True):
                srt_path = arquivo_audio.with_suffix('.srt')
                if srt_path.exists():
                    dados['arquivo_legenda'] = str(srt_path)
            
            with open(roteiro_path, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Áudio gerado com sucesso!")
            return True
        
        return False
    
    def _salvar_no_banco(self, dados: Dict, arquivo_audio: str, provider: str, canal_nome: str, config: Dict):
        """Salva informações no banco de dados"""
        try:
            # Busca ou cria canal
            canal_db = self.db.buscar_canal_por_nome(canal_nome)
            if not canal_db:
                canal_db = self.db.criar_canal(
                    nome=canal_nome,
                    config_path=str(config.get('PASTA_CANAL', ''))
                )
            
            # Cria roteiro no banco
            roteiro_db = self.db.criar_roteiro(
                canal_id=canal_db.id,
                titulo_a=dados.get('titulo', 'Sem título'),
                texto_pt=dados.get('texto_pt', ''),
                descricao=dados.get('descricao', ''),
                tags=dados.get('tags', ''),
                arquivo_audio=arquivo_audio,
                tts_provider=provider,
                voz_tts=config.get('EDGE_TTS_VOICE', ''),
                audio_gerado=True,
                vertical=True
            )
            
            print(f"💾 Salvo no banco: Roteiro ID {roteiro_db.id}")
            
        except Exception as e:
            print(f"⚠️ Aviso: Não foi possível salvar no banco: {e}")