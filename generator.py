import numpy as np

def random_bits(n, rng=None):
    # random 0 \ 1 sequence
    if rng is None:
        rng = np.random.default_rng()
    n = max(1, n)
    return rng.integers(0, 2, n)

def bits_with_zero_runs(n, rng=None, run_lengths=(4, 8)):
    # Random sequence  of 4 or 8 zeros 
    if rng is None:
        rng = np.random.default_rng()
    n = max(1, n)
    bits = rng.integers(0, 2, n)               # start with random bits

    number_of_runs = max(1, n // 16)           # roughly one run per 16 bits
    for _ in range(number_of_runs):
        run = int(rng.choice(run_lengths))     # 4 or 8
        if run <= n:
            start = int(rng.integers(0, n - run + 1))
            bits[start:start + run] = 0        # make these positions zero
    return bits


def parse_bits(text):
    cleaned = text.replace(" ", "").replace(",", "")
    if cleaned == "":
        raise ValueError("bits must contain only 0 and 1")
    for ch in cleaned:
        if ch != "0" and ch != "1":
            raise ValueError("bits must contain only 0 and 1")
    return np.array([int(ch) for ch in cleaned], dtype=int)


def to_string(bits):
    return "".join(str(int(b)) for b in bits)


def longest_palindrome(text):
    if text == "":
        return "", 0

    # '101' becomes '#1#0#1#'
    t = "#" + "#".join(text) + "#"
    n = len(t)

    # radius[i] = how many steps we can go left and right from position i
    # while both sides still match
    radius = [0] * n

    # the palindrome that reaches furthest to the right so far
    center = 0      # its middle
    right = 0       # its right end

    for i in range(n):          # try every position as a centre

        # STEP 1: shortcut.
        # If i is inside the big palindrome, the left side is a mirror of the
        # right side, so the answer at i is already known from the mirror spot.
        if i < right:
            mirror = 2 * center - i
            radius[i] = min(right - i, radius[mirror])

        # STEP 2: keep growing while the left and right characters match
        while (i - radius[i] - 1 >= 0 and i + radius[i] + 1 < n
               and t[i - radius[i] - 1] == t[i + radius[i] + 1]):
            radius[i] += 1

        # STEP 3: if this palindrome reaches further right, remember it
        if i + radius[i] > right:
            center = i
            right = i + radius[i]

    # the biggest radius is the longest palindrome
    best_center = radius.index(max(radius))
    best_length = radius[best_center]

    # convert the position in t back to a position in the original text
    start = (best_center - best_length) // 2
    return text[start:start + best_length], start