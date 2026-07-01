"""
inertia.py
==========
Compute full rigid-body inertial properties (mass, center of mass, inertia
tensor) for robot links directly from geometry and material density, then
express them in the MuJoCo body frame.

Why this exists
---------------
Most hand-written robot models use crude inertial data: an identity inertia
tensor, a guessed diagonal, or the value MuJoCo auto-derives from a bounding
primitive. That is fine for cartoons and terrible for dynamics. The joint
torques a manipulator needs, the way it swings under gravity, and the settling
behaviour after a contact are all governed by the inertia tensor. If the tensor
is wrong, every downstream controller and every learned policy is trained on a
lie, and the sim-to-real gap widens.

This module treats each link the way a mechanical engineer would: as a real
part with a material and a cross section. The inertia is derived analytically
for a hollow cylinder (a tube, which is what real arm links usually are), then
rotated into the body frame so it can be dropped straight into an MJCF
<inertial> element as a full inertia tensor.

Convention
----------
MuJoCo's <inertial fullinertia="..."> expects six numbers ordered
(Ixx, Iyy, Izz, Ixy, Ixz, Iyz), taken about the center of mass, expressed in
the body frame. That is exactly what `link_inertial` returns.

Units are SI throughout: metres, kilograms, seconds. Densities in kg/m^3.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


# A few common structural materials (kg/m^3). Values a designer would read off
# a datasheet. Aluminium 6061 is the default arm material here.
MATERIAL_DENSITY = {
    "aluminium_6061": 2700.0,
    "steel_1018": 7870.0,
    "titanium_ti6al4v": 4430.0,
    "abs_plastic": 1040.0,
    "carbon_fiber": 1600.0,
}


@dataclass
class MassProperties:
    """Mass properties of a single part, resolved in the body frame."""
    mass: float                # kg
    com: np.ndarray            # (3,) center of mass in body frame, metres
    inertia: np.ndarray        # (3,3) inertia tensor about the COM, body frame

    def fullinertia(self) -> tuple[float, ...]:
        """Return (Ixx, Iyy, Izz, Ixy, Ixz, Iyz) for an MJCF <inertial> tag."""
        I = self.inertia
        return (I[0, 0], I[1, 1], I[2, 2], I[0, 1], I[0, 2], I[1, 2])


def hollow_cylinder_principal(mass: float, r_out: float, r_in: float,
                              length: float) -> np.ndarray:
    """Principal moments of a hollow cylinder about its own COM.

    The cylinder axis is taken as the local x-axis. Because the cross section
    is circular, the two transverse moments are equal, so the choice of the
    transverse axes is irrelevant.

    Returns diag [I_axial, I_transverse, I_transverse].
    """
    r2 = r_out ** 2 + r_in ** 2
    i_axial = 0.5 * mass * r2
    i_transverse = (1.0 / 12.0) * mass * (3.0 * r2 + length ** 2)
    return np.array([i_axial, i_transverse, i_transverse])


def _frame_from_axis(axis: np.ndarray) -> np.ndarray:
    """Build an orthonormal rotation whose first column is `axis`.

    The remaining two columns span the transverse plane. Their orientation is
    arbitrary, which is acceptable here because transverse inertia is isotropic
    for a circular cross section.
    """
    x = axis / np.linalg.norm(axis)
    # Pick any vector not parallel to x to seed the cross product.
    seed = np.array([0.0, 0.0, 1.0]) if abs(x[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    y = np.cross(seed, x)
    y /= np.linalg.norm(y)
    z = np.cross(x, y)
    return np.column_stack([x, y, z])


def rotate_inertia(principal_diag: np.ndarray, axis: np.ndarray) -> np.ndarray:
    """Rotate a diagonal (principal) inertia so the local x-axis points along
    `axis`, expressed in the body frame: I_body = R * diag * R^T.
    """
    R = _frame_from_axis(axis)
    return R @ np.diag(principal_diag) @ R.T


def hollow_cylinder_link(start: np.ndarray, end: np.ndarray, r_out: float,
                         wall: float, density: float) -> MassProperties:
    """Full mass properties of a tubular link running from `start` to `end`.

    Parameters
    ----------
    start, end : (3,) endpoints of the link axis in the body frame (metres).
                 By convention the body origin sits at the proximal joint, so
                 `start` is usually the origin.
    r_out      : outer radius of the tube (metres).
    wall       : wall thickness (metres). Inner radius = r_out - wall.
    density    : material density (kg/m^3).
    """
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    r_in = max(r_out - wall, 0.0)

    axis_vec = end - start
    length = float(np.linalg.norm(axis_vec))
    volume = np.pi * (r_out ** 2 - r_in ** 2) * length
    mass = density * volume

    com = 0.5 * (start + end)
    principal = hollow_cylinder_principal(mass, r_out, r_in, length)
    inertia = rotate_inertia(principal, axis_vec)
    return MassProperties(mass=mass, com=com, inertia=inertia)


def solid_sphere(mass: float, radius: float,
                 com: np.ndarray | None = None) -> MassProperties:
    """Mass properties of a solid sphere (used for the payload)."""
    i = 0.4 * mass * radius ** 2
    com = np.zeros(3) if com is None else np.asarray(com, dtype=float)
    return MassProperties(mass=mass, com=com, inertia=np.diag([i, i, i]))


# ---------------------------------------------------------------------------
# Standalone report: print a mass-properties table like a CAD tool would.
# ---------------------------------------------------------------------------
def _demo_report() -> None:
    rho = MATERIAL_DENSITY["aluminium_6061"]
    links = {
        "link1_shoulder_riser": hollow_cylinder_link(
            [0, 0, 0], [0, 0, 0.15], r_out=0.025, wall=0.004, density=rho),
        "link2_upper_arm": hollow_cylinder_link(
            [0, 0, 0], [0.30, 0, 0], r_out=0.020, wall=0.003, density=rho),
        "link3_forearm": hollow_cylinder_link(
            [0, 0, 0], [0.25, 0, 0], r_out=0.018, wall=0.003, density=rho),
    }
    payload = solid_sphere(mass=0.50, radius=0.03)

    print("=" * 74)
    print("Mass properties, aluminium 6061 tubes (SI units, about link COM)")
    print("=" * 74)
    header = f"{'link':22s}{'mass[kg]':>10s}{'Ixx':>10s}{'Iyy':>10s}{'Izz':>10s}"
    print(header)
    print("-" * 74)
    total = 0.0
    for name, mp in links.items():
        fi = mp.fullinertia()
        total += mp.mass
        print(f"{name:22s}{mp.mass:10.4f}{fi[0]:10.2e}{fi[1]:10.2e}{fi[2]:10.2e}")
    print(f"{'payload_sphere':22s}{payload.mass:10.4f}"
          f"{payload.fullinertia()[0]:10.2e}"
          f"{payload.fullinertia()[1]:10.2e}"
          f"{payload.fullinertia()[2]:10.2e}")
    total += payload.mass
    print("-" * 74)
    print(f"{'TOTAL moving mass':22s}{total:10.4f} kg")
    print("=" * 74)


if __name__ == "__main__":
    _demo_report()
