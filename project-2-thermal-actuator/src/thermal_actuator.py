"""
thermal_actuator.py
===================
A thermally coupled actuator model for closing a sim-to-real gap that friction
and damping identification do not touch: sustained-torque motor derating.

The gap
-------
Robot joint motors have a peak torque they can hit briefly and a much lower
torque they can hold forever. The difference is heat. Torque is proportional to
current, and copper loss scales with current squared, so a joint asked to hold
a heavy pose dissipates I^2 R in the windings. The winding heats, the drive
derates torque to protect the insulation, and the achievable torque falls. A
simulator that treats peak torque as always available is optimistic: a
controller or learned policy tuned against it will command holds the real
hardware cannot sustain, and the arm will sag on the bench even though it held
in sim.

The model
---------
A two-node lumped-capacitance thermal network, the same resistance-capacitance
abstraction used for electronics cooling, applied to the motor:

    P_cu = c_loss * tau^2                      copper loss, tau = applied torque
                                               (c_loss bundles winding R / kt^2)

    Cw dTw/dt = P_cu - (Tw - Tc)/R_wc          winding node
    Cc dTc/dt = (Tw - Tc)/R_wc - (Tc - Ta)/R_ca   case/housing node

    Tw : winding temperature   Cw : winding heat capacity   R_wc : winding->case
    Tc : case temperature      Cc : case heat capacity      R_ca : case->ambient
    Ta : ambient

Torque derating is a linear roll-off on winding temperature:

    frac(Tw) = 1                                   Tw <= T_derate
             = linear 1 -> floor                   T_derate < Tw < T_max
             = floor                               Tw >= T_max
    tau_available = frac(Tw) * tau_peak

The class also exposes closed-form analysis (steady-state temperature,
continuous torque rating, and the two network time constants from the system
eigenvalues) so the actuator can be sized and reasoned about, not just
simulated.

SI units, temperatures in degrees Celsius.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np


@dataclass
class ThermalActuatorParams:
    tau_peak: float = 6.0        # peak/nominal torque, N m
    c_loss: float = 3.4          # copper-loss coefficient, W per (N m)^2
    R_wc: float = 1.0            # winding-to-case thermal resistance, K/W
    R_ca: float = 1.5            # case-to-ambient thermal resistance, K/W
    Cw: float = 12.0             # winding heat capacity, J/K
    Cc: float = 100.0            # case heat capacity, J/K
    T_ambient: float = 25.0      # ambient temperature, degC
    T_derate: float = 90.0       # winding temp where derating begins, degC
    T_max: float = 110.0         # winding temp at full derate, degC
    floor: float = 0.40          # torque fraction floor at/above T_max


class ThermalActuator:
    """Stateful two-node thermal model with torque derating for one joint."""

    def __init__(self, p: ThermalActuatorParams | None = None):
        self.p = p or ThermalActuatorParams()
        self.Tw = self.p.T_ambient
        self.Tc = self.p.T_ambient

    # -- runtime ----------------------------------------------------------
    def available_torque(self) -> float:
        """Torque the actuator can currently deliver given winding temp."""
        p = self.p
        if self.Tw <= p.T_derate:
            frac = 1.0
        elif self.Tw >= p.T_max:
            frac = p.floor
        else:
            span = (self.Tw - p.T_derate) / (p.T_max - p.T_derate)
            frac = 1.0 - (1.0 - p.floor) * span
        return frac * p.tau_peak

    def _derivs(self, Tw: float, Tc: float, tau_applied: float):
        p = self.p
        P = p.c_loss * tau_applied ** 2
        dTw = (P - (Tw - Tc) / p.R_wc) / p.Cw
        dTc = ((Tw - Tc) / p.R_wc - (Tc - p.T_ambient) / p.R_ca) / p.Cc
        return dTw, dTc

    def step(self, tau_applied: float, dt: float) -> None:
        """Advance winding and case temperatures by dt using RK4.

        `tau_applied` is the torque the joint actually produced this step, so
        the dissipation reflects the derated command, not the raw demand.
        """
        Tw, Tc = self.Tw, self.Tc
        k1 = self._derivs(Tw, Tc, tau_applied)
        k2 = self._derivs(Tw + 0.5 * dt * k1[0], Tc + 0.5 * dt * k1[1], tau_applied)
        k3 = self._derivs(Tw + 0.5 * dt * k2[0], Tc + 0.5 * dt * k2[1], tau_applied)
        k4 = self._derivs(Tw + dt * k3[0], Tc + dt * k3[1], tau_applied)
        self.Tw = Tw + dt / 6.0 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        self.Tc = Tc + dt / 6.0 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])

    def reset(self) -> None:
        self.Tw = self.p.T_ambient
        self.Tc = self.p.T_ambient

    # -- closed-form analysis --------------------------------------------
    def steady_state_winding_temp(self, tau: float) -> float:
        """Winding temperature if `tau` were held forever."""
        p = self.p
        P = p.c_loss * tau ** 2
        return p.T_ambient + P * (p.R_wc + p.R_ca)

    def continuous_torque_limit(self) -> float:
        """Largest torque holdable indefinitely without entering derating,
        i.e. the torque whose steady-state winding temp equals T_derate.
        """
        p = self.p
        return float(np.sqrt((p.T_derate - p.T_ambient)
                             / (p.c_loss * (p.R_wc + p.R_ca))))

    def time_constants(self) -> tuple[float, float]:
        """The two thermal time constants of the linear network, from the
        eigenvalues of the state matrix (fast winding node, slow case node).
        """
        p = self.p
        A = np.array([
            [-1.0 / (p.Cw * p.R_wc), 1.0 / (p.Cw * p.R_wc)],
            [1.0 / (p.Cc * p.R_wc),
             -(1.0 / (p.Cc * p.R_wc) + 1.0 / (p.Cc * p.R_ca))],
        ])
        eig = np.linalg.eigvals(A)
        taus = sorted(-1.0 / eig.real)
        return float(taus[0]), float(taus[1])


def _report() -> None:
    act = ThermalActuator()
    p = act.p
    t_fast, t_slow = act.time_constants()
    print("Thermal actuator characterisation")
    print("-" * 42)
    print(f"peak torque              : {p.tau_peak:.2f} N m")
    print(f"continuous torque limit  : {act.continuous_torque_limit():.2f} N m")
    print(f"winding time constant    : {t_fast:6.1f} s")
    print(f"case time constant       : {t_slow:6.1f} s")
    for tau in [2.0, 3.0, 3.46, 4.0, 5.0]:
        print(f"  hold {tau:4.2f} N m -> steady winding "
              f"{act.steady_state_winding_temp(tau):6.1f} degC")


if __name__ == "__main__":
    _report()
