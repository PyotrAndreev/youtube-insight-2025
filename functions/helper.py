import re

from db.connect.connect import Connect
from db.repository.VideoRepository import VideoRepository

session = Connect()
videoRepository = VideoRepository(Connect.session)

def convert_to_seconds(time):

    time_points = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    video_duration = list(map(float, re.findall(r"\d+\.?\d*", time)))[::-1]
    for j in range(len(video_duration)):
        time_points[6 - j - 1] = video_duration[j]

    years, mons, days, hours, mins, secs = time_points
    total_seconds = (
            years * 365 * 24 * 60 * 60 +
            mons * 30 * 24 * 60 * 60 +
            days * 24 * 60 * 60 +
            hours * 60 * 60 +
            mins * 60 +
            secs
    )
    return total_seconds

def print_categories():
    categories = ['None', 'Film & Animation', 'Autos & Vehicles', 'None', 'None', 'None', 'None', 'None', 'None',
                  'None',
                  'Music', 'None', 'None', 'None', 'None', 'Pets & Animals', 'None', 'Sports', 'Short Movies',
                  'Travel & Events', 'Gaming', 'Videoblogging', 'People & Blogs', 'Comedy', 'Entertainment',
                  'News & Politics', 'Howto & Style', 'Education', 'Science & Technology', 'Nonprofits & Activism',
                  'Movies', 'Anime/Animation', 'Action/Adventure', 'Classics', 'Comedy', 'Documentary', 'Drama',
                  'Family',
                  'Foreign', 'Horror', 'Sci-Fi/Fantasy', 'Thriller', 'Shorts', 'Shows', 'Trailers']

    for i in range(len(categories)):
        if categories[i] != 'None':
            print(f'{i}: {categories[i]}')

#print_categories()

def get_video_info_by_category():
    info_about_video = []
    name_category = []
    category_views = []
    category_likes = []
    category_comments = []
    categories = ['None', 'Film & Animation', 'Autos & Vehicles', 'None', 'None', 'None', 'None', 'None', 'None',
                  'None',
                  'Music', 'None', 'None', 'None', 'None', 'Pets & Animals', 'None', 'Sports', 'Short Movies',
                  'Travel & Events', 'Gaming', 'Videoblogging', 'People & Blogs', 'Comedy', 'Entertainment',
                  'News & Politics', 'Howto & Style', 'Education', 'Science & Technology', 'Nonprofits & Activism',
                  'Movies', 'Anime/Animation', 'Action/Adventure', 'Classics', 'Comedy', 'Documentary', 'Drama',
                  'Family',
                  'Foreign', 'Horror', 'Sci-Fi/Fantasy', 'Thriller', 'Shorts', 'Shows', 'Trailers']

    videos = videoRepository.get_by_id_above(0)
    for video in videos:
        i = video.id
        video = videoRepository.get_by_id(i)
        if video is not None:
            if video.category_id is not None:
                if categories[video.category_id] not in name_category:
                    name_category.append(categories[video.category_id])
                    category_views.append(video.view_count)
                    category_likes.append(video.like_count)
                    category_comments.append(len(video.comments))
                else:
                    ind = name_category.index(categories[video.category_id])
                    category_views[ind] += video.view_count
                    category_likes[ind] += video.like_count
                    category_comments[ind] += len(video.comments)
    info_about_video.append(name_category)
    info_about_video.append(category_views)
    info_about_video.append(category_likes)
    info_about_video.append(category_comments)
    return info_about_video

def get_video_info_by_channel(category_id):
    info_about_channel = []
    chanel = []
    channel_views = []
    channel_likes = []
    channel_comments_length = []
    channel_comments_amount = []
    len_comm_by_video = 0
    if category_id == -1:
        videos = videoRepository.get_by_id_above(0)
    else:
        videos = videoRepository.get_by_id_category(category_id)
    for video in videos:
        i = video.id
        video = videoRepository.get_by_id(i)
        if video is not None:
            for (comment) in video.comments:
                len_comm = len(comment.text)
                len_comm_by_video += len_comm
            if video.comment_count is None:
                comm_amount = 0
            else:
                comm_amount=video.comment_count
            if video.channel_title not in chanel:
                chanel.append(video.channel_title)
                channel_comments_length.append(len_comm_by_video)
                channel_comments_amount.append(comm_amount)
                channel_views.append(video.view_count)
                channel_likes.append(video.like_count)
            else:
                ind = chanel.index(video.channel_title)
                channel_comments_length[ind] += len_comm_by_video
                channel_comments_amount[ind] += comm_amount
                channel_views[ind] += video.view_count
                channel_likes[ind] += video.like_count
    info_about_channel.append(chanel)
    info_about_channel.append(channel_views)
    info_about_channel.append(channel_likes)
    info_about_channel.append(channel_comments_length)
    info_about_channel.append(channel_comments_amount)
    return info_about_channel

def get_video_info_by_manual_category(manual_categories):
    manual_category_list = []
    manual_category_views_list = []
    manual_category_likes_list = []
    manual_category_comments_list = []
    for manual_category in manual_categories:
        videos = videoRepository.get_by_manual_category(manual_category)
        print(videos)
        views = 0
        likes = 0
        comments = 0
        for video in videos:
            views += video.view_count
            likes += video.like_count
            comments += video.comment_count
        manual_category_list.append(manual_category)
        manual_category_views_list.append(views)
        manual_category_likes_list.append(likes)
        manual_category_comments_list.append(comments)

    info_about_manual_categories = []
    info_about_manual_categories.append(manual_category_list)
    info_about_manual_categories.append(manual_category_views_list)
    info_about_manual_categories.append(manual_category_likes_list)
    info_about_manual_categories.append(manual_category_comments_list)
    return info_about_manual_categories

