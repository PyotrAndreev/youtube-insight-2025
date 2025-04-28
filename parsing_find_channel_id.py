import urllib.request
import re

from db.connect.connect import Connect
from db.models.channel.channel import Channel
from db.repository.ChannelRepository import ChannelRepository
from db.repository.VideoRepository import VideoRepository


def get_channel_id_from_video(video_url):
    try:
        response = urllib.request.urlopen(video_url)
        html = response.read().decode('utf-8')

        channel_id = re.search(r'"channelId":"([^"]+)"', html)
        if channel_id:
            return channel_id.group(1)

        return None

    except Exception as e:
        print(f"Ошибка: {e}")
        return None

session = Connect()
videoRepository = VideoRepository(Connect.session)
channelRepository = ChannelRepository(Connect.session)
videos = videoRepository.get_unique_channel_titles()
for video in videos:
    print(video.channel_title)
    if channelRepository.find_by_title(video.channel_title) is None:
        video_url = f"https://www.youtube.com/watch?v={video.youtube_id}"  # Пример видео
        channel_id = get_channel_id_from_video(video_url)
        if channel_id:
            channel = Channel()
            channel.title = video.channel_title
            channel.youtube_id = channel_id
            channelRepository.save(channel)
            print(video.channel_title)
            print(f"ID канала: {channel_id}")
            print("---------------------------------")
        else:
            print(video.channel_title)
            print("Не удалось найти channelId в HTML")