"""
True 3D isometric render of the chamber STEP, colored by component.
Meshes the actual OCC surfaces (so it is the real geometry, not a sketch) and
draws them with matplotlib 3D. Enclosure/plates are made translucent so the
tube bank and chip are visible inside.
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import gmsh

STEP = "/mnt/user-data/uploads/CFD_Next_Gen.step"

# component styling by size signature (dx,dy,dz rounded to 0.1 mm)
STYLE = {
    (5.6, 95.0, 5.6):   dict(color="#b87333", alpha=1.0,  name="copper tubes"),
    (55.0, 55.0, 8.5):  dict(color="#a01818", alpha=1.0,  name="chip / heater block"),
    (85.0, 12.5, 24.0): dict(color="#d4a017", alpha=0.95, name="coolant headers"),
}
DEFAULT_PLATE = dict(color="#9bb0c1", alpha=0.12, name="aluminum enclosure")


def render(step=STEP, out="/home/claude/chamber_iso.png", size=2.5):
    gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
    gmsh.open(step)
    gmsh.option.setNumber("Mesh.MeshSizeMax", size)
    gmsh.option.setNumber("Mesh.MeshSizeMin", size * 0.3)
    gmsh.model.mesh.generate(2)

    nodeTags, coord, _ = gmsh.model.mesh.getNodes()
    coord = coord.reshape(-1, 3)
    idx = {t: i for i, t in enumerate(nodeTags)}

    # group triangles by style
    buckets = {}   # key -> list of triangles (Nx3x3)
    for (dim, vtag) in gmsh.model.getEntities(3):
        bb = gmsh.model.getBoundingBox(dim, vtag)
        sig = (round(bb[3]-bb[0], 1), round(bb[4]-bb[1], 1), round(bb[5]-bb[2], 1))
        st = STYLE.get(sig, DEFAULT_PLATE)
        key = (st["color"], st["alpha"])
        surfs = gmsh.model.getBoundary([(dim, vtag)], oriented=False, recursive=False)
        for (sd, stag) in surfs:
            et, etag, en = gmsh.model.mesh.getElements(2, abs(stag))
            for typ, nodes in zip(et, en):
                if typ != 2:           # 2 = 3-node triangle
                    continue
                tri = nodes.reshape(-1, 3)
                verts = np.array([[coord[idx[n]] for n in t] for t in tri])
                buckets.setdefault(key, []).append(verts)

    env = gmsh.model.getBoundingBox(-1, -1)
    gmsh.finalize()

    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection="3d")
    ls = matplotlib.colors.LightSource(azdeg=-50, altdeg=35)
    for (color, alpha), tris in buckets.items():
        tris = np.concatenate(tris, axis=0)
        pc = Poly3DCollection(tris, alpha=alpha, linewidths=0)
        # simple shading by face normal z-component
        if alpha > 0.5:
            n = np.cross(tris[:, 1]-tris[:, 0], tris[:, 2]-tris[:, 0])
            nz = np.abs(n[:, 2]) / (np.linalg.norm(n, axis=1) + 1e-9)
            shade = 0.55 + 0.45 * nz
            base = np.array(matplotlib.colors.to_rgb(color))
            pc.set_facecolor(np.clip(base[None, :] * shade[:, None], 0, 1))
        else:
            pc.set_facecolor(color)
        ax.add_collection3d(pc)

    ax.set_xlim(env[0], env[3]); ax.set_ylim(env[1], env[4]); ax.set_zlim(env[2], env[5])
    ax.set_box_aspect((env[3]-env[0], env[4]-env[1], env[5]-env[2]))
    ax.view_init(elev=22, azim=-55)
    ax.set_xlabel("X [mm]"); ax.set_ylabel("Y [mm]"); ax.set_zlabel("Z [mm]")
    ax.set_title("CFD Next Gen — chamber isometric (33 Cu tubes, chip, headers, see-through walls)")
    # legend
    from matplotlib.patches import Patch
    seen = {}
    for sig, st in {**STYLE, ('p',): DEFAULT_PLATE}.items():
        seen[st["name"]] = st["color"]
    ax.legend(handles=[Patch(facecolor=c, label=n) for n, c in seen.items()],
              loc="upper left", fontsize=9)
    fig.tight_layout(); fig.savefig(out, dpi=150); plt.close(fig)
    return out, len(buckets)


if __name__ == "__main__":
    out, ng = render()
    print("wrote", out)
