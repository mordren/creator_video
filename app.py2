# app.py - VERSÃO CORRIGIDA (robustez de filtros, mapeamento de canais, compatibilidade video_id/roteiro_id)
from flask import Flask, render_template, request, jsonify, url_for, redirect
from pathlib import Path
import sys
import json
import os
from datetime import datetime

# Adiciona o diretório atual ao path para imports
sys.path.append(str(Path(__file__).parent))

# Importações do sistema
from crud.manager import DatabaseManager
from crud.connection import test_connection, criar_tabelas
from tasks import generate_audio_task, generate_video_task, upload_youtube_task, check_task_status

app = Flask(__name__)

app.config.update(
    CELERY_BROKER_URL=os.getenv('CELERY_BROKER_URL', 'redis://192.168.31.200:6379/0'),
    CELERY_RESULT_BACKEND=os.getenv('CELERY_RESULT_BACKEND', 'redis://192.168.31.200:6379/0'),
    DEBUG=True,
    TEMPLATES_AUTO_RELOAD=True,
    SEND_FILE_MAX_AGE_DEFAULT=300,
)

# Inicializa o gerenciador de banco
db = DatabaseManager()

def get_payload():
    """Aceita JSON (mesmo sem Content-Type) ou form-data."""
    data = request.get_json(silent=True)
    if isinstance(data, dict):
        return data
    return request.form.to_dict(flat=True)

def to_bool(value):
    """Converte valor para booleano de forma segura"""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in ('true', '1', 'on', 'yes', 'sim')

# ========== ROTAS DE PÁGINAS ==========

@app.route('/')
def index():
    return redirect(url_for('list_videos'))

@app.route('/videos')
def list_videos():
    """Página principal com lista de vídeos"""
    try:
        # Parâmetros de filtro
        filter_type = request.args.get('filter', 'all')
        search = request.args.get('search', '') or ''
        selected_channel = request.args.get('channel', 'all')
        tipo_filter = request.args.get('tipo', 'all')

        # Buscar dados
        channels = db.canais.listar(apenas_ativos=True)
        roteiros = db.roteiros.listar()

        # Mapa id->canal para uso no template
        canais_por_id = {c.id: c for c in (channels or [])}

        # Aplicar filtros
        videos_filtrados = []
        for roteiro in roteiros or []:
            # Filtro por canal
            if selected_channel != 'all':
                try:
                    if int(selected_channel) != int(getattr(roteiro, 'canal_id', -1)):
                        continue
                except ValueError:
                    pass

            # Filtro por tipo (deduzido por resolução)
            res = (getattr(roteiro, 'resolucao', '') or '').lower()
            if tipo_filter != 'all':
                if tipo_filter == 'short' and res != '720x1280':
                    continue
                elif tipo_filter == 'long' and res != '1280x720':
                    continue
                elif tipo_filter == 'reel' and res != 'vertical':
                    continue

            # Filtro por status
            audio_ok = bool(getattr(roteiro, 'audio_gerado', False))
            video_ok = bool(getattr(roteiro, 'video_gerado', False))
            fin_ok = bool(getattr(roteiro, 'finalizado', False))

            if filter_type == 'audio' and not audio_ok:
                continue
            elif filter_type == 'video' and not video_ok:
                continue
            elif filter_type == 'finalized' and not fin_ok:
                continue

            # Filtro por busca (titulo/descricao/tags)
            if search:
                s = search.lower()
                titulo = (getattr(roteiro, 'titulo', '') or '').lower()
                descricao = (getattr(roteiro, 'descricao', '') or '').lower()
                tags = (getattr(roteiro, 'tags', '') or '').lower()
                if s not in titulo and s not in descricao and s not in tags:
                    continue

            videos_filtrados.append(roteiro)

        # Calcular estatísticas
        stats = {
            'total': len(videos_filtrados),
            'com_audio': sum(1 for v in videos_filtrados if getattr(v, 'audio_gerado', False)),
            'com_video': sum(1 for v in videos_filtrados if getattr(v, 'video_gerado', False)),
            'finalizados': sum(1 for v in videos_filtrados if getattr(v, 'finalizado', False)),
        }

        # request_args para manter filtros na paginação (se existir paginação no seu render)
        request_args = {k: v for k, v in request.args.items()}

        return render_template(
            'videos.html',
            videos=videos_filtrados,
            stats=stats,
            filter_type=filter_type,
            search=search,
            selected_channel=selected_channel,
            tipo_filter=tipo_filter,
            channels=channels,
            canais_por_id=canais_por_id,
            request_args=request_args,
        )

    except Exception as e:
        print(f"❌ Erro na rota list_videos: {e}")
        return render_template(
            'videos.html',
            videos=[],
            stats={'total': 0, 'com_audio': 0, 'com_video': 0, 'finalizados': 0},
            filter_type='all',
            search='',
            selected_channel='all',
            tipo_filter='all',
            channels=[],
            canais_por_id={},
            request_args={},
        )

