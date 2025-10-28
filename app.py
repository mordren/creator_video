# app.py
from flask import Flask, render_template, request, jsonify, send_file
import sys
from pathlib import Path
import json
from datetime import datetime
from read_config import carregar_config_canal

# Adiciona o diretório atual ao path para imports
sys.path.append(str(Path(__file__).parent))

app = Flask(__name__)

# Importações do sistema existente
try:
    from crud.manager import DatabaseManager
    from audio import AudioSystem
    from video import VideoGenerator
    from texto import TextGenerator
    from crud.connection import test_connection, criar_tabelas
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    raise

# Inicializa o gerenciador de banco
db = DatabaseManager()

@app.route('/')
def index():
    """Página inicial do sistema"""
    return render_template('index.html')

@app.route('/videos')
def list_videos():
    """Lista todos os vídeos com filtros"""
    # Parâmetros de filtro
    filter_type = request.args.get('filter', 'all')
    search = request.args.get('search', '')
    
    # Buscar vídeos
    videos = get_videos_with_filters(filter_type, search)
    
    # Estatísticas
    stats = {
        'total': len(videos),
        'com_audio': sum(1 for v in videos if v['audio_gerado']),
        'com_video': sum(1 for v in videos if v['video_gerado']),
        'finalizados': sum(1 for v in videos if v['finalizado'])
    }
    
    return render_template('videos.html', 
                         videos=videos, 
                         filter_type=filter_type,
                         search=search,
                         stats=stats)

@app.route('/videos/<int:video_id>')
def video_detail(video_id):
    """Detalhes de um vídeo específico"""
    video = get_video_by_id(video_id)
    if not video:
        return "Vídeo não encontrado", 404
    
    return render_template('video_detail.html', video=video)

# API Endpoints
@app.route('/api/videos')
def api_list_videos():
    """API para listar vídeos (JSON)"""
    filter_type = request.args.get('filter', 'all')
    search = request.args.get('search', '')
    
    videos = get_videos_with_filters(filter_type, search)
    return jsonify(videos)

@app.route('/api/videos/<int:video_id>')
def api_video_detail(video_id):
    """API para detalhes de um vídeo"""
    video = get_video_by_id(video_id)
    if not video:
        return jsonify({'error': 'Vídeo não encontrado'}), 404
    
    return jsonify(video)

@app.route('/api/videos/<int:video_id>/generate-audio', methods=['POST'])
def api_generate_audio(video_id):
    """API para gerar áudio"""
    try:
        audio_system = AudioSystem()
        success = audio_system.generate_audio(video_id)
        
        if success:
            return jsonify({
                'status': 'success', 
                'message': 'Áudio gerado com sucesso!'
            })
        else:
            return jsonify({
                'status': 'error', 
                'message': 'Falha ao gerar áudio'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': f'Erro: {str(e)}'
        }), 500

@app.route('/api/videos/<int:video_id>/generate-video', methods=['POST'])
def api_generate_video(video_id):
    """API para gerar vídeo"""
    try:
        video_gen = VideoGenerator()
        success = video_gen.gerar_video(video_id)
        
        if success:
            return jsonify({
                'status': 'success', 
                'message': 'Vídeo gerado com sucesso!'
            })
        else:
            return jsonify({
                'status': 'error', 
                'message': 'Falha ao gerar vídeo'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': f'Erro: {str(e)}'
        }), 500

@app.route('/api/videos/<int:video_id>/delete', methods=['DELETE'])
def api_delete_video(video_id):
    """API para excluir vídeo"""
    try:
        success = db.roteiros.deletar(video_id)
        
        if success:
            return jsonify({
                'status': 'success', 
                'message': 'Vídeo excluído com sucesso!'
            })
        else:
            return jsonify({
                'status': 'error', 
                'message': 'Falha ao excluir vídeo'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': f'Erro: {str(e)}'
        }), 500

