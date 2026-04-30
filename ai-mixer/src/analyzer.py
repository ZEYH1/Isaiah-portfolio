"""Reference track analysis using librosa + pyloudnorm.

Produces the features Claude needs to reason about loudness, headroom,
and tonal balance without introducing clipping.
"""

from dataclasses import dataclass

import librosa
import numpy as np
import pyloudnorm as pyln


@dataclass
class TrackFeatures:
    tempo: float
    rms_db: float          # average level
    peak_db: float         # peak sample in dBFS (0 = clipping)
    crest_factor_db: float # peak - rms; how dynamic the signal is
    lufs: float            # integrated loudness (broadcast standard)
    headroom_db: float     # = -peak_db; how much you can boost before clipping
    spectral_centroid_hz: float
    low_band_db: float
    mid_band_db: float
    high_band_db: float


def _to_db(x: float) -> float:
    return float(librosa.amplitude_to_db(np.array([max(x, 1e-9)]))[0])


def analyze(path: str) -> TrackFeatures:
    y, sr = librosa.load(path, sr=None, mono=True)

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    rms = float(np.sqrt(np.mean(y ** 2)))
    peak = float(np.max(np.abs(y)))
    rms_db = _to_db(rms)
    peak_db = _to_db(peak)

    meter = pyln.Meter(sr)
    lufs = float(meter.integrated_loudness(y))
    if not np.isfinite(lufs):
        lufs = -70.0

    centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))

    stft = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    low = float(stft[freqs < 250].mean())
    mid = float(stft[(freqs >= 250) & (freqs < 4000)].mean())
    high = float(stft[freqs >= 4000].mean())

    return TrackFeatures(
        tempo=float(np.asarray(tempo).item()),
        rms_db=rms_db,
        peak_db=peak_db,
        crest_factor_db=peak_db - rms_db,
        lufs=lufs,
        headroom_db=-peak_db,
        spectral_centroid_hz=centroid,
        low_band_db=_to_db(low),
        mid_band_db=_to_db(mid),
        high_band_db=_to_db(high),
    )
