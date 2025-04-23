import subprocess
from pathlib import Path

class OpenSmileAnalyzer:
    def __init__(self, smile_path="SMILExtract", config="config/emobase/emobase.conf"):
        self.smile_path = smile_path
        self.config = config

    def analyze(self, audio_path: Path, output_csv: Path) -> bool:
        """Запускает OpenSMILE для анализа аудио"""
        try:
            subprocess.run([
                self.smile_path,
                "-C", self.config,
                "-I", str(audio_path),
                "-O", str(output_csv),
                "-nologfile",
            ], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"OpenSMILE ошибка: {e}")
            return False
