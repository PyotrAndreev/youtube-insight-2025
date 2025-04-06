import os
from dotenv import load_dotenv

load_dotenv()

print("YouTube Key:", "OK" if os.getenv("YOUTUBE_API_KEY") else "MISSING")
print("OpenAI Key:", "OK" if os.getenv("OPENAI_API_KEY") else "MISSING")