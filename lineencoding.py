import numpy as np

SPB = 20            # samples per bit (must be divisible by 4)
HALF = SPB // 2     # samples per half-bit

# encoders
def nrz_l(bits):
    levels = []
    for bit in bits:
        if bit == 1:
            level = 1
        else:
            level = -1
        levels.append(level)      # first half of the bit
        levels.append(level)      # second half of the bit (same level)
    return levels

def nrz_i(bits):
    levels = []
    level = -1                    # the line starts at -V
    for bit in bits:
        if bit == 1:
            level = -level        # a 1 flips the level, a 0 keeps it
        levels.append(level)
        levels.append(level)
    return levels


def manchester(bits):
    levels = []
    for bit in bits:
        if bit == 1:
            levels.append(-1)     # 1 = low -> high
            levels.append(1)
        else:
            levels.append(1)      # 0 = high -> low
            levels.append(-1)
    return levels


def diff_manchester(bits):
    levels = []
    previous_end = -1             # level at the end of the previous bit
    for bit in bits:
        if bit == 1:
            start = previous_end      # 1 = no transition at the start
        else:
            start = -previous_end     # 0 = transition at the start
        end = -start                  # there is always a transition in the middle
        levels.append(start)
        levels.append(end)
        previous_end = end
    return levels


def ami(bits):
    levels = []
    last = -1                     # polarity of the last 1 (so the first 1 becomes +1)
    for bit in bits:
        if bit == 1:
            last = -last          # 1s alternate: +, -, +, -
            level = last
        else:
            level = 0             # 0 stays at zero volts
        levels.append(level)
        levels.append(level)
    return levels


# scrambling
#   last = polarity of the last pulse before the block
#   odd  = True if the number of 1s since the last substitution is odd
# V = violation (same polarity as the previous pulse), B = normal bipolar pulse
def b8zs_pattern(last, odd):
    return [0, 0, 0, last, -last, 0, -last, last]        # 0 0 0 V B 0 V B


def hdb3_pattern(last, odd):
    if odd:
        return [0, 0, 0, last]                           # 0 0 0 V
    return [-last, 0, 0, -last]                          # B 0 0 V


def scramble(bits, run, pattern_function):
    n = len(bits)
    out = [0] * n           # one level per bit
    last = -1               # polarity of the last pulse
    ones = 0                # number of pulses since the last substitution
    zeros = 0               # number of zeros in a row

    for i in range(n):
        if bits[i] == 1:
            last = -last
            out[i] = last
            ones += 1
            zeros = 0
        else:
            zeros += 1
            if zeros == run:                      # found a full block of zeros
                start = i - run + 1
                pattern = pattern_function(last, ones % 2 == 1)
                out[start:start + run] = pattern
                last = pattern[-1]                # every pattern ends with a pulse
                ones = 0
                zeros = 0

    levels = []
    for level in out:                             # write every level twice
        levels.append(level)
        levels.append(level)
    return levels


def b8zs(bits):
    return scramble(bits, 8, b8zs_pattern)


def hdb3(bits):
    return scramble(bits, 4, hdb3_pattern)


ENCODERS = {
    "NRZ-L": nrz_l,
    "NRZ-I": nrz_i,
    "Manchester": manchester,
    "Differential Manchester": diff_manchester,
    "AMI": ami,
    "B8ZS": b8zs,
    "HDB3": hdb3,
}


#  decoders
def decode_nrz_l(levels):
    bits = []
    for k in range(0, len(levels), 2):
        if levels[k] > 0:
            bits.append(1)
        else:
            bits.append(0)
    return bits


def decode_nrz_i(levels):
    bits = []
    previous = -1                     # the line starts at -V
    for k in range(0, len(levels), 2):
        if levels[k] != previous:     # level changed -> 1
            bits.append(1)
        else:
            bits.append(0)
        previous = levels[k]
    return bits


def decode_manchester(levels):
    bits = []
    for k in range(0, len(levels), 2):
        first = levels[k]
        second = levels[k + 1]
        if second > first:            # rising edge in the middle -> 1
            bits.append(1)
        else:
            bits.append(0)
    return bits


def decode_diff_manchester(levels):
    bits = []
    previous_end = -1
    for k in range(0, len(levels), 2):
        start = levels[k]
        end = levels[k + 1]
        if start == previous_end:     # no transition at the start -> 1
            bits.append(1)
        else:
            bits.append(0)
        previous_end = end
    return bits


def decode_ami(levels):
    bits = []
    for k in range(0, len(levels), 2):
        if levels[k] != 0:            # any pulse (+ or -) is a 1
            bits.append(1)
        else:
            bits.append(0)
    return bits


def descramble(levels, before, after):
    pulses = []
    for k in range(0, len(levels), 2):        # one level per bit
        pulses.append(levels[k])

    bits = []
    for p in pulses:                          # first treat every pulse as a 1
        if p != 0:
            bits.append(1)
        else:
            bits.append(0)

    n = len(pulses)
    last = -1
    i = 0
    while i < n:
        if pulses[i] == 0:
            i += 1
        elif pulses[i] == last and i - before >= 0 and i + after < n:
            for j in range(i - before, i + after + 1):    # the whole block was zeros
                bits[j] = 0
            last = pulses[i + after]
            i += after + 1
        else:
            last = pulses[i]
            i += 1
    return bits


def decode_b8zs(levels):
    return descramble(levels, 3, 4)       # V is the 4th of the 8 bits


def decode_hdb3(levels):
    return descramble(levels, 3, 0)       # V is the last of the 4 bits


DECODERS = {
    "NRZ-L": decode_nrz_l,
    "NRZ-I": decode_nrz_i,
    "Manchester": decode_manchester,
    "Differential Manchester": decode_diff_manchester,
    "AMI": decode_ami,
    "B8ZS": decode_b8zs,
    "HDB3": decode_hdb3,
}


#helpers
def encode(name, bits):
    levels = ENCODERS[name](list(bits))
    return np.array(levels, dtype=int)


def to_waveform(levels, spb=SPB):
    return np.repeat(levels, spb // 2).astype(float)


def read_levels(waveform, spb=SPB):
    half = spb // 2
    levels = []
    for start in range(0, len(waveform), half):
        sample = waveform[start + half // 2]      # middle of this half-bit
        if sample > 0.5:
            levels.append(1)
        elif sample < -0.5:
            levels.append(-1)
        else:
            levels.append(0)
    return levels


def decode(name, waveform, spb=SPB):
    levels = read_levels(waveform, spb)
    return np.array(DECODERS[name](levels), dtype=int)