# Importar a classe Flask

from flask import Flask, flash, redirect, render_template, request, url_for

# Criar uma instância do Flask (o app)
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

from controllers.video_controller import VideoController
from controllers.videos_controller import VideosController
from crud.video_manager import VideoManager

# Definir uma rota básica
videos_controller = VideosController() 

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/videos')
def videos():
    videos = videos_controller.list_videos()
    return render_template('videos.html', videos = videos)

@app.route('/video/<int:roteiro_id>', methods=['GET', 'POST'])
def video_detail(roteiro_id):
    """Rota única para visualizar e editar vídeo usando video.html"""
    controller = VideoController()
    
    if request.method == 'POST':
        # Modo edição - salvar alterações
        try:
            controller.update_roteiro_and_video(roteiro_id, request.form)
            flash("Alterações salvas com sucesso!", "success")
            return redirect(url_for('video_detail', roteiro_id=roteiro_id))
        except Exception as e:
            flash(f"Erro ao salvar: {str(e)}", "error")
            # Em caso de erro, recarrega a página em modo edição
            video = controller.get_video(roteiro_id)
            if video:
                return render_template('video.html', video=video, error=True)
            else:
                return redirect(url_for('videos'))
    
    # Modo GET - carregar dados
    video = controller.get_video(roteiro_id)
    
    if not video:
        flash("Vídeo não encontrado", "error")
        return redirect(url_for('videos'))
    
    # Verifica se deve mostrar em modo edição
    edit_mode = request.args.get('edit') == '1'
    return render_template('video.html', video=video, edit_mode=edit_mode)

# Rota para deletar vídeo (se necessário)
@app.route('/video/<int:video_id>/delete', methods=['POST'])
def delete_video(video_id):
    """Rota para deletar um vídeo"""
    controller = VideosController()
    try:
        if controller.delete_video(video_id):
            flash("Vídeo deletado com sucesso!", "success")
        else:
            flash("Erro ao deletar vídeo", "error")
    except Exception as e:
        flash(f"Erro ao deletar: {str(e)}", "error")
    
    return redirect(url_for('videos'))

if __name__ == '__main__':
    app.run(debug=True)

if __name__ == '__main__':
    app.run(debug=True)