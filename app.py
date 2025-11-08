# app.py
import os
from flask import Flask, flash, redirect, render_template, request, url_for

from controllers.video_controller import VideoController
from controllers.videos_controller import VideosController
from controllers.video_form_validator import VideoFormValidator  # <- usar o validador

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")  # não deixe fixo em PROD

videos_controller = VideosController()
video_controller = VideoController()

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/videos')
def videos():
    roteiros = videos_controller.list_roteiros()
    return render_template('videos.html', roteiros=roteiros)

@app.route('/video/<int:roteiro_id>', methods=['GET', 'POST'])
def video_detail(roteiro_id: int):
    roteiro = video_controller.get_roteiro(roteiro_id)
    if not roteiro:
        flash("Vídeo não encontrado", "error")
        return redirect(url_for('videos'))

    if request.method == 'POST':
        try:
            # ✅ parse/validação centralizados
            roteiro_data = VideoFormValidator.validate_and_extract(request.form)
            video_controller.update_roteiro_and_video(roteiro_id, roteiro_data)
            flash("Alterações salvas com sucesso!", "success")
            return redirect(url_for('video_detail', roteiro_id=roteiro_id))
        except Exception as e:
            flash(f"Erro ao salvar: {e}", "error")
            return render_template('video.html', roteiro=roteiro, error=True)

    edit_mode = request.args.get('edit') == '1'
    return render_template('video.html', roteiro=roteiro, edit_mode=edit_mode)

@app.route('/video/<int:video_id>/delete', methods=['POST'])
def delete_video(video_id: int):
    try:
        if videos_controller.delete_video(video_id):
            flash("Vídeo deletado com sucesso!", "success")
        else:
            flash("Erro ao deletar vídeo", "error")
    except Exception as e:
        flash(f"Erro ao deletar: {e}", "error")
    return redirect(url_for('videos'))

if __name__ == '__main__':
    app.run(debug=True)