@app.route('/video/<int:roteiro_id>/edit')
def video_edit(roteiro_id):
    """Página de edição do vídeo"""
    try:
        roteiro = db.roteiros.buscar_por_id(roteiro_id)
        if not roteiro:
            return "Vídeo não encontrado", 404

        video_info = db.videos.buscar_por_roteiro_id(roteiro_id)
        return render_template('video_edit.html', roteiro=roteiro, video_info=video_info)

    except Exception as e:
        print(f"❌ Erro na rota video_edit: {e}")
        return "Erro ao carregar página", 500

@app.route('/video/<int:roteiro_id>/scheduling')
def video_scheduling(roteiro_id):
    """Página de agendamento do vídeo"""
    try:
        roteiro = db.roteiros.buscar_por_id(roteiro_id)
        if not roteiro:
            return "Vídeo não encontrado", 404

        return render_template('video_scheduling.html', video=roteiro)
    except Exception as e:
        print(f"❌ Erro na rota video_scheduling: {e}")
        return "Erro ao carregar página", 500

@app.route('/video/<int:roteiro_id>/uploads')
def video_uploads(roteiro_id):
    """Página de uploads do vídeo"""
    try:
        roteiro = db.roteiros.buscar_por_id(roteiro_id)
        if not roteiro:
            return "Vídeo não encontrado", 404

        # Buscar informações completas
        video_info = db.videos.buscar_por_roteiro_id(roteiro_id)
        youtube_info = None

        if video_info:
            youtube_info = db.youtube.buscar_por_video_id(video_info.id)

        return render_template(
            'video_manager.html',
            video=roteiro,
            video_info=video_info,
            youtube_info=youtube_info,
        )

    except Exception as e:
        print(f"❌ Erro na rota video_uploads: {e}")
        return "Erro ao carregar página", 500

@app.route('/novo-roteiro')
def novo_roteiro():
    """Página para criar novo roteiro"""
    canais = db.canais.listar()
    return render_template('novo_roteiro.html', canais=canais)

# ========== API ENDPOINTS ==========

@app.route('/api/status')
def api_status():
    """Status do sistema"""
    db_status = test_connection()
    return jsonify({
        'database': 'connected' if db_status else 'disconnected',
        'timestamp': datetime.now().isoformat()
    })

# --- GESTÃO DE VÍDEOS ---

@app.route('/api/videos/<int:roteiro_id>')
def api_video_detail(roteiro_id):
    """Detalhes de um vídeo"""
    roteiro = db.roteiros.buscar_por_id(roteiro_id)
    if not roteiro:
        return jsonify({'error': 'Vídeo não encontrado'}), 404

    video_info = db.videos.buscar_por_roteiro_id(roteiro_id)
    return jsonify({
        'roteiro': roteiro.dict() if hasattr(roteiro, "dict") else roteiro.__dict__,
        'video_info': (video_info.dict() if hasattr(video_info, "dict") else video_info.__dict__) if video_info else None
    })

