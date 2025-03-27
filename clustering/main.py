from googleapiclient.discovery import build
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import mplcursors
from collections import Counter

API_KEY = "YOUR_API_KEY"
youtube = build('youtube', 'v3', developerKey=API_KEY)

def get_channels_by_subscribers(min_subscribers):
    request = youtube.search().list(
        q="technology",
        type="channel",
        part="snippet",
        maxResults=10
    )
    response = request.execute()

    channels = []
    for item in response['items']:
        channel_id = item['id']['channelId']
        channel_info = youtube.channels().list(
            id=channel_id,
            part="snippet,statistics"
        ).execute()
        subscribers = int(channel_info['items'][0]['statistics']['subscriberCount'])
        if subscribers >= min_subscribers:
            channels.append({
                "id": channel_id,
                "name": channel_info['items'][0]['snippet']['title'],
                "subscribers": subscribers
            })
    return channels

def get_videos_from_channel(channel_id, max_results=10):
    request = youtube.search().list(
        channelId=channel_id,
        type="video",
        part="snippet",
        maxResults=max_results
    )
    response = request.execute()
    videos = [item['snippet']['title'] for item in response['items']]
    return videos

min_subscribers = 1000000
channels = get_channels_by_subscribers(min_subscribers)
video_titles = []
for channel in channels:
    videos = get_videos_from_channel(channel['id'])
    video_titles.extend(videos)

nltk.download('punkt')
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

def clean_text(text):
    tokens = word_tokenize(text.lower())
    tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
    return " ".join(tokens)

cleaned_titles = [clean_text(title) for title in video_titles]

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(cleaned_titles)

num_clusters = 5
kmeans = KMeans(n_clusters=num_clusters, random_state=42)
clusters = kmeans.fit_predict(embeddings)

def get_cluster_keywords(cluster_titles, top_n=5):
    text = " ".join(cluster_titles)
    words = text.split()
    word_counts = Counter(words)
    return [word for word, count in word_counts.most_common(top_n)]


tsne = TSNE(n_components=2, random_state=42)
embeddings_2d = tsne.fit_transform(embeddings)

plt.figure(figsize=(10, 8))
scatter = plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], c=clusters, cmap='viridis')

cursor = mplcursors.cursor(scatter, hover=True)

@cursor.connect("add")
def on_add(sel):
    sel.annotation.set_text(video_titles[sel.index])
    sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)

plt.title("Clustering of Video Titles")
plt.show()