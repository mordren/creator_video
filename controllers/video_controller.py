

from crud.video_manager import VideoManager

class VideoController:
    def __init__(self):
        self.video_manager = VideoManager()

    def get_video(self, roteiro_id: int):
        videos = self.video_manager.get_videos_by_roteiro(roteiro_id)          
        return videos