@app.route('/api/status')
def api_status():
    """Status do sistema e banco"""
    db_status = test_connection()
    return jsonify({
        'database': 'connected' if db_status else 'disconnected',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/novo-roteiro')
def novo_roteiro():
    """Página para criar novo roteiro"""
    # Carrega lista de canais disponíveis
    canais = db.canais.listar()
    return render_template('novo_roteiro.html', canais=canais)

@app.route('/api/gerar-roteiro', methods=['POST'])
def api_gerar_roteiro():
    """API para gerar novo roteiro - VERSÃO COM DURAÇÃO PERSONALIZADA"""
    try:
        data = request.get_json()
        
        canal_nome = data.get('canal')
        linha_tema = data.get('tema', '').strip()
        tipo_video = data.get('tipo_video', 'short')
        provider = data.get('provider')
        duracao = data.get('duracao')  # ✅ NOVO: Duração personalizada em minutos
        
        if not canal_nome:
            return jsonify({
                'status': 'error', 
                'message': 'Canal é obrigatório'
            }), 400
        
        # Busca o canal no banco
        canal = db.canais.buscar_por_nome(canal_nome)
        if not canal:
            return jsonify({
                'status': 'error', 
                'message': f'Canal "{canal_nome}" não encontrado no banco de dados'
            }), 404
        
        print(f"🎯 Gerando roteiro para canal: {canal_nome}")
        print(f"📁 Config path do canal: {canal.config_path}")
        if duracao:
            print(f"⏱️ Duração personalizada: {duracao} minutos")
        
        # Carrega configuração
        try:            
            config = carregar_config_canal(canal.config_path+"/config.py")
            print(f"✅ Configuração carregada de: {canal.config_path}")
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Erro ao carregar configuração do canal: {str(e)}'
            }), 500
        
        # Gera o roteiro - ✅ ATUALIZADO: passa duração personalizada
        generator = TextGenerator()
        roteiro = generator.gerar_roteiro(canal.config_path, linha_tema, provider, tipo_video, duracao)
        
        if not roteiro:
            return jsonify({
                'status': 'error', 
                'message': 'Falha na geração do roteiro'
            }), 500
        
        # Salva o roteiro
        resultado_salvo = generator.salvar_roteiro_completo(roteiro, config, tipo_video)
        
        if resultado_salvo['db_result'].get('sucesso'):
            return jsonify({
                'status': 'success',
                'message': 'Roteiro gerado e salvo com sucesso!',
                'roteiro': {
                    'id': resultado_salvo['db_result'].get('id_banco'),
                    'id_video': resultado_salvo['id_roteiro'],
                    'titulo': roteiro.get('titulo'),
                    'descricao': roteiro.get('descricao'),
                    'tipo_video': tipo_video,
                    'resolucao': roteiro.get('resolucao'),
                    'palavras_geradas': roteiro.get('palavras_geradas'),  # ✅ NOVO
                    'duracao_estimada': roteiro.get('duracao_estimada_minutos')  # ✅ NOVO
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f"Erro ao salvar no banco: {resultado_salvo['db_result'].get('erro')}"
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': f'Erro na geração: {str(e)}'
        }), 500

    
@app.route('/api/canais/<string:canal_nome>/config')
def api_config_canal(canal_nome):
    """API para obter configurações de um canal"""
    try:
        canal = db.canais.buscar_por_nome(canal_nome)
        if not canal:
            return jsonify({'erro': f'Canal "{canal_nome}" não encontrado'})
        
        # Carrega configuração do canal
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
    """API para obter temas disponíveis de um canal - VERSÃO CORRIGIDA"""
    try:
        print(f"🔍 Buscando temas para o canal: {canal_nome}")
        
        # ✅ CORREÇÃO: Busca o canal no banco para obter o config_path
        canal = db.canais.buscar_por_nome(canal_nome)
        if not canal:
            return jsonify({
                'temas': [], 
                'erro': f'Canal "{canal_nome}" não encontrado no banco de dados'
            })
        
        # ✅ CORREÇÃO: Usa o config_path do banco em vez de carregar_config_canal
        pasta_canal = Path(canal.config_path)
        print(f"📁 Usando pasta do canal do banco: {pasta_canal}")
        
        if not pasta_canal.exists():
            return jsonify({
                'temas': [], 
                'erro': f'Pasta do canal não existe: {pasta_canal}'
            })
        
        # ✅ CORREÇÃO: Busca arquivo de temas
        temas_file = None
        possiveis_nomes = ['temas.txt', 'topicos.txt', 'assuntos.txt']
        
        for nome_arquivo in possiveis_nomes:
            caminho_teste = pasta_canal / nome_arquivo
            print(f"📁 Testando: {caminho_teste}")
            if caminho_teste.exists():
                temas_file = caminho_teste
                break
        
        if not temas_file:
            print(f"❌ Nenhum arquivo de temas encontrado em: {pasta_canal}")
            # Tenta criar um arquivo de temas padrão
            temas_file = pasta_canal / 'temas.txt'
            try:
                # Temas padrão para canal de terror
                temas_exemplo = [
                    "Assombração, Casa Mal-assombrada",
                    "Lendas Urbanas, O Homem do Saco",
                    "Criaturas, Lobisomem na Floresta", 
                    "Psicológico, Medo do Escuro",
                    "Sobrenatural, Espíritos Vingativos",
                    "Suspense, O Barulho no Sótão",
                    "Terror, Pesadelos Noturnos",
                    "Mistério, Desaparecimentos Estranhos"
                ]
                temas_file.write_text('\n'.join(temas_exemplo), encoding='utf-8')
                print(f"✅ Arquivo de temas criado: {temas_file}")
            except Exception as e:
                print(f"⚠️ Não foi possível criar arquivo de temas: {e}")
                return jsonify({'temas': [], 'erro': 'Arquivo de temas não encontrado'})
        
        print(f"✅ Usando arquivo de temas: {temas_file}")
        
        # Lê os temas
        with open(temas_file, 'r', encoding='utf-8') as f:
            conteudo = f.read().strip()
        
        if not conteudo:
            print("⚠️ Arquivo de temas está vazio")
            return jsonify({'temas': [], 'aviso': 'Arquivo de temas vazio'})
        
        temas = [tema.strip() for tema in conteudo.split('\n') if tema.strip()]
        print(f"📚 Encontrados {len(temas)} temas")
        
        return jsonify({
            'temas': temas,
            'arquivo': str(temas_file),
            'pasta_canal': str(pasta_canal)
        })
            
    except Exception as e:
        print(f"❌ Erro ao carregar temas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'temas': [], 
            'erro': f'Erro ao carregar temas: {str(e)}'
        })
    

