"""CPython 3: plot real HFSS real/imag S11 CSV; no fabricated RF data.

Usage: python scripts/postprocess_s11.py build/s11_ri.csv --bands 902:928
Optional dual-band acceptance: --bands 863:870 902:928
Exit 0: sampled specification passes; 2: sampled specification fails.
"""
import argparse
import csv
import math
import re
from pathlib import Path


def read_hfss_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        freq_cols = [i for i, h in enumerate(header) if re.search(r"\bFreq\b", h)]
        real_cols = [i for i, h in enumerate(header) if "re(S(" in h]
        imag_cols = [i for i, h in enumerate(header) if "im(S(" in h]
        if tuple(map(len, (freq_cols, real_cols, imag_cols))) != (1, 1, 1):
            raise ValueError("Export exactly Freq, re(S(port,port)), im(S(port,port))")
        fi, ri, ii = freq_cols[0], real_cols[0], imag_cols[0]
        unit = re.search(r"\[(GHz|MHz|kHz|Hz)\]", header[fi])
        if not unit:
            raise ValueError("Frequency column must state [Hz], [kHz], [MHz], or [GHz]")
        scale = {"Hz": 1e-6, "kHz": 1e-3, "MHz": 1, "GHz": 1e3}[unit.group(1)]
        data = []
        for row in reader:
            if not row or not any(row):
                continue
            freq = float(row[fi]) * scale
            value = complex(float(row[ri]), float(row[ii]))
            if not all(math.isfinite(x) for x in (freq, value.real, value.imag)) or freq <= 0:
                raise ValueError("Invalid numeric sample")
            data.append((freq, value))
    data.sort(key=lambda x: x[0])
    if len(data) < 2 or any(b[0] <= a[0] for a, b in zip(data, data[1:])):
        raise ValueError("Need unique increasing frequencies: export ONE nominal variation")
    return data


def db(value):
    return 20 * math.log10(max(abs(value), 1e-15))


def assess(data, bands, max_gap=1.01):
    results = []
    for lo, hi in bands:
        if lo > hi:
            raise ValueError("Reversed band")
        samples = [(f, g) for f, g in data if lo <= f <= hi]
        # Require measured/exported edges, not extrapolated acceptance values.
        if not samples or abs(samples[0][0] - lo) > 1e-6 or abs(samples[-1][0] - hi) > 1e-6:
            raise ValueError("Export exact band-edge frequencies %.6g and %.6g MHz" % (lo, hi))
        if any(b[0] - a[0] > max_gap for a, b in zip(samples, samples[1:])):
            raise ValueError("Band samples are too sparse for the selected maximum gap")
        worst = max(samples, key=lambda x: abs(x[1]))
        results.append((lo, hi, worst[0], db(worst[1]), db(worst[1]) <= -10))
    return results


def smith_grid(ax):
    import numpy as np
    theta = np.linspace(0, 2 * np.pi, 600)
    ax.plot(np.cos(theta), np.sin(theta), color="#768399", lw=0.9)
    for resistance in (0.2, 0.5, 1, 2, 5):
        center = resistance / (1 + resistance)
        radius = 1 / (1 + resistance)
        ax.plot(center + radius * np.cos(theta), radius * np.sin(theta),
                color="#d5dde8", lw=0.6)
    for reactance in (0.2, 0.5, 1, 2, 5):
        for sign in (-1, 1):
            x = reactance * sign
            xx = 1 + np.cos(theta) / abs(x)
            yy = 1 / x + np.sin(theta) / abs(x)
            outside = xx * xx + yy * yy > 1.001
            xx[outside], yy[outside] = np.nan, np.nan
            ax.plot(xx, yy, color="#d5dde8", lw=0.6)
    ax.axhline(0, color="#d5dde8", lw=0.6)
    ax.scatter([0], [0], c="#25344b", s=15)
    ax.text(0.03, -0.08, "50 + j0 Ω", fontsize=9)
    ax.set_aspect("equal")
    ax.set_xlim(-1.08, 1.08)
    ax.set_ylim(-1.08, 1.08)
    ax.axis("off")


def plot(data, bands, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False})
    f, g = zip(*data)
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.8), layout="constrained")
    ax = axes[0]
    ax.plot(f, [db(x) for x in g], color="#047f91", lw=2.2)
    ax.axhline(-10, color="#d05247", ls="--", lw=1.3, label="−10 dB requirement")
    for lo, hi in bands:
        ax.axvspan(lo, hi, color="#047f91", alpha=0.08)
    ax.set(xlabel="Frequency (MHz)", ylabel="S11 (dB)", xlim=(800, 1000),
           title="Input match · 50 Ω reference")
    ax.grid(alpha=0.18)
    ax.legend(frameon=False, loc="lower right")
    smith_grid(axes[1])
    axes[1].plot([x.real for x in g], [x.imag for x in g], color="#047f91", lw=2)
    axes[1].set_title("Smith chart · normalized to 50 Ω")
    for target, color in ((868, "#b34f87"), (915, "#db7b27")):
        exact = [(freq, value) for freq, value in data if abs(freq - target) < 1e-6]
        if exact:
            freq, value = exact[0]
            ax.scatter([freq], [db(value)], color=color, zorder=5)
            ax.annotate("%d MHz\n%.1f dB" % (target, db(value)), (freq, db(value)),
                        xytext=(8, -35 if db(value) > -20 else 12),
                        textcoords="offset points", fontsize=9)
            axes[1].scatter([value.real], [value.imag], color=color, zorder=5)
            axes[1].annotate("%d MHz" % target, (value.real, value.imag),
                             xytext=(8, 8), textcoords="offset points", fontsize=9)
    fig.suptitle("LoRa antenna | HFSS exported S-parameters", fontsize=16, weight="bold")
    fig.text(0.5, -0.015, "Acceptance applies to exported samples; verify with discrete solves and mesh convergence.",
             ha="center", fontsize=9, color="#667085")
    output.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(output / ("s11_smith_50ohm." + ext), dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv", type=Path)
    p.add_argument("--bands", nargs="+", default=["902:928"])
    p.add_argument("--output", type=Path, default=Path("build/plots"))
    p.add_argument("--max-gap-mhz", type=float, default=1.01)
    args = p.parse_args()
    bands = [tuple(map(float, b.split(":"))) for b in args.bands]
    if any(len(b) != 2 for b in bands) or args.max_gap_mhz <= 0:
        p.error("Use LOW:HIGH bands and a positive maximum gap")
    data = read_hfss_csv(args.csv)
    result = assess(data, bands, args.max_gap_mhz)
    plot(data, bands, args.output)
    for lo, hi, freq, worst, passed in result:
        print("%.3f-%.3f MHz: worst %.3f dB at %.3f MHz: %s (sampled)" %
              (lo, hi, worst, freq, "PASS" if passed else "FAIL"))
    raise SystemExit(0 if all(r[-1] for r in result) else 2)


if __name__ == "__main__":
    main()
