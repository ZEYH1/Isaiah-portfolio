"""Reference track analysis using librosa."""

from dataclasses import dataclass

import librosa
import numpy as np


@dataclass
class TrackFeatures:
    tempo: float
    rms_db: float
    spectral_centroid_hz: float
    low_band_db: float
    mid_band_db: float
    high_band_db: float


def analyze(path: str) -> TrackFeatures:
    y, sr = librosa.load(path, sr=None, mono=True)

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    rms_db = float(librosa.amplitude_to_db(np.array([np.sqrt(np.mean(y ** 2))]))[0])
    centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))

    stft = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    low = stft[freqs < 250].mean()
    mid = stft[(freqs >= 250) & (freqs < 4000)].mean()
    high = stft[freqs >= 4000].mean()

    to_db = lambda x: float(librosa.amplitude_to_db(np.array([x]))[0])

    return TrackFeatures(
        tempo=float(np.asarray(tempo).item()),
        rms_db=rms_db,
        spectral_centroid_hz=centroid,
        low_band_db=to_db(low),
        mid_band_db=to_db(mid),
        high_band_db=to_db(high),
    )
