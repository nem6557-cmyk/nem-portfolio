"""
Clean schematic isometric of the chamber for the modeling view:
- 33 copper tubes as parametric cylinders at their real STEP positions
- tubes colored by regime at 40% fill (submerged / straddling / vapor)
- chip face, translucent fluid plane, enclosure envelope as edges
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
import gmsh

STEP = "/mnt/user-data/uploads/CFD_Next_Gen.step"
OD, ID = 4.76, 3.137
FILL_ABOVE_CHIP = 10.0


def tube_centroids():
    gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
    gmsh.open(STEP); gmsh.model.occ.synchronize()
    cents, ylen, chip_top, env = [], 95.0, 0.75, None
    for (dim, tag) in gmsh.model.getEntities(3):
        bb = gmsh.model.getBoundingBox(dim, tag)
        sig = (round(bb[3]-bb[0],1), round(bb[4]-bb[1],1), round(bb[5]-bb[2],1))
        if sig == (5.6, 95.0, 5.6):
            cents.append(((bb[0]+bb[3])/2, bb[1], bb[4], (bb[2]+bb[5])/2)); ylen = bb[4]-bb[1]
        if sig == (55.0, 55.0, 8.5):
            chip_top = bb[5]
    env = gmsh.model.getBoundingBox(-1, -1)
    gmsh.finalize()
    return cents, chip_top, env


def wet_frac(z_c, r, z_fill):
    d = z_fill - z_c
    if d >= r: return 1.0
    if d <= -r: return 0.0
    return 1.0 - (r**2*np.arccos(d/r) - d*np.sqrt(r**2-d**2))/(np.pi*r**2)


def box_edges(ax, env, color="0.55"):
    x0,y0,z0,x1,y1,z1 = env[0],env[1],env[2],env[3],env[4],env[5]
    pts = np.array([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],
                    [x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]])
    E = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
    ax.add_collection3d(Line3DCollection([[pts[a],pts[b]] for a,b in E],
                        colors=color, linewidths=1.0, linestyles="--"))


def main(out="/home/claude/chamber_iso_clean.png"):
    cents, chip_top, env = tube_centroids()
    r = OD/2; z_fill = chip_top + FILL_ABOVE_CHIP

    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection="3d")

    th = np.linspace(0, 2*np.pi, 28)
    cmap = {"wet": "#1f77b4", "part": "#17becf", "dry": "#9aa0a6"}
    for (cx, y0, y1, cz) in cents:
        f = wet_frac(cz, r, z_fill)
        col = cmap["wet"] if f > 0.99 else (cmap["part"] if f > 0.01 else cmap["dry"])
        Y, TH = np.meshgrid([y0, y1], th)
        X = cx + r*np.cos(TH); Z = cz + r*np.sin(TH)
        ax.plot_surface(X, Y, Z, color=col, linewidth=0, antialiased=True, shade=True)

    # chip face (+Z) on the floor
    cw, cd = 34.5/2, 32/2
    chip = [[(-cw,-cd,chip_top),(cw,-cd,chip_top),(cw,cd,chip_top),(-cw,cd,chip_top)]]
    ax.add_collection3d(Poly3DCollection(chip, facecolor="#c0392b", edgecolor="k", lw=1))
    ax.text(0, 0, chip_top+1.5, "chip 34.5×32 (+Z)", color="#c0392b", fontsize=9, ha="center")

    # fluid fill plane
    fx, fy = 37, 48
    fluid = [[(-fx,-fy,z_fill),(fx,-fy,z_fill),(fx,fy,z_fill),(-fx,fy,z_fill)]]
    ax.add_collection3d(Poly3DCollection(fluid, facecolor="#2e86de", alpha=0.12, edgecolor="none"))
    ax.text(fx, fy, z_fill+0.5, f"fill line  z={z_fill:.1f} mm (40%)", color="navy", fontsize=9)

    box_edges(ax, env)

    ax.set_xlim(env[0], env[3]); ax.set_ylim(env[1], env[4]); ax.set_zlim(env[2], env[5])
    ax.set_box_aspect((env[3]-env[0], env[4]-env[1], env[5]-env[2]))
    ax.view_init(elev=20, azim=-60)
    ax.set_xlabel("X [mm]"); ax.set_ylabel("Y [mm]"); ax.set_zlabel("Z [mm]")
    ax.set_title("Chamber isometric (modeling view): tube regimes at 40% fill")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=cmap["wet"], label="submerged (13)"),
                       Patch(facecolor=cmap["part"], label="straddling (7)"),
                       Patch(facecolor=cmap["dry"], label="vapor space (13)"),
                       Patch(facecolor="#c0392b", label="chip face")],
              loc="upper left", fontsize=9)
    fig.tight_layout(); fig.savefig(out, dpi=150); plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    main()