@app.route('/api/videos/<int:roteiro_id>/update', methods=['POST'])
def api_update_video(roteiro_id):
    """Atualizar vídeo"""
    try:
        data = get_payload()

        campos_permitidos = [
            'titulo', 'descricao', 'tags', 'texto', 'thumb',
            'resolucao', 'audio_gerado', 'video_gerado', 'finalizado'
        ]

        atualizacao = {}
        for campo in campos_permitidos:
            if campo in data:
                if campo in ('audio_gerado', 'video_gerado', 'finalizado'):
                    atualizacao[campo] = to_bool(data[campo])
                else:
                    atualizacao[campo] = data[campo]

        success = db.roteiros.atualizar(roteiro_id, **atualizacao)

        if success:
            return jsonify({'status': 'success', 'message': 'Vídeo atualizado com sucesso!'})
        else:
            return jsonify({'status': 'error', 'message': 'Falha ao atualizar vídeo'}), 500

    except Exception as e:
        print(f"❌ Erro ao atualizar vídeo: {e}")
        return jsonify({'status': 'error', 'message': f'Erro: {str(e)}'}), 500

@app.route('/api/videos/<int:roteiro_id>/delete', methods=['DELETE'])
def api_delete_video(roteiro_id):
    """Excluir vídeo"""
    try:
        success = db.roteiros.deletar(roteiro_id)

        if success:
            return jsonify({'status': 'success', 'message': 'Vídeo excluído com sucesso!'})
        else:
            return jsonify({'status': 'error', 'message': 'Falha ao excluir vídeo'}), 500

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Erro: {str(e)}'}), 500

# --- TAREFAS ASSÍNCRONAS ---

