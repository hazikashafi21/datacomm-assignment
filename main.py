import numpy as np
import generator
import lineencoding
import pcmdm
import plotting


LINE_CODES = {"1": "NRZ-L", "2": "NRZ-I", "3": "Manchester",
              "4": "Differential Manchester", "5": "AMI"}
SCRAMBLING = {"1": "B8ZS", "2": "HDB3"}
SYMBOLS = {1: "+", 0: "0", -1: "-"}


# takingg input
def ask_choice(title, options):
    print()
    print(title)
    for key in options:
        print(key + ") " + options[key])
    choice = input("> ").strip()
    while choice not in options:
        print("Invalid choice, try again.")
        choice = input("> ").strip()
    return choice


def ask_yes_no(question):
    answer = input(question + " (y/n): ").strip().lower()
    return answer == "y"


def ask_number(prompt, default, number_type=float):
    
    while True:
        text = input(f"{prompt} [{default}]: ").strip()
        if text == "":
            return default
        try:
            return number_type(text)
        except ValueError:
            print("Please enter a valid number.")


#  digital input
def random_data():
    n = ask_number("Number of bits", 32, int)
    return generator.random_bits(n)


def zero_run_data():
    n = ask_number("Number of bits", 32, int)
    return generator.bits_with_zero_runs(n)


def typed_data():
    while True:
        text = input("Enter bits (e.g. 1011 0001): ")
        try:
            return generator.parse_bits(text)
        except ValueError:
            print("Only 0 and 1 are allowed.")


DIGITAL_MENU = {"1": "Completely random sequence",
                "2": "Random sequence with fixed runs of 4 / 8 zeros",
                "3": "Type my own bits"}
DIGITAL_SOURCES = {"1": random_data, "2": zero_run_data, "3": typed_data}


def show_data(bits):
    text = generator.to_string(bits)
    palindrome, start = generator.longest_palindrome(text)
    print()
    print("Digital data stream :", text)
    print(f"Longest palindrome  : {palindrome} (length {len(palindrome)}, starts at index {start})")


# line coding
def line_coding(bits):
    name = LINE_CODES[ask_choice("Choose a line coding scheme:", LINE_CODES)]
    panels = []     # each panel is (title, waveform) and gets its own plot

    if name == "AMI" and ask_yes_no("\nDo you want scrambling?"):
        ami_levels = lineencoding.encode("AMI", bits)
        panels.append(("AMI (before scrambling)", lineencoding.to_waveform(ami_levels)))
        name = SCRAMBLING[ask_choice("Type of scrambling:", SCRAMBLING)]

    levels = lineencoding.encode(name, bits)
    waveform = lineencoding.to_waveform(levels)
    panels.append((name + " encoded signal", waveform))

    print()
    print(name, "signal levels (per half-bit):")
    symbols = [SYMBOLS[int(v)] for v in levels]
    print(" ".join(symbols))
    print("Close the plot window to continue...")
    plotting.plot_line_code(bits, panels)

    if ask_yes_no("\nDo you want to decode the signal?"):
        # decoding uses only the waveform,,not the original bits
        decoded = lineencoding.decode(name, waveform)
        print("Decoded stream :", generator.to_string(decoded))
        if np.array_equal(decoded, bits):
            print("Matches original!")
        else:
            print("MISMATCH with original.")


def digital_flow():
    choice = ask_choice("Digital data source:", DIGITAL_MENU)
    bits = DIGITAL_SOURCES[choice]()
    show_data(bits)
    line_coding(bits)


# analog input
def sine_input(samples_per_cycle):
    amp = ask_number("Amplitude", 5.0)
    freq = ask_number("Frequency (Hz)", 1.0)
    fs = ask_number("Sampling rate (Hz)", samples_per_cycle * freq)
    if fs < 2 * freq:
        print("Warning: sampling rate is below the Nyquist rate (2 x frequency).")

    duration = 2 / freq                                   # show two cycles
    t = np.arange(int(duration * fs)) / fs                # sample times
    x = amp * np.sin(2 * np.pi * freq * t)                # samples
    t_dense = np.linspace(0, duration, 1000)              # curve for the plot
    x_dense = amp * np.sin(2 * np.pi * freq * t_dense)
    return t, x, t_dense, x_dense


def typed_input(samples_per_cycle):
    while True:
        text = input("Enter sample values separated by commas: ")
        try:
            x = np.array(text.split(","), dtype=float)
            break
        except ValueError:
            print("Please enter numbers only, e.g. 0, 2.5, 4, 2.5, 0, -2.5")
    t = np.arange(len(x))
    return t, x, t, x


ANALOG_MENU = {"1": "Sine wave", "2": "Type my own sample values"}
ANALOG_SOURCES = {"1": sine_input, "2": typed_input}


# PCM / DM
def pcm_flow(signal):
    t, x, t_dense, x_dense = signal
    n_bits = max(1, ask_number("Bits per sample", 3, int))
    bitstring, codes, low, step = pcmdm.pcm_encode(x, n_bits)
    staircase = pcmdm.pcm_decode(bitstring, n_bits, low, step)
    print()
    print("Quantised levels :", codes.tolist())
    title = f"PCM ({n_bits} bits/sample, {2 ** n_bits} levels)"
    plotting.plot_staircase(t, x, t_dense, x_dense, staircase, title)
    return generator.parse_bits(bitstring)


def dm_flow(signal):
    t, x, t_dense, x_dense = signal
    # default step = biggest jump between two samples
    jumps = np.abs(np.diff(x))
    default = 0.1
    if len(jumps) > 0 and jumps.max() > 0:
        default = round(float(jumps.max()), 3)
    delta = ask_number("Step size delta", default)
    bits = pcmdm.dm_encode(x, delta)
    staircase = pcmdm.dm_decode(bits, delta)
    plotting.plot_staircase(t, x, t_dense, x_dense, staircase, f"Delta modulation (delta = {delta})")
    return bits


MODULATION_MENU = {"1": "PCM - Pulse Code Modulation", "2": "DM  - Delta Modulation"}
MODULATION_FLOWS = {"1": pcm_flow, "2": dm_flow}
SAMPLES_PER_CYCLE = {"1": 10, "2": 50}      # default sampling: PCM 10 per cycle, DM 50


def analog_flow():
    method = ask_choice("Choose the modulation technique:", MODULATION_MENU)
    source = ask_choice("Analog input:", ANALOG_MENU)
    signal = ANALOG_SOURCES[source](SAMPLES_PER_CYCLE[method])
    bits = MODULATION_FLOWS[method](signal)
    show_data(bits)
    if ask_yes_no("\nFeed this digital data into a line encoder?"):
        line_coding(bits)


#  main
INPUT_MENU = {"1": "Digital input", "2": "Analog input"}
INPUT_FLOWS = {"1": digital_flow, "2": analog_flow}


def main():
    print("=== Digital Signal Encoder / Decoder ===")
    while True:
        choice = ask_choice("Input type:", INPUT_MENU)
        INPUT_FLOWS[choice]()
        if not ask_yes_no("\nRun again?"):
            break


if __name__ == "__main__":
    main()