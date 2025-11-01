# Importar a classe Flask
from flask import Flask, render_template

# Criar uma instância do Flask (o app)
app = Flask(__name__)

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

@app.route('/video/<int:roteiro_id>')
def video(roteiro_id):
    video_controller = VideoController()
    video = video_controller.get_video(roteiro_id)
    return render_template('video.html', video=video)

# Executar o app se este arquivo for o principal
if __name__ == '__main__':
    app.run(debug=True)