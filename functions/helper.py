import re

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
