

from crud.video_manager import VideoManager


class VideosController:
    def __init__(self):
        self.video_manager = VideoManager()

    def list_videos(self):
        videos = self.video_manager.get_all_videos()          
        return videos
    
    def delete_video(self, video_id: int) -> bool:
        return self.video_manager.deletar(video_id)