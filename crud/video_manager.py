#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

class VideoManager:
    """Manager unificado para operações com vídeos"""
    
    def __init__(self, pasta_base: Path):
        self.pasta_base = Path(pasta_base)
        self.pasta_base.mkdir(parents=True, exist_ok=True)
    
    def obter_proximo_id(self) -> str:
        """Obtém o próximo ID sequencial baseado nas pastas existentes"""
        ids_existentes = []
        
        for item in self.pasta_base.iterdir():
            if item.is_dir() and item.name.isdigit():
                try:
                    ids_existentes.append(int(item.name))
                except ValueError:
                    continue
        
        proximo_id = max(ids_existentes) + 1 if ids_existentes else 1
        return str(proximo_id)
    
    def criar_pasta_video(self, video_id: str = None) -> Path:
        """Cria pasta para o vídeo com ID específico ou próximo disponível"""
        if not video_id:
            video_id = self.obter_proximo_id()
        
        pasta_video = self.pasta_base / video_id
        pasta_video.mkdir(parents=True, exist_ok=True)
        return pasta_video
    
    def salvar_arquivos_video(self, dados: Dict, pasta_video: Path) -> Tuple[Path, Path]:
        """Salva arquivos JSON e TXT do vídeo"""
        video_id = pasta_video.name
        
        # Salva JSON com metadados
        caminho_json = pasta_video / f"{video_id}.json"
        with open(caminho_json, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        return caminho_json
    
    def salvar_video_completo(self, dados: Dict, canal_nome: str, config: Dict) -> Dict:
        """
        Salva vídeo completo: pasta, arquivos e banco de dados
        
        Returns:
            Dict com informações do vídeo salvo
        """
        from crud import DatabaseManager
        
        # Cria pasta do vídeo
        pasta_video = self.criar_pasta_video()
        video_id = pasta_video.name
        
        # Atualiza dados com ID do vídeo
        dados['id_video'] = video_id
        dados['canal'] = canal_nome
        dados['data_criacao'] = datetime.now().isoformat()
        
        # Salva arquivos
        caminho_json = self.salvar_arquivos_video(dados, pasta_video)
        
        # Salva no banco de dados
        resultado_db = self._salvar_no_banco(dados, config, canal_nome)
        
        return {
            'id_video': video_id,
            'pasta_video': pasta_video,
            'arquivo_json': caminho_json,            
            'dados': dados,
            'db_result': resultado_db
        }
            
    # No video_manager.py, ajuste o método _salvar_no_banco:
    def _salvar_no_banco(self, dados: dict, config: dict, canal_nome: str) -> dict:
        """Salva roteiro no banco de dados"""
        try:
            from crud.manager import DatabaseManager
            db = DatabaseManager()
            
            # Busca ou cria o canal
            canal = db.buscar_canal_por_nome(canal_nome)
            if not canal:
                canal = db.criar_canal(nome=canal_nome, config_path=str(config['PASTA_CANAL']))
            
            # Prepara dados para o roteiro
            roteiro_data = {
                'id_video': dados['id_video'],
                'titulo_a': dados.get('titulo') or "Título temporário",
                'titulo_b': dados.get('titulo_b') or "",
                'titulo_escolhido': dados.get('titulo_escolhido') or "",
                'texto': dados.get('texto') or "",
                'descricao': dados.get('descricao') or "",
                'tags': ', '.join(dados.get('tags', [])),
                'thumb_a': dados.get('thumb') or "thumb_temporaria",
                'thumb_b': dados.get('thumb_b') or "",
                'thumb_escolhida': dados.get('thumb_escolhida') or "",
                'canal_id': canal.id,
                'vertical': True
            }
            
            roteiro_db = db.criar_roteiro(**roteiro_data)
            return {'sucesso': True, 'id_banco': roteiro_db.id}
            
        except Exception as e:
            print(f"❌ Erro ao salvar no banco: {e}")
            return {'sucesso': False, 'erro': str(e)}
            
    def listar_videos(self, limite: int = 10) -> list:
        """Lista os vídeos mais recentes"""
        pastas = []
        for item in self.pasta_base.iterdir():
            if item.is_dir() and item.name.isdigit():
                pastas.append(item)
        
        # Ordena por ID (numérico) e pega os mais recentes
        pastas.sort(key=lambda x: int(x.name), reverse=True)
        return pastas[:limite]
    
    def buscar_video_por_id(self, video_id: str) -> Optional[Dict]:
        """Busca vídeo por ID"""
        pasta_video = self.pasta_base / video_id
        if not pasta_video.exists():
            return None
        
        arquivo_json = pasta_video / f"{video_id}.json"
        if not arquivo_json.exists():
            return None
        
        try:
            with open(arquivo_json, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            return {
                'id_video': video_id,
                'pasta_video': pasta_video,
                'dados': dados
            }
        except Exception:
            return None