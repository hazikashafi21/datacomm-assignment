import numpy as np
import matplotlib.pyplot as plt
from lineencoding import SPB

def plot_line_code(bits, panels, spb=SPB):
    #panels = [(title, waveform)] 
    #For AMI + scrambling pass two panels: plain AMI and the scrambled signal
    n = len(bits)
    bit_labels = [str(int(b)) for b in bits]          # built once, outside the loop
    fig, axes = plt.subplots(len(panels), 1, sharex=True, squeeze=False,
                             figsize=(min(24, max(8, 0.5 * n)), 2.6 * len(panels)))
    for ax, (title, wave) in zip(axes[:, 0], panels):
        t = np.arange(len(wave)) / spb
        ax.plot(t, wave, drawstyle="steps-post", lw=2)
        ax.axhline(0, color="gray", lw=0.8)
        ax.set_ylim(-1.6, 1.8)
        ax.set_yticks([-1, 0, 1])
        ax.set_title(title)
        ax.set_xticks(np.arange(n + 1))              
        ax.grid(axis="x", ls=":", lw=0.6)
        if n <= 64:                                  
            ax.set_xticks(np.arange(n) + 0.5, labels=bit_labels, minor=True)
            ax.tick_params(axis="x", which="minor", length=0,
                           top=True, labeltop=True, bottom=False, labelbottom=False)
    axes[-1, 0].set_xlabel("Bit interval")
    fig.tight_layout()
    plt.show()


def plot_staircase(t, x, t_dense, x_dense, staircase, title):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(t_dense, x_dense, label="Analog input")
    ax.plot(t, x, "o", ms=4, label="Samples")
    ax.step(t, staircase, where="post", label="Staircase (decoder output)")
    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel("Amplitude")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    plt.show()

