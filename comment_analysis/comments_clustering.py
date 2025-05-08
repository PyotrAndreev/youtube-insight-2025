import nltk
import spacy
import pandas as pd
from sklearn.metrics import pairwise_distances_argmin_min
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sentence_transformers import SentenceTransformer

from comment_analysis.tone_of_comments import analyze_comments
from db.repository.ChannelRepository import ChannelRepository
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import mplcursors
from collections import Counter
import numpy as np
import re

from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

from db.connect.connect import Connect
from db.repository.VideoRepository import VideoRepository

session = Connect()
videoRepository = VideoRepository(Connect.session)

video_titles = []

videos = videoRepository.get_by_id_above(0)

i = 7405
video = videoRepository.get_by_id(i)
if video is not None:
    for comment in video.comments:
        video_titles.append(comment.text)

nltk.download('punkt')
nltk.download('stopwords')
stop_words = set(stopwords.words('russian'))


def clean_text(text):
    text = re.sub(r'\b\d+\b', '', text)

    text = re.sub(r'#[\wа-яА-ЯёЁ]+', '', text)

    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    tokens = word_tokenize(text.lower())
    tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
    return " ".join(tokens)


def clean_text_aggressive(text):
    # Удаляем URL
    text = re.sub(r'https?://\S+|www\.\S+', '', text)

    # Удаляем эмодзи и спецсимволы
    text = re.sub(r'[^\w\s#]', ' ', text)

    # Лемматизация
    nlp = spacy.load('ru_core_news_sm')
    doc = nlp(text)
    tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]

    tokens = [word for word in tokens if len(word) > 5]

    return " ".join(tokens)


cleaned_titles1 = [clean_text(title) for title in video_titles]
cleaned_titles = []
for j in cleaned_titles1:
    if len(j) > 0:
        cleaned_titles.append(j)
# print(cleaned_titles)
# print(len(cleaned_titles))

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
embeddings = model.encode(cleaned_titles)

num_clusters = 10
kmeans = KMeans(n_clusters=num_clusters, random_state=42)
clusters = kmeans.fit_predict(embeddings)


def get_cluster_keywords(cluster_titles, top_n=5):
    text = " ".join(cluster_titles)
    words = text.split()
    word_counts = Counter(words)
    return [word for word, count in word_counts.most_common(top_n)]


cluster_descriptions = []
for i in range(num_clusters):
    cluster_titles = [cleaned_titles[j] for j in range(len(cleaned_titles)) if clusters[j] == i]
    keywords = get_cluster_keywords(cluster_titles)
    description = f"Cluster {i}: {', '.join(keywords)}"
    cluster_descriptions.append(description)

tsne = TSNE(n_components=2, random_state=42, perplexity=9)
embeddings_2d = tsne.fit_transform(embeddings)

cluster_centers = kmeans.cluster_centers_
centers_2d = tsne.fit_transform(cluster_centers)

plt.figure(figsize=(12, 10))

scatter = plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1],
                      c=clusters, cmap='viridis')

print("\nАнализ центров кластеров:")
for i in range(num_clusters):
    cluster_points = embeddings[clusters == i]

    closest_idx, _ = pairwise_distances_argmin_min([cluster_centers[i]], cluster_points)
    closest_comment = video_titles[np.where(clusters == i)[0][closest_idx[0]]]

    distances = np.linalg.norm(cluster_points - cluster_centers[i], axis=1)
    top3_idx = np.argsort(distances)[:3]
    top3_comments = [video_titles[idx] for idx in np.where(clusters == i)[0][top3_idx]]

    print(f"\nКластер {i}:")
    print(f"Ключевые слова: {cluster_descriptions[i].split(':')[1].strip()}")
    print("---")
    print(f"Центр: '{closest_comment}'")
    print("\nТоп-3 ближайших комментария:")

    for j, comment in enumerate(top3_comments, 1):
        print(f"{j}. {comment}")
    cluster_points = embeddings[clusters == i]
    cluster_indices = np.where(clusters == i)[0]
    video_titles1 = np.array(video_titles)
    cluster_comments = video_titles1[cluster_indices]

    comm = []
    for idx, comment in enumerate(cluster_comments, 1):
        comm.append(comment)

    sample_comments = pd.DataFrame({
        'text': comm
    })

    results = analyze_comments(sample_comments)
    print(f"Количество комментариев: {len(comm)}")

    print("\nРезультаты анализа тональности:")
    print(f"Позитивных: {results['stats']['positive']} ({results['stats']['positive_perc']:.1f}%)")
    print(f"Негативных: {results['stats']['negative']} ({results['stats']['negative_perc']:.1f}%)")
    print(f"Нейтральных: {results['stats']['neutral']} ({results['stats']['neutral_perc']:.1f}%)")


legend_elements = []
for i, desc in enumerate(cluster_descriptions):
    legend_elements.append(plt.Line2D([0], [0], marker='o', color='w',
                                      label=desc,
                                      markerfacecolor=plt.cm.viridis(i / (num_clusters - 1)),
                                      markersize=10))

first_legend = plt.legend(handles=legend_elements, title="Cluster Descriptions",
                          loc='upper left', bbox_to_anchor=(1, 1))

plt.gca().add_artist(first_legend)

cursor = mplcursors.cursor(scatter, hover=True)


@cursor.connect("add")
def on_add(sel):
    sel.annotation.set_text(video_titles[sel.index])
    sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)


plt.title("Clustering of Video Titles")
plt.tight_layout()
plt.show()

silhouette = silhouette_score(embeddings, clusters)
calinski = calinski_harabasz_score(embeddings, clusters)
davies = davies_bouldin_score(embeddings, clusters)

print(f"""
Оценка кластеризации:
1. Silhouette Score: {silhouette:.3f} (чем ближе к 1, тем лучше)
2. Calinski-Harabasz Index: {calinski:.1f} (чем выше, тем лучше)
3. Davies-Bouldin Index: {davies:.3f} (чем ближе к 0, тем лучше)
""")
