from db.connect.connect import Connect
from db.models.channel.channel import Channel
from db.repository.ChannelRepository import ChannelRepository
from db.repository.VideoRepository import VideoRepository

session = Connect()
videoRepository = VideoRepository(Connect.session)
channelRepository = ChannelRepository(Connect.session)

channels = channelRepository.get_by_id_above(0)
for channel in channels:
    videos = videoRepository.get_by_channel_title(channel.title)
    for video in videos:
        if video.channel_id is None:
            video.channel_id = channel.id
            videoRepository.save(video)