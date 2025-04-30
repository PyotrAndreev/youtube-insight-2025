import os
import json
import requests
import numpy as np
import librosa
import soundfile as sf
import pandas as pd
from scipy.signal import butter, lfilter

# Configuration: set your DeepSeek API key here or via environment variables
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY', 'sk-d0d3c590942846278ce321946af2bbc9')

# DeepSeek endpoint
deepseek_endpoint = 'https://api.deepseek.ai/process'


def call_deepseek(audio_path: str) -> dict:
    """
    Send audio file to DeepSeek for analysis.
    On network failure or HTTP error, logs and returns empty dict.
    """
    try:
        with open(audio_path, 'rb') as f:
            files = {'audio': f}
            headers = {'X-API-Key': deepseek_api_key}
            response = requests.post(deepseek_endpoint, files=files, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Warning: DeepSeek request failed for {audio_path}: {e}")
        return {}


def add_noise(y: np.ndarray, snr_db: float) -> np.ndarray:
    """
    Add white noise to signal to achieve target SNR in dB.
    """
    sig_power = np.mean(y ** 2)
    sig_db = 10 * np.log10(sig_power)
    noise_db = sig_db - snr_db
    noise_power = 10 ** (noise_db / 10)
    noise = np.random.normal(0, np.sqrt(noise_power), y.shape)
    return y + noise


def change_speed(y: np.ndarray, rate: float) -> np.ndarray:
    """
    Change speed by rate factor: >1 faster, <1 slower
    """
    return librosa.effects.time_stretch(y, rate)


def butter_filter(cutoff: float, sr: int, btype: str, order: int=4):
    nyq = 0.5 * sr
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype=btype, analog=False)
    return b, a


def apply_eq(y: np.ndarray, sr: int, low_gain_db: float=0, high_gain_db: float=0,
             low_freq: float=300.0, high_freq: float=3000.0) -> np.ndarray:
    """
    Simple EQ: apply low-shelf and high-shelf adjustments via gain on filtered signals.
    """
    b_low, a_low = butter_filter(low_freq, sr, btype='low')
    low = lfilter(b_low, a_low, y)
    b_high, a_high = butter_filter(high_freq, sr, btype='high')
    high = lfilter(b_high, a_high, y)
    low_gain = 10 ** (low_gain_db / 20)
    high_gain = 10 ** (high_gain_db / 20)
    return y + (low_gain - 1) * low + (high_gain - 1) * high


def extract_audio_features(y: np.ndarray, sr: int) -> dict:
    """
    Extract basic audio features: RMS energy and tempo.
    """
    rms = librosa.feature.rms(y=y)[0]
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    # Ensure tempo is scalar
    if isinstance(tempo, (list, np.ndarray)):
        tempo = float(np.array(tempo).flatten()[0])
    else:
        tempo = float(tempo)
    return {
        'mean_rms': float(np.mean(rms)),
        'std_rms': float(np.std(rms)),
        'tempo': tempo
    }


def generate_test_audio(output_dir: str):
    """
    Create synthetic test audio files (sine wave, white noise, chirp) in output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    sr = 22050
    duration = 2.0  # seconds

    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    sine = 0.5 * np.sin(2 * np.pi * 440 * t)
    sf.write(os.path.join(output_dir, 'sine_440Hz.wav'), sine, sr)

    noise = np.random.normal(0, 0.5, sine.shape)
    sf.write(os.path.join(output_dir, 'white_noise.wav'), noise, sr)

    chirp = 0.5 * np.sin(2 * np.pi * t * (220 + 220 * t))
    sf.write(os.path.join(output_dir, 'chirp.wav'), chirp, sr)

    print(f"Created test audio files in {output_dir}")


def run_tests(input_dir: str, output_csv: str):
    """
    Run adversarial tests on all audio files in input_dir and save results to CSV.
    If no audio found, auto-generate test files.
    """
    if not os.path.isdir(input_dir) or not any(fname.lower().endswith(('.wav', '.flac', '.mp3')) for fname in os.listdir(input_dir)):
        print("No audio found in input directory; generating test audio...")
        generate_test_audio(input_dir)

    records = []
    transformations = [
        ('noise_20dB', lambda y, sr: add_noise(y, 20)),
        ('noise_10dB', lambda y, sr: add_noise(y, 10)),
        ('speed_x1.1', lambda y, sr: change_speed(y, 1.1)),
        ('speed_x0.9', lambda y, sr: change_speed(y, 0.9)),
        ('eq_low+6_high-6', lambda y, sr: apply_eq(y, sr, low_gain_db=6, high_gain_db=-6)),
    ]

    for fname in os.listdir(input_dir):
        if not fname.lower().endswith(('.wav', '.flac', '.mp3')):
            continue
        full_path = os.path.join(input_dir, fname)
        y, sr = librosa.load(full_path, sr=None)

        deep_orig = call_deepseek(full_path)
        orig_feats = extract_audio_features(y, sr)

        for name, transform in transformations:
            try:
                y_mod = transform(y, sr)
                tmp_path = os.path.join(input_dir, f'tmp_{name}_{fname}')
                sf.write(tmp_path, y_mod, sr)

                deep_mod = call_deepseek(tmp_path)
                mod_feats = extract_audio_features(y_mod, sr)

                records.append({
                    'file': fname,
                    'transform': name,
                    'deepseek_orig': json.dumps(deep_orig),
                    'deepseek_mod': json.dumps(deep_mod),
                    **orig_feats,
                    **{f'mod_{k}': v for k, v in mod_feats.items()}
                })

                os.remove(tmp_path)
            except Exception as e:
                print(f"Error processing {fname} with {name}: {e}")

    df = pd.DataFrame(records)
    df.to_csv(output_csv, index=False)
    print(f"Results saved to {output_csv}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Adversarial testing for DeepSeek audio model')
    parser.add_argument('--input_dir', type=str, required=True, help='Directory with audio files')
    parser.add_argument('--output_csv', type=str, default='results.csv', help='Path to output CSV file')
    args = parser.parse_args()

    run_tests(args.input_dir, args.output_csv)
