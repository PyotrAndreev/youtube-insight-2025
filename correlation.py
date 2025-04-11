from collections import defaultdict

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from db.connect.connect import Connect
from db.repository.VideoRepository import VideoRepository
from functions.helper import convert_to_seconds

session = Connect()
videoRepository = VideoRepository(Connect.session)

video_length = []
views = []
titles = []
durations = []
channel_views = []
comments = []
comments_length = []
likes = []
all_comment_lengths = []
name_category = []
category_views = []
category_likes = []
category_comments = []
comment_stats = defaultdict(int)

videos = videoRepository.get_by_id_above(0)

for video in videos:
    i = video.id
    video = videoRepository.get_by_id(i)
    if video is not None:
        time_str = str(video.duration)
        total_seconds=convert_to_seconds(time_str)
        video_length.append(total_seconds)
        len_comm = 0
        comm_amount = 0
        for (comment) in video.comments:
            len_comm += len(comment.text)
            comm_amount += 1
        titles.append(video.channel_title)
        views.append(video.view_count)
        if comm_amount > 0:
            comments_length.append(len_comm / comm_amount)
        else:
            comments_length.append(0)
        comments.append(len(video.comments))
        durations.append(total_seconds)
        likes.append(video.like_count)

data = {
    'video_title': titles,
    'views': views,
    'comment_amount': comments,
    'duration': durations,
    'comment_length': comments_length,
    'likes': likes
}

df = pd.DataFrame(data)

df['title_length'] = df['video_title'].apply(len)

corr_columns = ['views', 'title_length', 'comment_length', 'comment_amount', 'duration', 'likes']
corr_df = df[corr_columns]

correlation_matrix = corr_df.corr()

plt.figure(figsize=(8, 6))
sns.heatmap(correlation_matrix,
            annot=True,
            cmap='coolwarm',
            fmt=".2f",
            linewidths=.5)
plt.title('Матрица корреляции')
plt.show()
