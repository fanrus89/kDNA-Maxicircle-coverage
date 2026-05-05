# ─────────────────────────────────────────────
#  MAXICIRCLE COVERAGE - ONT + ILLUMINA
# ─────────────────────────────────────────────

import subprocess
import sys

def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

install("pandas")
install("matplotlib")
install("numpy")

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ─────────────────────────────────────────────
#  DETECT ENVIRONMENT (Colab or local)
# ─────────────────────────────────────────────
def is_colab():
    try:
        import google.colab
        return True
    except ImportError:
        return False

# ─────────────────────────────────────────────
#  REQUEST INPUT FILES FROM USER
# ─────────────────────────────────────────────
def request_file(description):
    """Ask the user for a file path and verify it exists."""
    while True:
        filename = input(f"\nEnter the {description} coverage file (e.g. file.tabular): ").strip()
        if not filename:
            print("[WARN] No filename entered, please try again.")
            continue
        if not os.path.isfile(filename):
            print(f"[ERROR] File '{filename}' not found in current directory.")
            print(f"        Current directory: {os.getcwd()}")
            retry = input("        Try another filename? (y/n): ").strip().lower()
            if retry != "y":
                sys.exit("[INFO] Exiting.")
        else:
            print(f"[OK] File found: {filename}")
            return filename


def upload_files_colab():
    """In Colab, allow uploading files from the local machine."""
    from google.colab import files

    print("\n[INFO] Upload your ONT coverage file (.tabular):")
    uploaded = files.upload()
    ont_file = list(uploaded.keys())[0]
    print(f"[OK] ONT file: {ont_file}")

    print("\n[INFO] Upload your Illumina coverage file (.tabular):")
    uploaded = files.upload()
    illumina_file = list(uploaded.keys())[0]
    print(f"[OK] Illumina file: {illumina_file}")

    return ont_file, illumina_file


# ─────────────────────────────────────────────
#  SMOOTHING FUNCTION (moving average)
# ─────────────────────────────────────────────
def smooth(df, window=200):
    df = df.sort_values("pos").copy()
    df["smoothed"] = df["depth"].rolling(window, center=True, min_periods=1).mean()
    return df


# ─────────────────────────────────────────────
#  HORIZONTAL GUIDE LINES
# ─────────────────────────────────────────────
def add_horizontal_lines(ax, step, max_val):
    for y in np.arange(step, max_val, step):
        ax.axhline(y, color="lightgray", linestyle="--", linewidth=1)


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():

    # Get files depending on environment
    if is_colab():
        ont_file, illumina_file = upload_files_colab()
    else:
        ont_file      = request_file("ONT")
        illumina_file = request_file("Illumina")

    # Read data
    print("\n[INFO] Reading files...")
    df_ont      = pd.read_csv(ont_file,      sep="\t", comment="#", header=None,
                              names=["chr", "pos", "depth"])
    df_illumina = pd.read_csv(illumina_file, sep="\t", comment="#", header=None,
                              names=["chr", "pos", "depth"])

    # Apply smoothing
    df_ont      = smooth(df_ont,      window=200)
    df_illumina = smooth(df_illumina, window=200)

    # Calculate max coverage automatically from data
    max_ont      = df_ont["smoothed"].max()
    max_illumina = df_illumina["smoothed"].max()
    print(f"[INFO] Max ONT coverage:      {max_ont:.1f}x")
    print(f"[INFO] Max Illumina coverage: {max_illumina:.1f}x")

    # Create figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(22, 10), sharex=True,
                                   gridspec_kw={"hspace": 0.25})

    # Font parameters
    title_fontsize = 26
    label_fontsize = 22
    tick_fontsize  = 18

    # ONT TRACK
    ax1.fill_between(df_ont["pos"], df_ont["smoothed"], color="#c084f5", step="mid")
    add_horizontal_lines(ax1, step=max_ont / 5, max_val=max_ont * 1.1)
    ax1.set_ylabel("ONT coverage", fontsize=label_fontsize)
    ax1.set_title("Sequencing depth across the maxicircle",
                  fontsize=title_fontsize, pad=20)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.spines["bottom"].set_position("zero")
    ax1.tick_params(axis="x", labelbottom=False, labelsize=tick_fontsize)
    ax1.tick_params(axis="y", labelsize=tick_fontsize)
    ax1.set_xlim(left=0, right=df_ont["pos"].max())
    ax1.set_ylim(bottom=0)

    # ILLUMINA TRACK
    ax2.fill_between(df_illumina["pos"], df_illumina["smoothed"],
                     color="#5fa8d3", step="mid")
    add_horizontal_lines(ax2, step=max_illumina / 5, max_val=max_illumina * 1.1)
    ax2.set_ylabel("Illumina coverage", fontsize=label_fontsize)
    ax2.set_xlabel("Position in maxicircle (bp)", fontsize=label_fontsize, labelpad=15)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.spines["bottom"].set_position("zero")
    ax2.tick_params(axis="x", labelsize=tick_fontsize)
    ax2.tick_params(axis="y", labelsize=tick_fontsize)
    ax2.set_xlim(left=0, right=df_illumina["pos"].max())
    ax2.set_ylim(0, max_illumina * 1.05)

    # Save figure
    output_file = "maxicircle_coverage_smoothed_guides.png"
    plt.tight_layout()
    plt.savefig(output_file, dpi=1000, format="png")
    plt.show()
    print(f"\n[OK] Figure saved as: {output_file}")

    # Download in Colab
    if is_colab():
        from google.colab import files
        files.download(output_file)
        print("[OK] Download started.")


if __name__ == "__main__":
    main()
