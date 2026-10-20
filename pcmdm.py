import numpy as np
# PCM
def pcm_encode(x, n_bits):
    x = np.asarray(x, dtype=float)
    lo, hi = x.min(), x.max()
    levels = 2 ** n_bits
    step = (hi - lo) / (levels - 1) if hi > lo else 1.0
    codes = np.round((x - lo) / step).astype(int)
    bitstring = "".join(format(c, f"0{n_bits}b") for c in codes)
    return bitstring, codes, lo, step


def pcm_decode(bitstring, n_bits, lo, step):
    codes = [int(bitstring[i:i + n_bits], 2) for i in range(0, len(bitstring), n_bits)]
    return lo + np.array(codes) * step


# DM
def dm_encode(x, delta):
    bits = np.empty(len(x), dtype=int)
    approx = 0.0
    for k, v in enumerate(x):
        bits[k] = 1 if v > approx else 0
        approx += delta * (2 * bits[k] - 1)
    return bits


def dm_decode(bits, delta):
    return delta * np.cumsum(2 * np.asarray(bits) - 1)