@app.route('/api/videos/<int:roteiro_id>/generate-audio', methods=['POST'])
def api_generate_audio(roteiro_id):
    """Gerar áudio de forma assíncrona"""
    try:
        task = generate_audio_task.delay(roteiro_id)
        return jsonify({
            'status': 'success',
            'message': 'Geração de áudio iniciada!',
            'task_id': task.id
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/videos/<int:roteiro_id>/generate-video', methods=['POST'])
def api_generate_video(roteiro_id):
    """Gerar vídeo de forma assíncrona"""
    try:
        task = generate_video_task.delay(roteiro_id)
        return jsonify({
            'status': 'success',
            'message': 'Geração de vídeo iniciada!',
            'task_id': task.id
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/videos/<int:roteiro_id>/upload-youtube', methods=['POST'])
def api_upload_youtube(roteiro_id):
    """Upload para YouTube de forma assíncrona"""
    try:
        data = get_payload() or {}
        publicar_imediato = data.get('publicar_imediato', False)

        task = upload_youtube_task.delay(roteiro_id, publicar_imediato)
        return jsonify({
            'status': 'success',
            'message': 'Upload para YouTube iniciado!',
            'task_id': task.id
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/tasks/<string:task_id>/status')
def api_task_status(task_id):
    """Status de uma tarefa"""
    try:
        result = check_task_status.delay(task_id)
        task_info = result.get(timeout=5)
        return jsonify(task_info)
    except Exception as e:
        return jsonify({'state': 'ERROR', 'status': str(e)}), 500

# --- GERAR ROTEIRO ---

@app.route('/api/gerar-roteiro', methods=['POST'])
def api_gerar_roteiro():
    """Gerar novo roteiro"""
    try:
        from texto import TextGenerator
        from read_config import carregar_config_canal

        data = get_payload()
        canal_nome = data.get('canal')
        linha_tema = data.get('tema', '').strip()
        tipo_video = data.get('tipo_video', 'short')
        provider = data.get('provider')
        duracao = data.get('duracao')

        if not canal_nome:
            return jsonify({'status': 'error', 'message': 'Canal é obrigatório'}), 400

        # Buscar canal
        canal = db.canais.buscar_por_nome(canal_nome)
        if not canal:
            return jsonify({'status': 'error', 'message': f'Canal não encontrado: {canal_nome}'}), 404

        # Carregar configuração
        config = carregar_config_canal(f"{canal.config_path}/config.py")

        # Gerar roteiro
        generator = TextGenerator()
        roteiro = generator.gerar_roteiro(canal.config_path, linha_tema, provider, tipo_video, duracao)

        if not roteiro:
            return jsonify({'status': 'error', 'message': 'Falha na geração do roteiro'}), 500

        # Salvar roteiro
        resultado = generator.salvar_roteiro_completo(roteiro, config, tipo_video)

        if resultado['db_result'].get('sucesso'):
            return jsonify({
                'status': 'success',
                'message': 'Roteiro gerado e salvo!',
                'roteiro': {
                    'id': resultado['db_result'].get('id_banco'),
                    'id_video': resultado['id_roteiro'],
                    'titulo': roteiro.get('titulo'),
                    'descricao': roteiro.get('descricao'),
                    'tipo_video': tipo_video,
                    'resolucao': roteiro.get('resolucao')
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f"Erro ao salvar: {resultado['db_result'].get('erro')}"
            }), 500

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- CANAIS E TEMAS ---

@app.route('/api/canais/<string:canal_nome>/config')
def api_config_canal(canal_nome):
    """Configurações de um canal"""
    try:
        canal = db.canais.buscar_por_nome(canal_nome)
        if not canal:
            return jsonify({'erro': f'Canal não encontrado: {canal_nome}'})

        from read_config import carregar_config
        config = carregar_config(canal.config_path)

        return jsonify({
            'canal': canal_nome,
            'config': {
                'TAMANHO_MAX_SHORT': config.get('TAMANHO_MAX_SHORT', 130),
                'TAMANHO_MAX_LONG': config.get('TAMANHO_MAX_LONG', 130),
                'DURACAO_MIN_SHORT': config.get('DURACAO_MIN_SHORT', 1),
                'DURACAO_MIN_LONG': config.get('DURACAO_MIN_LONG', 3),
                'RESOLUCAO_SHORT': config.get('RESOLUCAO_SHORT', '720x1280'),
                'RESOLUCAO_LONG': config.get('RESOLUCAO_LONG', '1280x720')
            }
        })
    except Exception as e:
        return jsonify({'erro': str(e)})

@app.route('/api/canais/<string:canal_nome>/temas')
def api_temas_canal(canal_nome):
    """Temas disponíveis de um canal"""
    try:
        canal = db.canais.buscar_por_nome(canal_nome)
        if not canal:
            return jsonify({'temas': [], 'erro': f'Canal não encontrado: {canal_nome}'})

        pasta_canal = Path(canal.config_path)
        if not pasta_canal.exists():
            return jsonify({'temas': [], 'erro': f'Pasta não existe: {pasta_canal}'})

        # Buscar arquivo de temas
        temas_file = None
        for nome in ['temas.txt', 'topicos.txt', 'assuntos.txt']:
            caminho = pasta_canal / nome
            if caminho.exists():
                temas_file = caminho
                break

        if not temas_file:
            return jsonify({'temas': [], 'erro': 'Arquivo de temas não encontrado'})

        # Ler temas
        with open(temas_file, 'r', encoding='utf-8') as f:
            temas = [tema.strip() for tema in f.read().strip().split('\n') if tema.strip()]

        return jsonify({'temas': temas, 'arquivo': str(temas_file)})

    except Exception as e:
        return jsonify({'temas': [], 'erro': str(e)})

# --- YOUTUBE ---

@app.route('/api/youtube/create', methods=['POST'])
def api_youtube_create():
    """
    Criar registro no YouTube.
    Aceita tanto 'roteiro_id' (preferido) quanto 'video_id' (retrocompatibilidade).
    """
    try:
        data = get_payload() or {}

        roteiro_id = data.get('roteiro_id')
        video_id_in = data.get('video_id')  # retrocompat

        if not data.get('link'):
            return jsonify({'status': 'error', 'message': 'link é obrigatório'}), 400

        # Normaliza origem da chave: preferir roteiro_id; aceitar video_id como fallback
        video = None
        if roteiro_id:
            video = db.videos.buscar_por_roteiro_id(roteiro_id)
        elif video_id_in:
            # Tenta buscar pelo ID do objeto de vídeo (se houver método); caso contrário,
            # considere que o sistema usa "roteiro_id" como id principal do vídeo.
            if hasattr(db.videos, 'buscar_por_id'):
                video = db.videos.buscar_por_id(video_id_in)
            else:
                # Último recurso: tratar video_id como se fosse o próprio roteiro_id
                video = db.videos.buscar_por_roteiro_id(video_id_in)

        if not video:
            return jsonify({'status': 'error', 'message': 'Vídeo não encontrado'}), 404

        # Processar datas
        def parse_dt(s):
            if not s:
                return None
            try:
                return datetime.fromisoformat(s.replace('Z', '+00:00'))
            except ValueError:
                return None

        hora_upload = parse_dt(data.get('hora_upload'))
        hora_estreia = parse_dt(data.get('hora_estreia'))

        # Criar registro
        from crud.models import VideoYouTube
        youtube_info = VideoYouTube(
            video_id=video.id,
            link=data['link'],
            hora_upload=hora_upload,
            hora_estreia=hora_estreia,
            visualizacoes=int(data.get('visualizacoes', 0) or 0),
            likes=int(data.get('likes', 0) or 0),
            comentarios=int(data.get('comentarios', 0) or 0),
            tipo_conteudo=data.get('tipo_conteudo', 'long')
        )

        youtube_created = db.youtube.criar(youtube_info)

        if youtube_created:
            return jsonify({
                'status': 'success',
                'message': 'Registro do YouTube criado!',
                'youtube_id': youtube_created.id
            })
        else:
            return jsonify({'status': 'error', 'message': 'Falha ao criar registro'}), 500

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/videos/<int:roteiro_id>/youtube-info')
def api_youtube_info(roteiro_id):
    """Informações do YouTube de um vídeo"""
    try:
        video = db.videos.buscar_por_roteiro_id(roteiro_id)
        if not video:
            return jsonify({'youtube_info': None})

        youtube_info = db.youtube.buscar_por_video_id(video.id)
        if not youtube_info:
            return jsonify({'youtube_info': None})

        return jsonify({
            'youtube_info': {
                'id': youtube_info.id,
                'link': youtube_info.link,
                'hora_upload': youtube_info.hora_upload.isoformat() if youtube_info.hora_upload else None,
                'hora_estreia': youtube_info.hora_estreia.isoformat() if youtube_info.hora_estreia else None,
                'visualizacoes': youtube_info.visualizacoes,
                'likes': youtube_info.likes,
                'comentarios': youtube_info.comentarios,
                'tipo_conteudo': youtube_info.tipo_conteudo
            }
        })
    except Exception as e:
        return jsonify({'youtube_info': None})

@app.route('/api/youtube/<int:youtube_id>/update', methods=['PUT'])
def api_youtube_update(youtube_id):
    """Atualizar registro do YouTube"""
    try:
        data = get_payload() or {}

        campos_permitidos = [
            'link', 'hora_upload', 'hora_estreia',
            'visualizacoes', 'likes', 'comentarios', 'tipo_conteudo'
        ]

        atualizacao = {}
        for campo in campos_permitidos:
            if campo in data:
                if campo in ['hora_upload', 'hora_estreia'] and data[campo]:
                    try:
                        atualizacao[campo] = datetime.fromisoformat(str(data[campo]).replace('Z', '+00:00'))
                    except ValueError:
                        pass
                else:
                    atualizacao[campo] = data[campo]

        success = db.youtube.atualizar_campos(youtube_id, **atualizacao)

        if success:
            return jsonify({'status': 'success', 'message': 'Registro atualizado!'})
        else:
            return jsonify({'status': 'error', 'message': 'Registro não encontrado'}), 404

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/youtube/<int:youtube_id>/delete', methods=['DELETE'])
def api_youtube_delete(youtube_id):
    """Excluir registro do YouTube"""
    try:
        success = db.youtube.deletar(youtube_id)

        if success:
            return jsonify({'status': 'success', 'message': 'Registro excluído!'})
        else:
            return jsonify({'status': 'error', 'message': 'Registro não encontrado'}), 404

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- AGENDAMENTOS ---

@app.route('/api/videos/<int:roteiro_id>/agendamentos')
def api_video_agendamentos(roteiro_id):
    """Agendamentos de um vídeo (roteiro_id como chave do vídeo no sistema)."""
    try:
        agendamentos = db.agendamentos.buscar_por_video_id(roteiro_id)

        agendamentos_formatados = []
        for ag in agendamentos or []:
            agendamentos_formatados.append({
                'id': ag.id,
                'video_id': ag.video_id,
                'plataformas': json.loads(ag.plataformas) if isinstance(ag.plataformas, str) else (ag.plataformas or []),
                'data_publicacao': ag.data_publicacao,
                'hora_publicacao': ag.hora_publicacao,
                'recorrente': ag.recorrente,
                'status': ag.status
            })

        return jsonify(agendamentos_formatados)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agendamentos', methods=['POST'])
def api_criar_agendamento():
    """Criar agendamento"""
    try:
        data = get_payload() or {}

        required_fields = ['video_id', 'plataformas', 'data_publicacao', 'hora_publicacao']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'message': f'Campo obrigatório: {field}'}), 400

        # Verificar se vídeo existe (no sistema, video_id == roteiro_id)
        video = db.roteiros.buscar_por_id(data['video_id'])
        if not video:
            return jsonify({'status': 'error', 'message': 'Vídeo não encontrado'}), 404

        # Criar agendamento
        from crud.models import Agendamento
        agendamento = Agendamento(
            video_id=data['video_id'],
            plataformas=json.dumps(data['plataformas']) if not isinstance(data['plataformas'], str) else data['plataformas'],
            data_publicacao=data['data_publicacao'],
            hora_publicacao=data['hora_publicacao'],
            recorrente=to_bool(data.get('recorrente', False))
        )

        agendamento_criado = db.agendamentos.criar(agendamento)

        return jsonify({
            'status': 'success',
            'message': 'Agendamento criado!',
            'agendamento_id': agendamento_criado.id
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/agendamentos/<int:agendamento_id>', methods=['DELETE'])
def api_deletar_agendamento(agendamento_id):
    """Excluir agendamento"""
    try:
        success = db.agendamentos.deletar(agendamento_id)

        if success:
            return jsonify({'status': 'success', 'message': 'Agendamento excluído!'})
        else:
            return jsonify({'status': 'error', 'message': 'Agendamento não encontrado'}), 404

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ========== CONTEXT PROCESSOR ==========

@app.context_processor
def utility_processor():
    def remove_filter_url(filter_name):
        args = request.args.copy()
        args.pop(filter_name, None)
        return url_for('list_videos', **args)
    return dict(remove_filter_url=remove_filter_url)

# ========== INICIALIZAÇÃO ==========

if __name__ == '__main__':
    print("🔧 Inicializando servidor Flask...")

    if test_connection():
        criar_tabelas()
        print("✅ Banco de dados conectado e pronto!")
    else:
        print("❌ Problema com o banco de dados")

    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
