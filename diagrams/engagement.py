import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from db.connect.connect import Connect
from db.repository.VideoRepository import VideoRepository
from functions.helper import convert_to_seconds, get_video_info_by_category, get_video_info_by_channel

def plot_likes_comments_sorted_by_engagement(df, channel_col='title',
                                             likes_col='likes', comments_col='comments', views_col='views',
                                             palette=['#3498db', '#e74c3c'],
                                             figsize=None):
    """
    Строит группированную диаграмму с сортировкой каналов по вовлеченности (лайки + комментарии) на одном графике.

    Параметры:
        df: DataFrame с данными
        channel_col : str, optional
            Название колонки с именами каналов (по умолчанию 'channel')
        likes_col : str, optional
            Название колонки с количеством лайков (по умолчанию 'likes')
        comments_col : str, optional
            Название колонки с количеством комментариев (по умолчанию 'comments')
        views_col : str, optional
            Название колонки с количеством просмотров (по умолчанию 'views')
        palette : list, optional
            Список цветов для столбцов [лайки, комментарии] (по умолчанию синий и красный)
        figsize : tuple, optional
            Размер графика в дюймах (ширина, высота). Если None, размер определяется автоматически
            на основе количества каналов (по умолчанию None)
    """
    # Проверка данных
    required_cols = [channel_col, likes_col, comments_col, views_col]
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        raise ValueError(f"Отсутствуют колонки: {missing}")

    # Рассчитываем общую вовлеченность и сортируем
    grouped_df = df.groupby(channel_col)[[likes_col, comments_col, views_col]].sum().reset_index()
    # grouped_df['views'] = df[views_col]
    grouped_df['engagement'] = (grouped_df[likes_col] + grouped_df[comments_col]) / grouped_df[views_col]
    grouped_df = grouped_df.sort_values('engagement', ascending=False)

    # Автоподбор размера
    num_channels = len(grouped_df)
    if figsize is None:
        figsize = (max(10, num_channels * 0.8), 6)

    # Создание графика
    fig, ax = plt.subplots(figsize=figsize)
    sns.set_style("whitegrid")

    # Позиции и параметры столбцов
    x = np.arange(num_channels)
    bar_width = 0.35

    # Столбцы
    bars_likes = ax.bar(x - bar_width / 2, round(grouped_df[likes_col] / grouped_df[views_col], 5),
                        width=bar_width, color=palette[0], alpha=0.8, label='Лайки')
    bars_comments = ax.bar(x + bar_width / 2, round(grouped_df[comments_col] / grouped_df[views_col], 5),
                           width=bar_width, color=palette[1], alpha=0.8, label='Комментарии')

    ax.set_title('Лайки и комментарии по каналам (сортировка по вовлеченности)', fontsize=14)
    ax.set_xlabel('Канал', fontsize=12)
    ax.set_ylabel('Количество', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(grouped_df[channel_col], rotation=45 if num_channels > 5 else 0, ha='right')
    ax.legend()

    # Подписи значений
    for bars in [bars_likes, bars_comments]:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height:,}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.show()