@app.route('/api/videos/<int:video_id>/agendamentos')
def api_video_agendamentos(video_id):
    """API para obter agendamentos de um vídeo"""
    try:
        # Buscar agendamentos do vídeo (implementar conforme seu modelo)
        agendamentos = []  # Substituir pela busca real no banco
        
        return jsonify(agendamentos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agendamentos', methods=['POST'])
def api_criar_agendamento():
    """API para criar novo agendamento"""
    try:
        data = request.get_json()
        
        # Validar dados
        required_fields = ['video_id', 'plataformas', 'data_publicacao', 'hora_publicacao']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'message': f'Campo obrigatório faltando: {field}'}), 400
        
        # Criar agendamento no banco (implementar conforme seu modelo)
        # agendamento = criar_agendamento_no_banco(data)
        
        return jsonify({
            'status': 'success', 
            'message': 'Agendamento criado com sucesso!',
            'agendamento_id': 1  # Substituir pelo ID real
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/agendamentos/<int:agendamento_id>', methods=['GET', 'PUT', 'DELETE'])
def api_gerenciar_agendamento(agendamento_id):
    """API para gerenciar agendamento específico"""
    try:
        if request.method == 'GET':
            # Buscar agendamento
            agendamento = {}  # Substituir pela busca real
            return jsonify(agendamento)
            
        elif request.method == 'PUT':
            # Atualizar agendamento
            data = request.get_json()
            # atualizar_agendamento_no_banco(agendamento_id, data)
            return jsonify({'status': 'success', 'message': 'Agendamento atualizado!'})
            
        elif request.method == 'DELETE':
            # Excluir agendamento
            # excluir_agendamento_no_banco(agendamento_id)
            return jsonify({'status': 'success', 'message': 'Agendamento excluído!'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/videos/<int:video_id>/agendamentos', methods=['DELETE'])
def api_cancelar_todos_agendamentos(video_id):
    """API para cancelar todos os agendamentos de um vídeo"""
    try:
        # cancelar_agendamentos_video(video_id)
        return jsonify({'status': 'success', 'message': 'Todos os agendamentos foram cancelados!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Funções auxiliares
def get_videos_with_filters(filter_type='all', search=''):
    """Busca vídeos com filtros aplicados - VERSÃO CORRIGIDA"""
    try:
        roteiros = db.roteiros.listar()
        videos = []
        
        for roteiro in roteiros:
            canal = db.canais.buscar_por_id(roteiro.canal_id)
            video_info = db.videos.buscar_por_roteiro_id(roteiro.id)
            
            # ✅ CORREÇÃO: Verifica se o canal existe
            if not canal:
                canal_nome = "Canal Não Encontrado"
                print(f"⚠️ Canal não encontrado para roteiro {roteiro.id}")
            else:
                canal_nome = canal.nome
            
            video_data = {
                'id': roteiro.id,
                'id_video': roteiro.id_video,
                'titulo': roteiro.titulo,
                'texto': roteiro.texto,
                'descricao': roteiro.descricao,
                'tags': roteiro.tags,
                'thumb': roteiro.thumb,
                'audio_gerado': roteiro.audio_gerado,
                'video_gerado': roteiro.video_gerado,
                'finalizado': roteiro.finalizado,
                'data_criacao': roteiro.data_criacao.isoformat() if roteiro.data_criacao else None,
                'resolucao': roteiro.resolucao,
                'canal_nome': canal_nome,
                'canal_id': roteiro.canal_id,
                'canal_obj': canal,  # ✅ Adiciona o objeto canal completo
                'video_info': {
                    'arquivo_audio': video_info.arquivo_audio if video_info else None,
                    'arquivo_video': video_info.arquivo_video if video_info else None,
                    'arquivo_legenda': video_info.arquivo_legenda if video_info else None,
                    'audio_mixado': video_info.audio_mixado if video_info else None,
                    'tts_provider': video_info.tts_provider if video_info else None,
                    'duracao': video_info.duracao if video_info else None
                } if video_info else None
            }
            videos.append(video_data)
        
        # Aplicar filtros
        if filter_type == 'audio':
            videos = [v for v in videos if v['audio_gerado']]
        elif filter_type == 'video':
            videos = [v for v in videos if v['video_gerado']]
        elif filter_type == 'finalized':
            videos = [v for v in videos if v['finalizado']]
        
        # Aplicar busca
        if search:
            search_lower = search.lower()
            videos = [v for v in videos if 
                     search_lower in v['titulo'].lower() or 
                     search_lower in v['descricao'].lower() or 
                     search_lower in v['texto'].lower() or
                     search_lower in v['tags'].lower()]
        
        return sorted(videos, key=lambda x: x.get('data_criacao', ''), reverse=True)
        
    except Exception as e:
        print(f"Erro ao buscar vídeos: {e}")
        return []

def get_video_by_id(video_id):
    """Busca um vídeo específico pelo ID"""
    videos = get_videos_with_filters()
    for video in videos:
        if video['id'] == video_id:
            return video
    return None

if __name__ == '__main__':
    # Verificar e criar tabelas se necessário
    print("🔧 Inicializando servidor Flask...")
    if test_connection():
        criar_tabelas()
        print("✅ Banco de dados conectado e pronto!")
    else:
        print("❌ Problema com o banco de dados")
    
    # Iniciar servidor
    app.run(debug=True, host='0.0.0.0', port=5000)