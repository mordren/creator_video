# roteiro_manager.py
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime
from utils import obter_proximo_id, vertical_horizontal

class RoteiroManager:
    """Manager unificado para operações com roteiros"""
    
    def __init__(self, pasta_base: Path):
        self.pasta_base = Path(pasta_base)
        self.pasta_base.mkdir(parents=True, exist_ok=True)
    

    def criar_pasta_roteiro(self, roteiro_id: str = None) -> Path:
        """Cria pasta para o roteiro com ID específico ou próximo disponível"""
        if not roteiro_id:
            roteiro_id = obter_proximo_id()
        
        pasta_roteiro = self.pasta_base / roteiro_id
        pasta_roteiro.mkdir(parents=True, exist_ok=True)
        return pasta_roteiro
    
    def salvar_arquivos_roteiro(self, dados: Dict, pasta_roteiro: Path) -> Path:
        """Salva arquivo JSON do roteiro"""
        roteiro_id = pasta_roteiro.name
        
        # Salva JSON com metadados
        caminho_json = pasta_roteiro / f"{roteiro_id}.json"
        with open(caminho_json, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        return caminho_json
    
    def salvar_roteiro_completo(self, dados: Dict, config: Dict) -> Dict:
        """
        Salva roteiro completo: pasta, arquivos e banco de dados
        """
        from crud.manager import DatabaseManager

        # ✅ CORREÇÃO: Garantir que temos um ID válido
        roteiro_id = dados.get('id_roteiro')
        
        # Se não tem ID ou é inválido, gerar novo
        if not roteiro_id or not roteiro_id.isdigit() or roteiro_id == "Vídeos Automáticos":
            roteiro_id = obter_proximo_id(self.pasta_base)
            print(f"🆔 Gerado novo ID: {roteiro_id}")
        
        # Cria pasta do roteiro
        pasta_roteiro = self.criar_pasta_roteiro(roteiro_id)
        
        # Atualiza dados com ID do roteiro
        dados['id_roteiro'] = roteiro_id
        dados['canal'] = config.get('NOME')
        dados['data_criacao'] = datetime.now().isoformat()
        
        # Salva arquivos
        caminho_json = self.salvar_arquivos_roteiro(dados, pasta_roteiro)
        
        # Salva no banco de dados
        resultado_db = self._salvar_no_banco(dados, config)
        
        return {
            'id_roteiro': roteiro_id,
            'pasta_roteiro': pasta_roteiro,
            'arquivo_json': caminho_json,            
            'dados': dados,
            'db_result': resultado_db
        }
                
    def _salvar_no_banco(self, dados: dict, config: dict) -> dict:
        """Salva roteiro no banco de dados"""
        try:
            from crud.manager import DatabaseManager
            db = DatabaseManager()
            nome_canal = config.get('NOME')

            # Busca ou cria o canal
            canal = db.buscar_canal_por_nome(nome_canal)
            if not canal:
                canal = db.criar_canal(nome=nome_canal, config_path=str(config.get('PASTA_CANAL', '')))
            
            # ✅ CORREÇÃO CRÍTICA: Usar o ID do roteiro como id_video
            # O id_video deve ser único, como "1", "2", etc.
            id_video = dados['id_roteiro']
            
            # ✅ VERIFICAÇÃO: Se o id_video não é um ID válido, gerar um novo
            if not id_video or not id_video.isdigit() or id_video == "Vídeos Automáticos":
                print(f"⚠️ ID inválido detectado: {id_video}. Gerando novo ID...")
                id_video = obter_proximo_id(self.pasta_base)
                dados['id_roteiro'] = id_video  # Atualiza também nos dados
            
            # Prepara dados para o roteiro usando o novo modelo
            roteiro_data = {
                'id_video': id_video,  # ✅ Agora é um ID único como "1", "2", etc.
                'titulo': dados.get('titulo') or "Título temporário",                 
                'texto': dados.get('texto') or "",
                'descricao': dados.get('descricao') or "",
                'tags': ', '.join(dados.get('tags', [])),
                'thumb': dados.get('thumb') or "thumb_temporaria",                                
                'canal_id': canal.id,                
                'resolucao': config.get('RESOLUCAO', 'vertical')
            }
            
            # ✅ VERIFICA se já existe um roteiro com esse id_video
            roteiro_existente = db.buscar_roteiro_por_id_video(id_video)
            if roteiro_existente:
                print(f"⚠️ Roteiro com id_video {id_video} já existe. Atualizando...")
                # Atualiza o roteiro existente
                roteiro_existente.titulo = roteiro_data['titulo']
                roteiro_existente.texto = roteiro_data['texto']
                roteiro_existente.descricao = roteiro_data['descricao']
                roteiro_existente.tags = roteiro_data['tags']
                roteiro_existente.thumb = roteiro_data['thumb']
                roteiro_existente.resolucao = roteiro_data['resolucao']
                
                with db as manager:
                    manager.session.commit()
                
                roteiro_db = roteiro_existente
            else:
                # Cria novo roteiro
                roteiro_db = db.criar_roteiro(**roteiro_data)
            
            # Se temos dados de áudio, criar também o vídeo
            if dados.get('audio_gerado') or dados.get('arquivo_audio'):
                video_data = {
                    'roteiro_id': roteiro_db.id,
                    'titulo': roteiro_data['titulo'],
                    'thumb': roteiro_data['thumb'],
                    'arquivo_audio': dados.get('arquivo_audio'),
                    'arquivo_legenda': dados.get('arquivo_legenda'),
                    'tts_provider': dados.get('tts_provider'),
                    'voz_tts': dados.get('voz_tts'),
                    'duracao': dados.get('duracao')
                }
                
                # Verifica se já existe vídeo para este roteiro
                video_existente = db.buscar_video_por_roteiro_id(roteiro_db.id)
                if video_existente:
                    # Atualiza vídeo existente
                    video_existente.arquivo_audio = video_data['arquivo_audio']
                    video_existente.arquivo_legenda = video_data['arquivo_legenda']
                    video_existente.tts_provider = video_data['tts_provider']
                    video_existente.voz_tts = video_data['voz_tts']
                    video_existente.duracao = video_data['duracao']
                    
                    with db as manager:
                        manager.session.commit()
                else:
                    # Cria novo vídeo
                    db.criar_video(**video_data)
            
            return {'sucesso': True, 'id_banco': roteiro_db.id}
            
        except Exception as e:
            print(f"❌ Erro ao salvar no banco: {e}")
            return {'sucesso': False, 'erro': str(e)}
    
            
    def listar_roteiros(self, limite: int = 10) -> list:
        """Lista os roteiros mais recentes"""
        pastas = []
        for item in self.pasta_base.iterdir():
            if item.is_dir() and item.name.isdigit():
                pastas.append(item)
        
        # Ordena por ID (numérico) e pega os mais recentes
        pastas.sort(key=lambda x: int(x.name), reverse=True)
        return pastas[:limite]
    
    def buscar_roteiro_por_id(self, roteiro_id: str) -> Optional[Dict]:
        """Busca roteiro por ID"""
        pasta_roteiro = self.pasta_base / roteiro_id
        if not pasta_roteiro.exists():
            return None
        
        arquivo_json = pasta_roteiro / f"{roteiro_id}.json"
        if not arquivo_json.exists():
            return None
        
        try:
            with open(arquivo_json, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            return {
                'id_roteiro': roteiro_id,
                'pasta_roteiro': pasta_roteiro,
                'dados': dados
            }
        except Exception:
            return None