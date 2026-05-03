"""Equilibrium solver for statically determinate beams.

Solves support reactions and computes shear V(x) and moment M(x) diagrams
using static equilibrium equations:
    ΣFx = 0,  ΣFy = 0,  ΣM = 0
"""

from dataclasses import dataclass

import numpy as np

from .model import Beam, PointLoad, DistributedLoad


@dataclass
class Reactions:
    """Solved support reactions."""
    forces: dict[str, float]     # e.g. {"Ay": 50.0, "By": 25.0, "Ax": 0.0}
    equations: list[str]         # LaTeX strings showing the equilibrium steps


@dataclass
class DiagramData:
    """Arrays for plotting V and M diagrams."""
    x: np.ndarray
    V: np.ndarray
    M: np.ndarray
    V_max: float
    V_min: float
    M_max: float
    M_min: float


def solve_reactions(beam: Beam) -> Reactions:
    """Solve support reactions for a simply supported beam (pin + roller).

    Assumes pin at support A (left), roller at support B (right).
    """
    errors = beam.validate()
    if errors:
        raise ValueError("Invalid beam configuration:\n" + "\n".join(errors))

    if len(beam.supports) != 2:
        raise ValueError(
            f"Expected 2 supports for simply supported beam, got {len(beam.supports)}"
        )

    sup_a, sup_b = beam.supports
    a_pos = sup_a.position
    b_pos = sup_b.position

    # Collect all applied forces and their moments about A
    total_fy = 0.0   # sum of applied forces (positive = downward)
    total_ma = 0.0   # sum of moments about A (positive = clockwise)

    for load in beam.point_loads:
        total_fy += load.magnitude
        total_ma += load.magnitude * (load.position - a_pos)

    for load in beam.distributed_loads:
        f_r = load.resultant_force
        x_r = load.resultant_position
        total_fy += f_r
        total_ma += f_r * (x_r - a_pos)

    # Equilibrium: ΣM_A = 0  →  R_B * (b_pos - a_pos) - total_ma = 0
    lever_ab = b_pos - a_pos
    if lever_ab == 0:
        raise ValueError("Supports A and B cannot be at the same position")

    r_by = total_ma / lever_ab
    # ΣFy = 0  →  R_Ay + R_By - total_fy = 0
    r_ay = total_fy - r_by
    # ΣFx = 0  →  Ax = 0 (no horizontal loads)
    r_ax = 0.0

    # Build step-by-step LaTeX equations
    equations = [
        r"$\sum F_x = 0 \;\Rightarrow\; A_x = 0$",
        (
            rf"$\sum M_A = 0 \;\Rightarrow\; "
            rf"B_y \cdot {lever_ab:.2f} = {total_ma:.2f}$"
        ),
        rf"$B_y = \frac{{{total_ma:.2f}}}{{{lever_ab:.2f}}} = {r_by:.2f} \;\mathrm{{kN}}$",
        (
            rf"$\sum F_y = 0 \;\Rightarrow\; "
            rf"A_y = {total_fy:.2f} - {r_by:.2f} = {r_ay:.2f} \;\mathrm{{kN}}$"
        ),
    ]

    return Reactions(
        forces={"Ax": r_ax, "Ay": r_ay, "By": r_by},
        equations=equations,
    )


def compute_diagrams(beam: Beam, reactions: Reactions, n_points: int = 500) -> DiagramData:
    """Compute shear and moment diagrams along the beam."""
    x = np.linspace(0, beam.length, n_points)
    V = np.zeros_like(x)
    M = np.zeros_like(x)

    r_ay = reactions.forces["Ay"]
    r_by = reactions.forces["By"]
    sup_a = beam.supports[0].position
    sup_b = beam.supports[1].position

    for i, xi in enumerate(x):
        v = 0.0
        m = 0.0

        # Reaction at A
        if xi >= sup_a:
            v += r_ay
            m += r_ay * (xi - sup_a)

        # Reaction at B
        if xi >= sup_b:
            v += r_by
            m += r_by * (xi - sup_b)

        # Point loads (positive magnitude = downward = negative shear)
        for load in beam.point_loads:
            if xi >= load.position:
                v -= load.magnitude
                m -= load.magnitude * (xi - load.position)

        # Distributed loads
        for load in beam.distributed_loads:
            if xi > load.start:
                x_in = min(xi, load.end) - load.start
                L = load.end - load.start
                # Linear interpolation of intensity at cut
                if L > 0:
                    w_at_start = load.w_start
                    w_at_cut = load.w_start + (load.w_end - load.w_start) * (x_in / L)
                else:
                    w_at_start = load.w_start
                    w_at_cut = load.w_start
                # Resultant of partial distributed load up to xi
                f_partial = (w_at_start + w_at_cut) / 2 * x_in
                # Centroid of partial trapezoid from load.start
                if w_at_start + w_at_cut > 0:
                    centroid = x_in * (w_at_start + 2 * w_at_cut) / (3 * (w_at_start + w_at_cut))
                else:
                    centroid = x_in / 2
                x_resultant = load.start + centroid

                v -= f_partial
                m -= f_partial * (xi - x_resultant)

        V[i] = v
        M[i] = m

    return DiagramData(
        x=x, V=V, M=M,
        V_max=float(np.max(V)), V_min=float(np.min(V)),
        M_max=float(np.max(M)), M_min=float(np.min(M)),
    )
