

from crud.video_manager import VideoManager

class VideoController:
    def __init__(self):
        self.video_manager = VideoManager()

    def get_video(self, roteiro_id: int):
        with get_session() as session:
            # Carrega o vídeo JUNTAMENTE com o roteiro em uma única query
            video = session.query(Video).options(
                joinedload(Video.roteiro)
            ).filter(Video.roteiro_id == roteiro_id).first()
            
            return video