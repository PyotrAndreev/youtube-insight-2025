import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

from db.connect.connect import Connect
from db.repository.VideoRepository import VideoRepository
from functions.helper import convert_to_seconds, get_video_info_by_channel

def avg_comm_len_by_channel(df, channel_col='channel', comm_len_col='comm_len',
                            comm_amount_col='comm_amount',
                            palette='viridis', figsize=None):
    """
    Визуализирует среднюю длину комментариев по каналам в виде столбчатой диаграммы.

    Параметры:
        df : DataFrame с данными о комментариях
        channel_col : str, optional
            Название колонки с каналами (по умолчанию 'channel')
        comm_len_col : str, optional
            Название колонки с общей длиной комментариев (по умолчанию 'comm_len')
        comm_amount_col : str, optional
            Название колонки с количеством комментариев (по умолчанию 'comm_amount')
        palette : str, optional
            Цветовая палитра (по умолчанию 'viridis')
        figsize : Tuple[int, int], optional
            Размер графика (по умолчанию автоматический подбор)
        top_n : int, optional
            Количество топовых каналов для отображения (по умолчанию все)
    """

    required_cols = [channel_col, comm_len_col, comm_amount_col]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"DataFrame должен содержать колонки: {required_cols}")

    df['avg_length'] = df[comm_len_col] // df[comm_amount_col]

    # Группируем по каналам
    average_length = df.groupby(channel_col)['avg_length'].mean().reset_index()
    average_length = average_length.sort_values('avg_length', ascending=False)

    # Автоподбор размера графика
    num_chanels = len(average_length)
    if figsize is None:
        base_width = 10
        width_per_chanel = 0.8
        fig_width = max(base_width, num_chanels * width_per_chanel)
        figsize = (fig_width, 6)

    plt.figure(figsize=figsize)
    sns.set_style("whitegrid")

    ax = sns.barplot(
        x=channel_col,
        y='avg_length',
        data=average_length,
        palette=palette,
        alpha=0.8
    )

    fontsize = 10 - min(2, num_chanels // 10)

    for p in ax.patches:
        height = p.get_height()
        ax.annotate(
            height,
            (p.get_x() + p.get_width() / 2., height),
            ha='center',
            va='center',
            xytext=(0, 5),
            textcoords='offset points',
            fontsize=fontsize
        )

    ax.set_title('Средняя длина комментариев', fontsize=14)
    ax.set_xlabel('Канал', fontsize=12)
    ax.set_ylabel('Средняя длина комментариев', fontsize=12)

    # Настройка подписей каналов
    rotation = 45 if num_chanels > 5 else 0
    plt.xticks(
        rotation=rotation,
        ha='right' if rotation != 0 else 'center',
        fontsize=10
    )

    plt.tight_layout()
    plt.show()

def plot_comment_count_vs_length(comment_stats, label):
    """
    Визуализирует распределение длины комментариев.

    Параметры:
        comment_stats : Dict[int, int]
            Словарь с распределением длин комментариев {длина: количество}
        label : str, optional
            Метка для заголовка (по умолчанию "")
    """
    plt.figure(figsize=(12, 6))

    df = pd.DataFrame({
        'comment_length': list(comment_stats.keys()),
        'comment_count': list(comment_stats.values())
    }).sort_values('comment_length')

    # Оставляем подписи только для каждого 30-го значения
    xticks = df['comment_length'].iloc[::30]

    sns.barplot(
        x='comment_length',
        y='comment_count',
        data=df,
        color='blue',
        alpha=0.6
    )

    plt.title(f'Количество комментариев в зависимости от длины {label}', fontsize=14)
    plt.xlabel('Длина комментария (символы)', fontsize=12)
    plt.ylabel('Количество комментариев', fontsize=12)
    plt.xticks(ticks=range(0, len(df), 30), labels=xticks, rotation=45)
    plt.tight_layout()
    plt.show()


def plot_video_duration_vs_comments(df, figsize=(12, 7), point_size=50,
                                    alpha=0.6, color='royalblue'):
    """
    Строит точечный график зависимости комментариев от длины видео

    Параметры:
        df : DataFrame с колонками 'video_duration' и 'comment_count'
        figsize : tuple, optional
            Размер графика (ширина, высота)
        point_size : int, optional
            Размер точек на графике
        alpha : float, optional
            Прозрачность точек (0-1)
        color : str, optional
            Цвет точек
    """
    plt.figure(figsize=figsize)

    ax = sns.scatterplot(
        x='video_length',
        y='comments_number',
        data=df,
        s=point_size,
        alpha=alpha,
        color=color
    )

    plt.title('Зависимость количества комментариев от длительности видео\n',
              fontsize=14, pad=20)
    plt.xlabel('Длительность видео (секунды)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.3)

    plt.tight_layout()
    plt.show()


session = Connect()
videoRepository = VideoRepository(Connect.session)

video_length = []
short_video_length = []
long_video_length = []
video_views = []
video_comments_number = []
short_video_views = []
long_video_views = []
short_video_comments_number = []
long_video_comments_number = []
all_comment_lengths = []
comment_stats_all = defaultdict(int)
comment_stats_shorts = defaultdict(int)
comment_stats_long_video = defaultdict(int)

videos = videoRepository.get_by_id_above(0)

for video in videos:
    i = video.id
    video = videoRepository.get_by_id(i)
    if video is not None:
        time_str = str(video.duration)
        total_seconds = convert_to_seconds(time_str)
        video_length.append(total_seconds)
        if total_seconds < 60:
            short_video_length.append(total_seconds)
            short_video_comments_number.append(video.comment_count)
            short_video_views.append(video.view_count)
        else:
            if (total_seconds<10000):
                long_video_length.append(total_seconds)
                long_video_views.append(video.view_count)
                long_video_comments_number.append(video.comment_count)
        len_comm = 0
        len_comm_by_video = 0
        for (comment) in video.comments:
            len_comm = len(comment.text)
            all_comment_lengths.append(len_comm)
            comment_stats_all[len_comm] += 1
            len_comm_by_video += len_comm
            if total_seconds < 60:
                comment_stats_shorts[len_comm] += 1
            else:
                comment_stats_long_video[len_comm] += 1


df_short_videos = pd.DataFrame({
    'video_length': short_video_length,
    'views': short_video_views,
    'comments_number': short_video_comments_number,
}).sort_values('video_length')

df_long_videos = pd.DataFrame({
    'video_length': long_video_length,
    'views': long_video_views,
    'comments_number': long_video_comments_number,
}).sort_values('video_length')
plot_video_duration_vs_comments(df_long_videos)
plot_video_duration_vs_comments(df_short_videos)

category_num = -1
chanel, channel_views, channel_likes, channel_comments_length, channel_comments_amount = get_video_info_by_channel(category_num)

channel_sorted_data = sorted(zip(chanel, channel_comments_length, channel_comments_amount),
                             key=lambda x: x[2],  # Сортировка по comments_length
                             reverse=True)

chanel_sorted, channel_comments_length_sorted, channel_comments_amount_sorted = zip(*channel_sorted_data)

chanel_info_data_comm = {
    'channel': chanel_sorted[:15],
    'comm_len': channel_comments_length_sorted[:15],
    'comm_amount': channel_comments_amount_sorted[:15]
}
test_df = pd.DataFrame(chanel_info_data_comm)
avg_comm_len_by_channel(test_df)

plot_comment_count_vs_length(comment_stats_shorts, "Shorts")
plot_comment_count_vs_length(comment_stats_long_video, "Long videos")

if all_comment_lengths:
    plot_comment_count_vs_length(comment_stats_all, "All videos")
