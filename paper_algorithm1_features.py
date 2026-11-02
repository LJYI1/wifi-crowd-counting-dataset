from __future__ import annotations

import numpy as np
from scipy import signal

T = 200
W_MAD = 200
W_WMA = 100
N_LINKS = 4
N_SUBCARRIERS = 57
FEATURE_DIM = N_LINKS * N_SUBCARRIERS * 2  # 456
PAPER_INDEX = np.arange(-28, 29)  # -28..28，共 57，含 0


BUTTER_ORDER = 4
BUTTER_CUTOFF_HZ = 10.0
FS = 60
DB_FLOOR = 1e-6
MAD_Q_LOW = 5.0
MAD_Q_HIGH = 95.0
SOS = signal.butter(BUTTER_ORDER, BUTTER_CUTOFF_HZ, btype='low', fs=FS, output='sos')


def firmware_to_57(csi_56):
    csi_56 = np.asarray(csi_56)
    if csi_56.shape[-1] != 56:
        raise ValueError('firmware tensor must end with 56 tones')
    zero = np.zeros(csi_56.shape[:-1] + (1,), dtype=csi_56.dtype)
    return np.concatenate([csi_56[..., :28], zero, csi_56[..., 28:]], axis=-1)


def replace_invalid(csi):
    output = np.array(csi, copy=True, dtype=np.complex128)
    bad = ~np.isfinite(output.real) | ~np.isfinite(output.imag)
    output.real[bad] = 0
    output.imag[bad] = 0
    return output


def mad_eq1(amplitude):
    amplitude = np.asarray(amplitude, np.float64)
    if amplitude.shape[0] != W_MAD:
        raise ValueError('MAD window must have 200 samples')
    center = np.median(amplitude, axis=0)
    return np.median(np.abs(amplitude - center), axis=0)


def fit_tau(mad_train):
    values = np.asarray(mad_train, np.float64).ravel()
    values = values[np.isfinite(values)]
    positive = values[values > 0]
    if len(positive) < 10:
        raise ValueError('not enough positive MAD values')
    tau_l = float(np.percentile(positive, MAD_Q_LOW))
    tau_h = float(np.percentile(values, MAD_Q_HIGH))
    if not tau_l < tau_h:
        raise ValueError('MAD thresholds are not ordered')
    return tau_l, tau_h


def mask_eq2(mad, tau_l, tau_h):
    mad = np.asarray(mad, np.float64)
    return (np.isfinite(mad) & (mad >= tau_l) & (mad <= tau_h)).astype(np.float32)


def butterworth(amplitude):
    amplitude = np.asarray(amplitude, np.float64)
    return signal.sosfiltfilt(SOS, amplitude, axis=0)


def wma_eq11(values, width=W_WMA):
    values = np.asarray(values, np.float64)
    weights = np.arange(width, 0, -1, dtype=np.float64)
    numerator = signal.lfilter(weights, [1.0], values, axis=0)
    denominator = width * (width + 1) / 2.0
    return numerator / denominator


def least_squares_phase(phase, subcarrier_index):
    phase = np.asarray(phase, np.float64)
    index = np.asarray(subcarrier_index, np.float64)
    unwrapped = np.unwrap(phase, axis=-1)
    design = np.column_stack([index, np.ones(len(index))])
    slope_intercept, _, _, _ = np.linalg.lstsq(design, unwrapped.T, rcond=None)
    slope, intercept = slope_intercept
    return unwrapped - (slope[:, None] * index[None, :] + intercept[:, None])


def calibrate_all_links(phase, subcarrier_index):
    width = len(subcarrier_index)
    output = np.empty_like(phase, dtype=np.float64)
    for link in range(N_LINKS):
        block = slice(link * width, (link + 1) * width)
        output[:, block] = least_squares_phase(phase[:, block], subcarrier_index)
    return output


def one_window(csi_200):
    csi_200 = replace_invalid(csi_200)
    if csi_200.shape != (T, N_LINKS, N_SUBCARRIERS):
        raise ValueError('expected [200, 4, 57]')
    amplitude = np.abs(csi_200).reshape(T, N_LINKS * N_SUBCARRIERS)
    phase = np.angle(csi_200).reshape(T, N_LINKS * N_SUBCARRIERS)
    mad = mad_eq1(amplitude)
    smoothed = wma_eq11(butterworth(amplitude))
    amplitude_db = 20.0 * np.log10(np.maximum(smoothed, DB_FLOOR))
    calibrated = calibrate_all_links(phase, PAPER_INDEX)
    return amplitude_db.astype(np.float32), calibrated.astype(np.float32), mad.astype(np.float32)


def fuse(amplitude_db, phase):
    values = np.concatenate([amplitude_db, phase], axis=-1)
    if values.shape[-2:] != (T, FEATURE_DIM):
        raise ValueError(f'expected [*, 200, 456], got {values.shape}')
    return values


def expand_mask(mask_228):
    mask_228 = np.asarray(mask_228, np.float32)
    if mask_228.shape[-1] != N_LINKS * N_SUBCARRIERS:
        raise ValueError('mask must have 228 columns')
    return np.concatenate([mask_228, mask_228], axis=-1)


def zscore_then_mask(values, train_rows, mask_456):
    values = np.asarray(values, np.float32)
    train = values[train_rows]
    mean = train.mean(axis=(0, 1), dtype=np.float64)
    std = train.std(axis=(0, 1), dtype=np.float64)
    std = np.where(std < 1e-6, 1.0, std)
    standardized = (values - mean.astype(np.float32)) / std.astype(np.float32)
    return standardized * np.asarray(mask_456, np.float32)[:, None, :]


def paper_feature_matrix(csi_windows_56, train_rows):
    csi_57 = firmware_to_57(csi_windows_56)
    amplitude_db, phase, mad = [], [], []
    for window in csi_57:
        amp_db, phase_cal, score = one_window(window)
        amplitude_db.append(amp_db)
        phase.append(phase_cal)
        mad.append(score)
    amplitude_db = np.stack(amplitude_db)
    phase = np.stack(phase)
    mad = np.stack(mad)
    tau_l, tau_h = fit_tau(mad[train_rows])
    mask_228 = mask_eq2(mad, tau_l, tau_h)
    values = fuse(amplitude_db, phase)
    z_fused = zscore_then_mask(values, train_rows, expand_mask(mask_228))
    return z_fused.astype(np.float32), {'tau_L': tau_l, 'tau_H': tau_h}


if __name__ == '__main__':
    tone = np.linspace(-1.0, 1.0, 56, dtype=np.float64)
    time = np.linspace(0.0, 2.0 * np.pi, T, dtype=np.float64)
    amplitude = 1.0 + 0.3 * np.sin(time)[:, None] * (1.0 + tone[None, :])
    one = amplitude[:, None, :] * np.exp(1j * tone[None, :])
    one = np.broadcast_to(one, (T, N_LINKS, 56))
    demo = np.stack([np.array(one), np.array(one) * 1.2])
    z, tau = paper_feature_matrix(demo, train_rows=np.array([0]))
    inserted = firmware_to_57(demo)
    print('inserted index 0 is', PAPER_INDEX[28], 'value', inserted[0, 0, 0, 28])
    print('Z', z.shape, 'tau', tau)
    if z.shape != (2, 200, 456):
        raise SystemExit('shape is not the paper 200 x 456')
