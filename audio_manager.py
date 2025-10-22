import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Corrige imports - adiciona o caminho atual ao sys.path
sys.path.append(str(Path(__file__).parent))

try:
    from read_config import carregar_config_canal
    from providers import create_tts_provider
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    # Tenta import absoluto como fallback
    try:
        import read_config
        carregar_config_canal = read_config.carregar_config_canal
        
        from providers import create_tts_provider
    except ImportError:
        print("❌ Não foi possível importar os módulos necessários")
        sys.exit(1)

class AudioManager:
    """Gerenciador central de áudio - Versão simplificada e modular"""
    
    def _carregar_texto_do_roteiro(self, roteiro_path: Path, config: Dict[str, Any]) -> tuple:
        """Carrega o texto do roteiro de forma compatível"""
        try:
            with open(roteiro_path, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            # Encontra o texto para sintetizar
            idioma = dados.get('idioma', config.get('IDIOMA', 'pt'))
            chave_texto = f"texto_{idioma}"
            
            # Fallback para chaves comuns
            if chave_texto not in dados:
                for chave in ['texto_pt', 'texto_en', 'texto']:
                    if chave in dados:
                        chave_texto = chave
                        break
            
            if chave_texto not in dados:
                print(f"❌ Texto não encontrado no roteiro. Chaves disponíveis: {list(dados.keys())}")
                return None, None
            
            texto = dados[chave_texto]
            if not texto or len(texto.strip()) < 10:
                print("❌ Texto muito curto ou vazio para sintetizar")
                return None, None
            
            return texto, dados
            
        except Exception as e:
            print(f"❌ Erro ao carregar roteiro: {e}")
            return None, None
    
    def gerar_audio(self, roteiro_path: Path, canal: str, provider: str = None) -> bool:
        """Gera áudio para um roteiro"""
        
        # Carrega configuração do canal
        try:
            config = carregar_config_canal(canal)
        except Exception as e:
            print(f"❌ Erro ao carregar configuração do canal '{canal}': {e}")
            return False
        
        # Carrega texto do roteiro
        texto, dados = self._carregar_texto_do_roteiro(roteiro_path, config)
        if not texto:
            return False
        
        # Determina provedor (edge como padrão)
        if not provider:
            provider = config.get('TTS_PROVIDER', 'edge')
        
        # Cria o provedor via factory
        try:
            provider_instance = create_tts_provider(provider)
        except ValueError as e:
            print(f"❌ {e}")
            return False
        
        # Prepara caminho de saída
        pasta_roteiro = roteiro_path.parent
        video_id = dados.get('Id', roteiro_path.stem)
        arquivo_audio = pasta_roteiro / f"{video_id}.mp3"
        
        print(f"🎵 Gerando áudio com {provider.upper()}...")
        print(f"📝 Texto: {len(texto)} caracteres")
        print(f"🎯 Idioma: {dados.get('idioma', 'N/A')}")
        print(f"🔊 Voz: {config.get('EDGE_TTS_VOICE', 'N/A')}")
        print(f"💾 Saída: {arquivo_audio}")
        
        # Gera áudio
        success = provider_instance.sintetizar(texto, arquivo_audio, config)
        
        if success:
            # Atualiza dados do roteiro com informações do áudio
            dados['audio_gerado'] = True
            dados['arquivo_audio'] = str(arquivo_audio)
            dados['tts_provider'] = provider
            dados['voz_tts'] = config.get('EDGE_TTS_VOICE', 'N/A')
            
            # Adiciona informações de legendas se aplicável
            if provider == 'edge' and config.get('EDGE_TTS_LEGENDAS', True):
                srt_path = arquivo_audio.with_suffix('.srt')
                if srt_path.exists():
                    dados['arquivo_legenda'] = str(srt_path)
            
            with open(roteiro_path, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Áudio gerado com sucesso!")
            return True
        
        return False