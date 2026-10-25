"""CPython 3, zero-thickness quasi-static microstrip starting estimate.
Does NOT model coplanar grounds, solder mask, roughness, or copper thickness.
"""
import argparse
import math


def impedance(width_mm, height_mm, er):
    if width_mm <= 0 or height_mm <= 0 or er < 1:
        raise ValueError("Need w>0, h>0, er>=1")
    u = width_mm / height_mm
    correction = 0.04 * (1 - u) ** 2 if u <= 1 else 0
    ee = (er + 1) / 2 + (er - 1) / 2 * ((1 + 12 / u) ** -0.5 + correction)
    if u <= 1:
        return 60 / math.sqrt(ee) * math.log(8 / u + u / 4)
    return 120 * math.pi / (math.sqrt(ee) * (u + 1.393 + 0.667 * math.log(u + 1.444)))


def width_for_z0(height_mm, er, z0=50):
    if height_mm <= 0 or er < 1 or z0 <= 0:
        raise ValueError("Invalid stackup/impedance")
    low, high = height_mm * 1e-6, height_mm * 1e3
    for _ in range(100):
        mid = (low + high) / 2
        if impedance(mid, height_mm, er) > z0:
            low = mid
        else:
            high = mid
    return (low + high) / 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--h-mm", type=float, required=True)
    parser.add_argument("--er", type=float, required=True)
    parser.add_argument("--z0", type=float, default=50)
    args = parser.parse_args()
    print("Estimated width: %.4f mm; validate actual cross section in a field solver" %
          width_for_z0(args.h_mm, args.er, args.z0))
