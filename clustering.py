import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import mplcursors
from collections import Counter

from db.connect.connect import Connect
from db.repository.VideoRepository import VideoRepository

session = Connect()
videoRepository = VideoRepository(Connect.session)

video_titles = []

videos = videoRepository.get_by_id_above(0)

for video in videos:
    i = video.id
    video = videoRepository.get_by_id(i)
    if video is not None:
        video_titles.append(video.title)

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

num_clusters = 6
kmeans = KMeans(n_clusters=num_clusters, random_state=42)
clusters = kmeans.fit_predict(embeddings)

def get_cluster_keywords(cluster_titles, top_n=5):
    text = " ".join(cluster_titles)
    words = text.split()
    word_counts = Counter(words)
    return [word for word, count in word_counts.most_common(top_n)]

# Получаем ключевые слова и создаем описания кластеров
cluster_descriptions = []
for i in range(num_clusters):
    cluster_titles = [cleaned_titles[j] for j in range(len(cleaned_titles)) if clusters[j] == i]
    keywords = get_cluster_keywords(cluster_titles)
    description = f"Cluster {i}: {', '.join(keywords)}"
    cluster_descriptions.append(description)

tsne = TSNE(n_components=2, random_state=42, perplexity=4)
embeddings_2d = tsne.fit_transform(embeddings)

cluster_centers = kmeans.cluster_centers_
centers_2d = tsne.fit_transform(cluster_centers)

plt.figure(figsize=(12, 10))

scatter = plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1],
                     c=clusters, cmap='viridis')

legend_elements = []
for i, desc in enumerate(cluster_descriptions):
    legend_elements.append(plt.Line2D([0], [0], marker='o', color='w',
                                    label=desc,
                                    markerfacecolor=plt.cm.viridis(i/num_clusters),
                                    markersize=10))

first_legend = plt.legend(handles=legend_elements, title="Cluster Descriptions",
                         loc='upper left', bbox_to_anchor=(1, 1))

plt.gca().add_artist(first_legend)

# Добавляем интерактивные подсказки
cursor = mplcursors.cursor(scatter, hover=True)

@cursor.connect("add")
def on_add(sel):
    sel.annotation.set_text(video_titles[sel.index])
    sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)

plt.title("Clustering of Video Titles")
plt.tight_layout()
plt.show()