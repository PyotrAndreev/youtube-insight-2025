import logging
import torch
import numpy as np
import pandas as pd
from tqdm import tqdm
from transformers import AutoModelForSequenceClassification, BertTokenizerFast
from db.repository.ChannelRepository import ChannelRepository
from db.repository.PlaylistRepository import PlaylistRepository
import matplotlib.pyplot as plt

from comments_summary import comm_summary
from db.connect.connect import Connect
from db.repository.VideoRepository import VideoRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    def __init__(self, model_name='blanchefort/rubert-base-cased-sentiment-rusentiment'):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.tokenizer = BertTokenizerFast.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)
        self.model.eval()

    def analyze_sentiments(self, texts: list[str], batch_size: int = 16) -> np.ndarray:
        """
        Анализирует тональность списка текстов
        Возвращает массив с предсказаниями: 0 - нейтральный, 1 - позитивный, 2 - негативный
        """
        sentiments = []

        with torch.no_grad():
            for i in tqdm(range(0, len(texts), batch_size), desc="Анализ тональности"):
                batch = texts[i:i + batch_size]
                try:
                    inputs = self.tokenizer(
                        batch,
                        max_length=512,
                        padding=True,
                        truncation=True,
                        return_tensors='pt'
                    ).to(self.device)

                    outputs = self.model(**inputs)
                    predicted = torch.argmax(outputs.logits, dim=1).cpu().numpy()
                    sentiments.append(predicted)

                except Exception as e:
                    logger.error(f"Ошибка при обработке батча {i}: {e}")
                    continue

        return np.concatenate(sentiments) if sentiments else np.array([])

    def calculate_stats(self, sentiments: np.ndarray) -> dict:

        if len(sentiments) == 0:
            return {
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'positive_perc': 0,
                'negative_perc': 0,
                'neutral_perc': 0,
                'total': 0
            }

        total = len(sentiments)
        positive = np.sum(sentiments == 1)
        negative = np.sum(sentiments == 2)
        neutral = np.sum(sentiments == 0)

        return {
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'positive_perc': (positive / total) * 100,
            'negative_perc': (negative / total) * 100,
            'neutral_perc': (neutral / total) * 100,
            'total': total
        }

    def plot_sentiment_distribution(self, stats: dict, title: str = "Распределение тональности комментариев"):
        """Визуализирует распределение тональностей"""
        labels = ['Позитивные', 'Негативные', 'Нейтральные']
        sizes = [stats['positive'], stats['negative'], stats['neutral']]
        colors = ['#4CAF50', '#F44336', '#9E9E9E']

        plt.figure(figsize=(8, 6))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')
        plt.title(title)
        plt.tight_layout()
        plt.show()


def analyze_comments(comments: pd.DataFrame) -> dict:
    analyzer = SentimentAnalyzer()

    texts = comments['text'].fillna('').astype(str).tolist()

    sentiments = analyzer.analyze_sentiments(texts)

    stats = analyzer.calculate_stats(sentiments)

    analyzer.plot_sentiment_distribution(stats)

    comments['sentiment'] = sentiments
    comments['sentiment_label'] = comments['sentiment'].map({
        0: 'neutral',
        1: 'positive',
        2: 'negative'
    })

    return {
        'stats': stats,
        'comments_with_sentiment': comments,
        'sentiment_distribution': analyzer.plot_sentiment_distribution
    }


def get_negative_comments(comments_df: pd.DataFrame) -> pd.DataFrame:
    """
    Возвращает DataFrame только с отрицательными комментариями

    :param comments_df: DataFrame с колонками 'text' и 'sentiment_label'
    :return: DataFrame только с негативными комментариями
    """

    if 'sentiment_label' not in comments_df.columns:
        raise ValueError("DataFrame должен содержать колонку 'sentiment_label'")

    negative_comments = comments_df[comments_df['sentiment_label'] == 'negative']

    return negative_comments[['text', 'sentiment_label']]


session = Connect()
videoRepository = VideoRepository(Connect.session)
video = videoRepository.get_by_id(9743)
comments = video.comments
comm = []
for comment in comments:
    comm.append(comment.text)

sample_comments = pd.DataFrame({
    'text': comm
})

results = analyze_comments(sample_comments)

negative_only = get_negative_comments(results['comments_with_sentiment'])

print("\nОтрицательные комментарии:")
print(negative_only)
negative_comm_list = negative_only['text'].tolist()
comm_summary(negative_comm_list)

print("\nРезультаты анализа тональности:")
print(f"Позитивных: {results['stats']['positive']} ({results['stats']['positive_perc']:.1f}%)")
print(f"Негативных: {results['stats']['negative']} ({results['stats']['negative_perc']:.1f}%)")
print(f"Нейтральных: {results['stats']['neutral']} ({results['stats']['neutral_perc']:.1f}%)")

print("\nКомментарии с предсказаниями:")
print(results['comments_with_sentiment'][['text', 'sentiment_label']])
