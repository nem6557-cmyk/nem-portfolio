"""
CFD Next Gen — consolidated chamber geometry (single source of truth)
====================================================================
All values CONFIRMED by Noor from the drawing + messages:
  - tubes: copper, OD 4.76 mm, ID 3.137 mm, staggered, 33 total
  - chip : plain copper, 34.5 x 32 mm face, pointing +Z, at chamber floor
  - walls: aluminum
  - fluid: 40% fill ~ 10 mm liquid height above the chip surface
  - one symmetric pass, inlet/outlet interchangeable

Tube centroids are read from the STEP so the submerged/vapor split is exact.
Remaining operating inputs (NOT geometry): working fluid, chamber pressure,
coolant flow rate -> needed to run the coupled chamber.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import gmsh

STEP = "/mnt/user-data/uploads/CFD_Next_Gen.step"

# ----------------------------------------------------------------------
# CONFIRMED GEOMETRY
# ----------------------------------------------------------------------
TUBE_OD   = 4.76e-3
TUBE_ID   = 3.137e-3
TUBE_WALL = (TUBE_OD - TUBE_ID) / 2          # 0.8115 mm
N_TUBES   = 33
PITCH_T   = 11.17e-3                          # transverse pitch (staggered)
K_TUBE    = 385.0                             # copper
K_WALL    = 237.0                             # aluminum enclosure
CHIP_X, CHIP_Y = 34.5e-3, 32.0e-3            # heated face, pointing +Z
FILL_HEIGHT = 10.0e-3                         # ~40% of available height


# ----------------------------------------------------------------------
def get_tube_centroids(step=STEP):
    """Read the 33 tube bodies (size signature 5.6 x 95 x 5.6 mm) and return
    centroids [mm] and the overall tube axial length."""
    gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
    gmsh.open(step); gmsh.model.occ.synchronize()
    cents, length, chip_top = [], None, None
    for (dim, tag) in gmsh.model.getEntities(3):
        bb = gmsh.model.getBoundingBox(dim, tag)
        dx, dy, dz = bb[3]-bb[0], bb[4]-bb[1], bb[5]-bb[2]
        cx, cy, cz = (bb[0]+bb[3])/2, (bb[1]+bb[4])/2, (bb[2]+bb[5])/2
        sig = (round(dx, 1), round(dy, 1), round(dz, 1))
        if sig == (5.6, 95.0, 5.6):
            cents.append((cx, cy, cz)); length = dy
        if sig == (55.0, 55.0, 8.5):
            chip_top = bb[5]                  # top face z of heater block
    gmsh.finalize()
    return np.array(cents), length, chip_top


def wetted_fraction(z_c, r, z_fill):
    """Submerged area fraction of a horizontal circle (radius r, centroid z_c)."""
    d = z_fill - z_c
    if d >= r:  return 1.0
    if d <= -r: return 0.0
    A_above = r**2 * np.arccos(d / r) - d * np.sqrt(r**2 - d**2)
    return 1.0 - A_above / (np.pi * r**2)


# ----------------------------------------------------------------------
def main():
    cents, L_tube, chip_top = get_tube_centroids()
    r = TUBE_OD / 2 * 1e3                      # mm
    z = cents[:, 2]
    chip_top = chip_top if chip_top is not None else 0.75
    z_fill = chip_top + FILL_HEIGHT * 1e3      # fill line [mm]

    # derived areas
    A_flow_tube = np.pi/4 * TUBE_ID**2
    A_flow_tot  = N_TUBES * A_flow_tube
    L = (L_tube if L_tube else 95.0) * 1e-3
    A_ext_tube  = np.pi * TUBE_OD * L
    A_ext_tot   = N_TUBES * A_ext_tube
    A_int_tot   = N_TUBES * np.pi * TUBE_ID * L
    A_chip      = CHIP_X * CHIP_Y

    # submerged split
    fr = np.array([wetted_fraction(zc, r, z_fill) for zc in z])
    n_wet  = int(np.sum(fr > 0.99))
    n_part = int(np.sum((fr > 0.01) & (fr <= 0.99)))
    n_dry  = int(np.sum(fr <= 0.01))
    wet_area_frac = np.sum(fr) / N_TUBES       # area-weighted submerged fraction

    print("="*68)
    print("CFD NEXT GEN — LOCKED CHAMBER GEOMETRY")
    print("="*68)
    print(f"Tubes (copper): OD {TUBE_OD*1e3:.3f} mm, ID {TUBE_ID*1e3:.3f} mm, "
          f"wall {TUBE_WALL*1e3:.3f} mm, n = {N_TUBES} staggered")
    print(f"   axial length {L*1e3:.1f} mm, transverse pitch {PITCH_T*1e3:.2f} mm")
    print(f"   flow area/tube {A_flow_tube*1e6:.3f} mm^2, total flow area {A_flow_tot*1e6:.1f} mm^2")
    print(f"   internal area total {A_int_tot*1e4:.1f} cm^2, external area total {A_ext_tot*1e4:.1f} cm^2")
    print(f"Chip (plain copper): {CHIP_X*1e3:.1f} x {CHIP_Y*1e3:.1f} mm, "
          f"area {A_chip*1e4:.2f} cm^2, face +Z at z = {chip_top:.2f} mm")
    print(f"Walls: aluminum (k = {K_WALL:.0f} W/mK)")
    print(f"\nFill line at z = {z_fill:.2f} mm  ({FILL_HEIGHT*1e3:.0f} mm above chip, ~40%):")
    print(f"   tube rows at z = {sorted(set(np.round(z,1)))}")
    print(f"   fully submerged tubes : {n_wet}")
    print(f"   straddling fill line  : {n_part}")
    print(f"   in vapor space        : {n_dry}")
    print(f"   area-weighted submerged fraction of the bank: {wet_area_frac*100:.1f}%")
    print(f"   -> submerged tubes do pool-side natural convection,")
    print(f"      vapor-space tubes do film condensation (the regime split)")
    print("="*68)
    print("Still needed to RUN the coupled chamber (operating inputs, not geometry):")
    print("   1) working fluid: water or HFE-7000")
    print("   2) chamber pressure (e.g. 12 kPa for water -> T_sat 49.4 C)")
    print("   3) coolant flow rate (total, split over the 33 tubes)")
    print("="*68)

    # figure: front view (X-Z), tubes colored by wet/partial/dry
    fig, ax = plt.subplots(figsize=(11, 4.6))
    for (cx, cy, cz), f in zip(cents, fr):
        c = "tab:blue" if f > 0.99 else ("tab:cyan" if f > 0.01 else "0.6")
        ax.add_patch(Circle((cx, cz), r, facecolor=c, edgecolor="k", lw=0.5))
        ax.add_patch(Circle((cx, cz), TUBE_ID/2*1e3, facecolor="white", edgecolor="k", lw=0.3))
    # chip / heater block
    ax.add_patch(Rectangle((-27.5, chip_top-8.5), 55, 8.5, facecolor="0.8", edgecolor="k"))
    ax.plot([-CHIP_X*1e3/2, CHIP_X*1e3/2], [chip_top, chip_top], color="firebrick", lw=4,
            label="heated chip face (+Z)")
    # fluid
    xmin, xmax = -40, 40
    ax.axhline(z_fill, color="navy", ls="--", lw=1.5)
    ax.fill_between([xmin, xmax], -8.5+chip_top, z_fill, color="tab:blue", alpha=0.10)
    ax.text(xmax-1, z_fill+0.4, f"fill line  z={z_fill:.1f} mm", ha="right", color="navy", fontsize=9)
    ax.set_xlim(xmin, xmax); ax.set_ylim(chip_top-10, 22)
    ax.set_aspect("equal"); ax.set_xlabel("X [mm]"); ax.set_ylabel("Z [mm]")
    ax.set_title(f"Front view (X-Z): {n_wet} tubes submerged, {n_part} straddling, "
                 f"{n_dry} in vapor at 40% fill")
    # legend proxies
    from matplotlib.lines import Line2D
    proxies = [Line2D([0],[0], marker='o', color='w', markerfacecolor='tab:blue', label='submerged', markersize=10),
               Line2D([0],[0], marker='o', color='w', markerfacecolor='tab:cyan', label='straddling', markersize=10),
               Line2D([0],[0], marker='o', color='w', markerfacecolor='0.6', label='vapor space', markersize=10),
               Line2D([0],[0], color='firebrick', lw=4, label='chip face')]
    ax.legend(handles=proxies, fontsize=8, loc="upper right", ncol=2)
    fig.tight_layout(); fig.savefig("/home/claude/chamber_fill.png", dpi=140); plt.close(fig)
    print("\nFigure: /home/claude/chamber_fill.png")


if __name__ == "__main__":
    main()
