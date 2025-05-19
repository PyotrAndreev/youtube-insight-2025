from functions.helper import get_video_info_by_channel
from db.repository.ChannelRepository import ChannelRepository


category_num = 28  # category_num=-1 используется для вывода рейтинга вовлеченности по категориям
channel, channel_views, channel_likes, channel_comments_length, channel_comments_amount = get_video_info_by_channel(category_num)
print(channel)