def plot_likes_comments_separate_engagement(df, channel_col='title',
                                            likes_col='likes', comments_col='comments', views_col='views',
                                            palette=['#3498db', '#e74c3c'],
                                            figsize=None):
    """
    Строит два отдельных графика (лайки и комментарии) с сортировкой каналов по вовлеченности,
    где вовлеченность = (лайки + комментарии) / просмотры.

    Параметры:
        df : pandas.DataFrame
            DataFrame с данными о видео и их метриках
        channel_col : str, optional
            Название колонки с именами каналов (по умолчанию 'channel')
        likes_col : str, optional
            Название колонки с количеством лайков (по умолчанию 'likes')
        comments_col : str, optional
            Название колонки с количеством комментариев (по умолчанию 'comments')
        views_col : str, optional
            Название колонки с количеством просмотров (по умолчанию 'views')
        palette : list, optional
            Список цветов для графиков [лайки, комментарии] (по умолчанию синий и красный)
        figsize : tuple, optional
            Размер графиков в дюймах (ширина, высота). Если None, размер определяется автоматически


    """
    # Проверка данных
    required_cols = [channel_col, likes_col, comments_col, views_col]
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        raise ValueError(f"Отсутствуют колонки: {missing}")

    # Рассчитываем вовлеченность и сортируем
    grouped_df = df.groupby(channel_col)[[likes_col, comments_col, views_col]].sum().reset_index()
    grouped_df['engagement'] = (grouped_df[likes_col] + grouped_df[comments_col]) / grouped_df[views_col]
    grouped_df = grouped_df.sort_values('engagement', ascending=False)

    # Нормализованные значения
    grouped_df['likes_norm'] = grouped_df[likes_col] / grouped_df[views_col]
    grouped_df['comments_norm'] = grouped_df[comments_col] / grouped_df[views_col]

    # Автоподбор размера
    num_channels = len(grouped_df)
    if figsize is None:
        figsize = (max(10, num_channels * 0.6), 8)

    # Создание фигуры с двумя subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
    sns.set_style("whitegrid")

    # Позиции для столбцов
    x = np.arange(num_channels)
    bar_width = 0.7  # Шире, так как отдельные графики

    # График лайков
    bars_likes = ax1.bar(x, grouped_df['likes_norm'],
                         width=bar_width, color=palette[0], alpha=0.8, label='Лайки/просмотры')
    ax1.set_title('Лайки на просмотр по каналам (сортировка по вовлеченности)', fontsize=12)
    ax1.set_ylabel('Лайки/просмотры', fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # График комментариев
    bars_comments = ax2.bar(x, grouped_df['comments_norm'],
                            width=bar_width, color=palette[1], alpha=0.8, label='Комментарии/просмотры')
    ax2.set_title('Комментарии на просмотр по каналам', fontsize=12)
    ax2.set_xlabel('Канал', fontsize=10)
    ax2.set_ylabel('Комментарии/просмотры', fontsize=10)
    ax2.grid(True, linestyle='--', alpha=0.6)

    # Общие настройки для обоих графиков
    for ax in [ax1, ax2]:
        ax.set_xticks(x)
        ax.set_xticklabels(grouped_df[channel_col], rotation=45 if num_channels > 5 else 0, ha='right')
        ax.legend()

        # Подписи значений на столбцах
        for bar in ax.patches:
            height = bar.get_height()
            ax.annotate(f"{height:.5f}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.show()


def plot_engagement(df, title_col='title', views_col='views',
                    likes_col='likes', comments_col='comments',
                    palette='viridis', titles_name="", figsize=None):
    """
    Строит столбчатую диаграмму среднего рейтинга вовлеченности по категориям.
    Рейтинг вовлеченности = (лайки + комментарии) / просмотры

    Параметры:
        df : pandas.DataFrame
            DataFrame с данными о видео
        category_col : str, optional
            Название колонки с категориями (по умолчанию 'category')
        views_col : str, optional
            Название колонки с просмотрами (по умолчанию 'views')
        likes_col : str, optional
            Название колонки с лайками (по умолчанию 'likes')
        comments_col : str, optional
            Название колонки с комментариями (по умолчанию 'comments')
        palette : str, optional
            Цветовая палитра (по умолчанию 'viridis')
        figsize : tuple, optional
            Размер графика (ширина, высота). Если None, размер определяется автоматически
    """
    required_cols = [title_col, views_col, likes_col, comments_col]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"DataFrame должен содержать колонки: {required_cols}")

    # Рассчитываем рейтинг вовлеченности (в процентах)
    df['engagement_rate'] = (df[likes_col] + df[comments_col]) / df[views_col] * 100

    # Группируем по категориям
    engagement_df = df.groupby(title_col)['engagement_rate'].mean().reset_index()
    engagement_df = engagement_df.sort_values('engagement_rate', ascending=False)

    # Автоподбор размера графика
    num_categories = len(engagement_df)
    if figsize is None:
        base_width = 10
        width_per_category = 0.8
        fig_width = max(base_width, num_categories * width_per_category)
        figsize = (fig_width, 6)

    plt.figure(figsize=figsize)
    sns.set_style("whitegrid")

    ax = sns.barplot(
        x=title_col,
        y='engagement_rate',
        data=engagement_df,
        palette=palette,
        alpha=0.8
    )

    fontsize = 10 - min(2, num_categories // 10)  # Автоподбор размера шрифта

    for p in ax.patches:
        height = p.get_height()
        ax.annotate(
            f"{height:.1f}%",
            (p.get_x() + p.get_width() / 2., height),
            ha='center',
            va='center',
            xytext=(0, 5),
            textcoords='offset points',
            fontsize=fontsize
        )

    ax.set_title(f'Средний рейтинг вовлеченности по {titles_name}', fontsize=14)
    ax.set_xlabel('Категория', fontsize=12)
    ax.set_ylabel('Рейтинг вовлеченности (%)', fontsize=12)

    # Настройка подписей категорий
    rotation = 45 if num_categories > 5 else 0
    plt.xticks(
        rotation=rotation,
        ha='right' if rotation != 0 else 'center',
        fontsize=10
    )

    plt.tight_layout()
    plt.show()


session = Connect()
videoRepository = VideoRepository(Connect.session)

video_length = []
short_video_length = []
long_video_length = []
video_names = []
video_views = []
video_likes = []
video_comments_number = []
all_comment_lengths = []
comment_stats_all = defaultdict(int)
comment_stats_shorts = defaultdict(int)
comment_stats_long_video = defaultdict(int)

videos = videoRepository.get_by_id_above(0)
name_category, category_views, category_likes, category_comments = get_video_info_by_category()

for video in videos:
    i = video.id
    video = videoRepository.get_by_id(i)
    if video is not None:
        video_names.append(video.title)
        video_views.append(video.view_count)
        video_comments_number.append(video.comment_count)
        video_likes.append(video.like_count)
        time_str = str(video.duration)
        total_seconds = convert_to_seconds(time_str)
        video_length.append(total_seconds)
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

category_num = 22  # category_num=-1 используется для вывода рейтинга вовлеченности по категориям
chanel, channel_views, channel_likes, channel_comments_length, channel_comments_amount = get_video_info_by_channel(category_num)

channel_sorted_data = sorted(zip(chanel, channel_views, channel_likes, channel_comments_amount),
                             key=lambda x: x[2],  # Сортировка по likes
                             reverse=True)

chanel_sorted, views_sorted, likes_sorted, comments_sorted = zip(*channel_sorted_data)

chanel_info_data = {
    'title': chanel_sorted[:15],
    'views': views_sorted[:15],
    'likes': likes_sorted[:15],
    'comments': comments_sorted[:15]
}
chanel_info_df = pd.DataFrame(chanel_info_data)

video_sorted_data = sorted(zip(video_names, video_views, video_likes, video_comments_number),
                           key=lambda x: x[2],  # Сортировка по likes
                           reverse=True)

video_sorted, video_views_sorted, video_likes_sorted, video_comments_sorted = zip(*video_sorted_data)

video_info_data = {
    'title': video_sorted[:15],
    'views': video_views_sorted[:15],
    'likes': video_likes_sorted[:15],
    'comments': video_comments_sorted[:15]
}
video_info_df = pd.DataFrame(video_info_data)

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

sorted_data2 = sorted(zip(name_category, category_views, category_likes, category_comments),
                      key=lambda x: x[2],  # Сортировка по views
                      reverse=True)

category_sorted, views_category_sorted, likes_category_sorted, comments_category_sorted = zip(*sorted_data2)

category_data = {
    'title': category_sorted,
    'views': views_category_sorted,
    'likes': likes_category_sorted,
    'comments': comments_category_sorted
}
test_df2 = pd.DataFrame(category_data)

plot_engagement(chanel_info_df, titles_name="каналам")
plot_engagement(test_df2, titles_name="категориям")
plot_likes_comments_sorted_by_engagement(chanel_info_df)
plot_likes_comments_separate_engagement(chanel_info_df)
plot_engagement(video_info_df, titles_name="видео")
plot_likes_comments_sorted_by_engagement(video_info_df)
plot_likes_comments_separate_engagement(video_info_df)
