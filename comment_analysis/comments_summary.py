import ollama

from db.connect.connect import Connect
from db.repository.VideoRepository import VideoRepository


def comm_summary(comm):
    text = " ".join(comm)
    print(text)
    print("--------------------------------------------------------------------")
    response = ollama.generate(
        model="llama3",
        prompt=f"На русском. Суммаризируй кратко. Напиши максимум тремя предложениями: {text}",
        options={"temperature": 0.3}
    )

    print(response["response"])