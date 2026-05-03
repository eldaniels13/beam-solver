"""Matplotlib visualization for beam diagrams.

Generates a figure with 3 subplots:
    1. Beam schematic (supports, loads, dimensions)
    2. Shear force diagram V(x)
    3. Bending moment diagram M(x)
Plus a text area showing equilibrium equations with LaTeX rendering.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec

from .model import Beam
from .solver import Reactions, DiagramData


def plot_beam_analysis(
    beam: Beam,
    reactions: Reactions,
    diagrams: DiagramData,
    title: str = "Beam Analysis",
    show: bool = True,
    save_path: str | None = None,
) -> plt.Figure:
    """Create the full beam analysis figure."""
    fig = plt.figure(figsize=(14, 10))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    gs = GridSpec(3, 2, figure=fig, width_ratios=[3, 1], hspace=0.35, wspace=0.3)

    ax_beam = fig.add_subplot(gs[0, 0])
    ax_eq = fig.add_subplot(gs[0, 1])
    ax_shear = fig.add_subplot(gs[1, :])
    ax_moment = fig.add_subplot(gs[2, :])

    _draw_beam(ax_beam, beam, reactions)
    _draw_equations(ax_eq, reactions)
    _draw_shear(ax_shear, diagrams)
    _draw_moment(ax_moment, diagrams)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()

    return fig


def _draw_beam(ax: plt.Axes, beam: Beam, reactions: Reactions):
    """Draw the beam schematic with supports and loads."""
    L = beam.length
    margin = L * 0.1
    ax.set_xlim(-margin, L + margin)
    ax.set_ylim(-L * 0.4, L * 0.5)
    ax.set_aspect("equal")
    ax.set_title("Beam Schematic")
    ax.axhline(y=0, color="gray", linewidth=0.5, linestyle="--")

    # Beam body
    beam_h = L * 0.03
    rect = patches.Rectangle(
        (0, -beam_h / 2), L, beam_h,
        linewidth=2, edgecolor="black", facecolor="#d4e6f1",
    )
    ax.add_patch(rect)

    # Supports
    for sup in beam.supports:
        if sup.kind == "pin":
            _draw_pin(ax, sup.position, beam_h, L)
        elif sup.kind == "roller":
            _draw_roller(ax, sup.position, beam_h, L)

    # Point loads
    for load in beam.point_loads:
        _draw_point_load(ax, load.position, load.magnitude, L)

    # Distributed loads
    for load in beam.distributed_loads:
        _draw_distributed_load(ax, load, L)

    # Reactions (upward arrows)
    for sup in beam.supports:
        key = "Ay" if sup == beam.supports[0] else "By"
        r_val = reactions.forces[key]
        if abs(r_val) > 1e-10:
            _draw_reaction(ax, sup.position, r_val, key, L)

    # Dimension line
    y_dim = -L * 0.3
    ax.annotate(
        "", xy=(L, y_dim), xytext=(0, y_dim),
        arrowprops=dict(arrowstyle="<->", color="black", lw=1.2),
    )
    ax.text(L / 2, y_dim - L * 0.04, f"L = {L} m",
            ha="center", va="top", fontsize=10)

    ax.set_xlabel("x (m)")
    ax.tick_params(left=False, labelleft=False)


def _draw_pin(ax, x, beam_h, L):
    """Draw a pin support (triangle)."""
    s = L * 0.04
    triangle = plt.Polygon(
        [(x, -beam_h / 2), (x - s, -beam_h / 2 - s * 1.5), (x + s, -beam_h / 2 - s * 1.5)],
        closed=True, facecolor="white", edgecolor="black", linewidth=1.5, zorder=5,
    )
    ax.add_patch(triangle)
    # Ground hatch
    ax.plot([x - s * 1.2, x + s * 1.2], [-beam_h / 2 - s * 1.5] * 2,
            color="black", linewidth=1.5)


def _draw_roller(ax, x, beam_h, L):
    """Draw a roller support (triangle + circle)."""
    s = L * 0.04
    triangle = plt.Polygon(
        [(x, -beam_h / 2), (x - s, -beam_h / 2 - s * 1.2), (x + s, -beam_h / 2 - s * 1.2)],
        closed=True, facecolor="white", edgecolor="black", linewidth=1.5, zorder=5,
    )
    ax.add_patch(triangle)
    circle = plt.Circle(
        (x, -beam_h / 2 - s * 1.2 - s * 0.3), s * 0.3,
        facecolor="white", edgecolor="black", linewidth=1.5, zorder=5,
    )
    ax.add_patch(circle)
    ax.plot([x - s * 1.2, x + s * 1.2],
            [-beam_h / 2 - s * 1.2 - s * 0.6] * 2,
            color="black", linewidth=1.5)


def _draw_point_load(ax, x, magnitude, L):
    """Draw a point load arrow."""
    arrow_len = L * 0.2
    ax.annotate(
        "", xy=(x, 0), xytext=(x, arrow_len),
        arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.2",
                        color="red", lw=2),
    )
    ax.text(x, arrow_len + L * 0.02, f"{magnitude} kN",
            ha="center", va="bottom", fontsize=9, color="red", fontweight="bold")


def _draw_distributed_load(ax, load, L):
    """Draw a distributed load with arrows."""
    n_arrows = max(5, int(load.length / L * 15))
    xs = np.linspace(load.start, load.end, n_arrows)
    max_h = L * 0.18

    for xi in xs:
        # Interpolate intensity
        if load.length > 0:
            t = (xi - load.start) / load.length
            w = load.w_start + (load.w_end - load.w_start) * t
        else:
            w = load.w_start
        w_max = max(abs(load.w_start), abs(load.w_end))
        if w_max > 0:
            h = max_h * abs(w) / w_max
        else:
            h = 0
        ax.annotate(
            "", xy=(xi, 0), xytext=(xi, h),
            arrowprops=dict(arrowstyle="->,head_width=0.2,head_length=0.1",
                            color="red", lw=1),
        )

    # Top line connecting arrow tails
    top_ys = []
    for xi in xs:
        if load.length > 0:
            t = (xi - load.start) / load.length
            w = load.w_start + (load.w_end - load.w_start) * t
        else:
            w = load.w_start
        w_max = max(abs(load.w_start), abs(load.w_end))
        top_ys.append(max_h * abs(w) / w_max if w_max > 0 else 0)

    ax.plot(xs, top_ys, color="red", linewidth=1.5)

    # Label
    mid_x = (load.start + load.end) / 2
    max_y = max(top_ys) if top_ys else max_h
    if load.w_start == load.w_end:
        label = f"{load.w_start} kN/m"
    else:
        label = f"{load.w_start}→{load.w_end} kN/m"
    ax.text(mid_x, max_y + L * 0.03, label,
            ha="center", va="bottom", fontsize=9, color="red", fontweight="bold")


def _draw_reaction(ax, x, value, label, L):
    """Draw a reaction force arrow (blue, upward)."""
    arrow_len = L * 0.15
    y_base = -L * 0.18
    ax.annotate(
        "", xy=(x, -L * 0.03), xytext=(x, y_base),
        arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.2",
                        color="blue", lw=2),
    )
    ax.text(x, y_base - L * 0.03,
            f"${label} = {value:.2f}$ kN",
            ha="center", va="top", fontsize=9, color="blue", fontweight="bold")


def _draw_equations(ax: plt.Axes, reactions: Reactions):
    """Render the equilibrium equations using LaTeX."""
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("Equilibrium", fontsize=11)

    n = len(reactions.equations)
    for i, eq in enumerate(reactions.equations):
        y = 0.85 - i * (0.7 / max(n - 1, 1))
        ax.text(0.05, y, eq, fontsize=10, va="center",
                transform=ax.transAxes)


def _draw_shear(ax: plt.Axes, data: DiagramData):
    """Plot shear force diagram."""
    ax.fill_between(data.x, data.V, alpha=0.3, color="steelblue")
    ax.plot(data.x, data.V, color="steelblue", linewidth=1.5)
    ax.axhline(y=0, color="black", linewidth=0.8)
    ax.set_title("Shear Force Diagram — V(x)")
    ax.set_ylabel("V (kN)")
    ax.set_xlabel("x (m)")
    ax.grid(True, alpha=0.3)

    # Annotate max/min
    i_max = np.argmax(data.V)
    i_min = np.argmin(data.V)
    ax.annotate(
        f"Vmax = {data.V_max:.2f} kN",
        xy=(data.x[i_max], data.V_max),
        xytext=(10, 10), textcoords="offset points",
        fontsize=9, color="steelblue", fontweight="bold",
    )
    ax.annotate(
        f"Vmin = {data.V_min:.2f} kN",
        xy=(data.x[i_min], data.V_min),
        xytext=(10, -15), textcoords="offset points",
        fontsize=9, color="steelblue", fontweight="bold",
    )


def _draw_moment(ax: plt.Axes, data: DiagramData):
    """Plot bending moment diagram."""
    ax.fill_between(data.x, data.M, alpha=0.3, color="darkorange")
    ax.plot(data.x, data.M, color="darkorange", linewidth=1.5)
    ax.axhline(y=0, color="black", linewidth=0.8)
    ax.set_title("Bending Moment Diagram — M(x)")
    ax.set_ylabel("M (kN·m)")
    ax.set_xlabel("x (m)")
    ax.grid(True, alpha=0.3)

    # Annotate max
    i_max = np.argmax(np.abs(data.M))
    ax.annotate(
        f"Mmax = {data.M[i_max]:.2f} kN·m",
        xy=(data.x[i_max], data.M[i_max]),
        xytext=(10, 10), textcoords="offset points",
        fontsize=9, color="darkorange", fontweight="bold",
    )
