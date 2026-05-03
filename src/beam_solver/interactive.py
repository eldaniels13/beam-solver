"""Matplotlib interactive beam editor.

Launch with:
    python -m beam_solver --interactive
"""

from __future__ import annotations

import sys
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import Button

from .model import Beam, PointLoad, DistributedLoad, Support
from .solver import solve_reactions, compute_diagrams
from .plotter import plot_beam_analysis


# ── Constants ──────────────────────────────────────────────────────────────────

_BEAM_Y = 0.0          # y-position of beam centerline in editor axes
_BEAM_H = 0.08         # beam rectangle half-height (in data coords)
_SNAP = 0.25           # snap grid (m) when placing loads
_DELETE_TOL = 0.5      # distance tolerance for delete-click (m)

_COLOR_PL = "#e74c3c"        # point load arrows
_COLOR_DL = "#e67e22"        # distributed load region
_COLOR_REACT = "#2980b9"     # reaction arrows
_COLOR_GHOST = "#aaaaaa"     # ghost preview during placement


# ── Helpers ────────────────────────────────────────────────────────────────────

def _snap(x: float, grid: float = _SNAP) -> float:
    return round(x / grid) * grid


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# ── Main class ─────────────────────────────────────────────────────────────────

class InteractiveBeamEditor:
    """Click-to-place interactive beam analysis editor."""

    def __init__(self, beam_length: float = 10.0):
        self.beam_length = beam_length

        # Working beam (loads accumulate here)
        self._point_loads: list[PointLoad] = []
        self._dist_loads: list[DistributedLoad] = []

        # Interaction state
        self.mode: str = "IDLE"
        self._dist_start: float | None = None   # first click x for distributed load
        self._ghost_x: float | None = None       # current mouse x for ghost preview

        # ── Figure layout ──────────────────────────────────────────────────────
        self.fig = plt.figure(figsize=(14, 11))
        self.fig.suptitle(
            "Beam Solver — Interactive Editor",
            fontsize=13, fontweight="bold", y=0.98,
        )

        gs = GridSpec(
            4, 1,
            figure=self.fig,
            height_ratios=[3, 0.55, 1.5, 1.5],
            hspace=0.45,
        )
        self.ax_editor = self.fig.add_subplot(gs[0])    # beam canvas
        self.ax_vd     = self.fig.add_subplot(gs[2])    # shear diagram
        self.ax_md     = self.fig.add_subplot(gs[3])    # moment diagram

        # Toolbar axes — positioned as absolute insets above diagram area
        self._setup_toolbar()
        self._setup_editor_axes()
        self._connect_events()

        # Initial draw
        self._redraw_editor()
        self._clear_diagrams()

    # ── Toolbar ────────────────────────────────────────────────────────────────

    def _setup_toolbar(self):
        """Create toolbar buttons as inset axes."""
        btn_defs = [
            ("Add Point Load [P]",  0.04, self._btn_add_point),
            ("Add Dist. Load [D]",  0.20, self._btn_add_dist),
            ("Delete Load [X]",     0.36, self._btn_delete),
            ("Clear All [C]",       0.52, self._btn_clear),
            ("Full Report [R]",     0.68, self._btn_report),
        ]
        self._buttons = []
        for label, left, callback in btn_defs:
            ax_btn = self.fig.add_axes([left, 0.565, 0.13, 0.035])
            btn = Button(ax_btn, label, color="#ecf0f1", hovercolor="#bdc3c7")
            btn.label.set_fontsize(8)
            btn.on_clicked(callback)
            self._buttons.append(btn)  # keep references to avoid GC

    def _setup_editor_axes(self):
        ax = self.ax_editor
        ax.set_xlim(-0.5, self.beam_length + 0.5)
        ax.set_ylim(-0.6, 0.8)
        ax.set_aspect("auto")
        ax.set_xlabel("Position (m)", fontsize=9)
        ax.set_title(
            "Click on beam to place loads | P: point  D: distributed  X: delete  Esc: cancel  R: full report",
            fontsize=8, color="#555555",
        )
        ax.axhline(0, color="#cccccc", linewidth=0.5, zorder=0)

        # Status text
        self._status_text = ax.text(
            self.beam_length / 2, -0.55,
            "Ready — select an action above or press P / D",
            ha="center", va="bottom",
            fontsize=8, color="#555555",
            style="italic",
        )

    # ── Events ─────────────────────────────────────────────────────────────────

    def _connect_events(self):
        self.fig.canvas.mpl_connect("button_press_event", self._on_click)
        self.fig.canvas.mpl_connect("motion_notify_event", self._on_motion)
        self.fig.canvas.mpl_connect("key_press_event", self._on_key)

    def _on_click(self, event):
        if event.inaxes != self.ax_editor:
            return
        if event.xdata is None:
            return

        x = _snap(_clamp(event.xdata, 0.0, self.beam_length))

        if self.mode == "ADD_POINT_LOAD":
            self._point_loads.append(PointLoad(magnitude=10.0, position=x))
            self._set_mode("IDLE")
            self._redraw_editor()
            self._auto_solve()

        elif self.mode == "ADD_DIST_LOAD":
            self._dist_start = x
            self._set_mode("WAIT_DIST_END")

        elif self.mode == "WAIT_DIST_END":
            x_end = x
            x_start = self._dist_start
            if x_end == x_start:
                self._set_status("Start and end must differ — try again")
                return
            if x_end < x_start:
                x_start, x_end = x_end, x_start
            self._dist_loads.append(
                DistributedLoad(w_start=10.0, w_end=10.0, start=x_start, end=x_end)
            )
            self._dist_start = None
            self._set_mode("IDLE")
            self._redraw_editor()
            self._auto_solve()

        elif self.mode == "DELETE_LOAD":
            self._delete_nearest(x)
            self._set_mode("IDLE")
            self._redraw_editor()
            self._auto_solve()

    def _on_motion(self, event):
        if event.inaxes != self.ax_editor or event.xdata is None:
            return
        self._ghost_x = _snap(_clamp(event.xdata, 0.0, self.beam_length))
        if self.mode in ("ADD_POINT_LOAD", "WAIT_DIST_END", "ADD_DIST_LOAD"):
            self._redraw_editor(ghost=True)

    def _on_key(self, event):
        key = event.key.lower() if event.key else ""
        if key == "p":
            self._btn_add_point(None)
        elif key == "d":
            self._btn_add_dist(None)
        elif key == "x":
            self._btn_delete(None)
        elif key == "c":
            self._btn_clear(None)
        elif key == "r":
            self._btn_report(None)
        elif key == "escape":
            self._dist_start = None
            self._set_mode("IDLE")
            self._redraw_editor()

    # ── Button callbacks ───────────────────────────────────────────────────────

    def _btn_add_point(self, _event):
        self._set_mode("ADD_POINT_LOAD")

    def _btn_add_dist(self, _event):
        self._set_mode("ADD_DIST_LOAD")

    def _btn_delete(self, _event):
        self._set_mode("DELETE_LOAD")

    def _btn_clear(self, _event):
        self._point_loads.clear()
        self._dist_loads.clear()
        self._dist_start = None
        self._set_mode("IDLE")
        self._redraw_editor()
        self._clear_diagrams()

    def _btn_report(self, _event):
        """Open a formal 4-panel analysis in a new figure."""
        beam = self._build_beam()
        errors = beam.validate()
        if errors:
            self._set_status("Cannot generate report: " + " | ".join(errors))
            return
        if not self._point_loads and not self._dist_loads:
            self._set_status("Add loads before generating a report.")
            return
        try:
            reactions = solve_reactions(beam)
            diagrams = compute_diagrams(beam, reactions)
        except ValueError as exc:
            self._set_status(f"Solver error: {exc}")
            return

        # Opens in a new window (doesn't block editor)
        plot_beam_analysis(
            beam, reactions, diagrams,
            title="Full Beam Analysis Report",
            show=True,
        )

    # ── Mode management ────────────────────────────────────────────────────────

    def _set_mode(self, mode: str):
        self.mode = mode
        messages = {
            "IDLE":          "Ready — press P (point load) or D (distributed load)",
            "ADD_POINT_LOAD": "Click on the beam to place a 10 kN point load",
            "ADD_DIST_LOAD":  "Click the START position of the distributed load",
            "WAIT_DIST_END":  f"Now click the END position (started at {self._dist_start} m)",
            "DELETE_LOAD":    "Click nearest load to delete it",
        }
        self._set_status(messages.get(mode, ""))

    def _set_status(self, text: str):
        self._status_text.set_text(text)
        self.fig.canvas.draw_idle()

    # ── Beam helpers ───────────────────────────────────────────────────────────

    def _build_beam(self) -> Beam:
        return Beam(
            length=self.beam_length,
            supports=[
                Support(kind="pin",    position=0.0),
                Support(kind="roller", position=self.beam_length),
            ],
            point_loads=list(self._point_loads),
            distributed_loads=list(self._dist_loads),
        )

    def _delete_nearest(self, x: float):
        """Remove the load whose representative x is closest to the click."""
        candidates: list[tuple[float, str, int]] = []  # (dist, kind, index)

        for i, pl in enumerate(self._point_loads):
            candidates.append((abs(pl.position - x), "pt", i))
        for i, dl in enumerate(self._dist_loads):
            mid = (dl.start + dl.end) / 2
            candidates.append((abs(mid - x), "dl", i))

        if not candidates:
            self._set_status("No loads to delete.")
            return

        dist, kind, idx = min(candidates, key=lambda c: c[0])
        if dist > _DELETE_TOL:
            self._set_status(f"No load within {_DELETE_TOL} m of click.")
            return

        if kind == "pt":
            removed = self._point_loads.pop(idx)
            self._set_status(f"Removed point load: {removed.magnitude} kN at x={removed.position} m")
        else:
            removed = self._dist_loads.pop(idx)
            self._set_status(f"Removed dist. load: {removed.w_start}–{removed.w_end} kN/m")

    # ── Drawing ────────────────────────────────────────────────────────────────

    def _redraw_editor(self, ghost: bool = False):
        """Clear and redraw the beam editor canvas."""
        ax = self.ax_editor
        # Save status text content before clearing
        status = self._status_text.get_text()

        ax.cla()
        self._setup_editor_axes()
        self._status_text.set_text(status)

        L = self.beam_length

        # ── Beam rectangle ──
        beam_rect = plt.Rectangle(
            (0, -_BEAM_H), L, 2 * _BEAM_H,
            color="#d5d8dc", zorder=2,
        )
        ax.add_patch(beam_rect)
        ax.plot([0, L], [0, 0], color="#7f8c8d", linewidth=1.5, zorder=3)

        # ── Pin support (left) ──
        _draw_pin(ax, 0.0, L)

        # ── Roller support (right) ──
        _draw_roller(ax, L, L)

        # ── Distributed loads ──
        for dl in self._dist_loads:
            _draw_dist_load(ax, dl, L, alpha=1.0)

        # ── Ghost preview ──
        gx = self._ghost_x
        if ghost and gx is not None:
            if self.mode == "ADD_POINT_LOAD":
                _draw_arrow(ax, gx, 0.55, -0.45, _COLOR_GHOST, alpha=0.4)
                ax.text(gx, 0.58, f"{gx:.2f} m", ha="center", fontsize=7,
                        color=_COLOR_GHOST, alpha=0.6)
            elif self.mode == "WAIT_DIST_END" and self._dist_start is not None:
                xs, xe = sorted([self._dist_start, gx])
                ax.axvspan(xs, xe, ymin=0.55, ymax=0.85, color=_COLOR_GHOST, alpha=0.25)
                ax.text((xs + xe) / 2, 0.72, f"{xs:.2f} – {gx:.2f} m",
                        ha="center", fontsize=7, color=_COLOR_GHOST)
            elif self.mode == "ADD_DIST_LOAD":
                ax.axvline(gx, color=_COLOR_GHOST, linestyle="--", alpha=0.5, linewidth=1)
                ax.text(gx, 0.72, f"{gx:.2f} m", ha="center", fontsize=7,
                        color=_COLOR_GHOST, alpha=0.6)

        # ── Point loads ──
        max_pl = max((abs(pl.magnitude) for pl in self._point_loads), default=10.0)
        for pl in self._point_loads:
            scale = abs(pl.magnitude) / max_pl
            arrow_len = 0.25 + 0.3 * scale
            _draw_arrow(ax, pl.position, _BEAM_H + arrow_len, -arrow_len, _COLOR_PL)
            ax.text(
                pl.position, _BEAM_H + arrow_len + 0.04,
                f"{pl.magnitude:.1f} kN",
                ha="center", fontsize=7, color=_COLOR_PL, fontweight="bold",
            )

        # ── Reactions (if solved) ──
        if hasattr(self, "_last_reactions") and self._last_reactions:
            r = self._last_reactions
            ay = r.forces.get("Ay", 0)
            by = r.forces.get("By", 0)
            _draw_arrow(ax, 0.0, -_BEAM_H - 0.3, 0.28, _COLOR_REACT)
            ax.text(0.0, -_BEAM_H - 0.36, f"Ay={ay:.1f} kN",
                    ha="center", fontsize=7, color=_COLOR_REACT)
            _draw_arrow(ax, L, -_BEAM_H - 0.3, 0.28, _COLOR_REACT)
            ax.text(L, -_BEAM_H - 0.36, f"By={by:.1f} kN",
                    ha="center", fontsize=7, color=_COLOR_REACT)

        # ── x-axis labels ──
        ax.set_xticks(np.arange(0, L + 0.01, max(0.5, round(L / 10, 1))))
        ax.set_yticks([])
        ax.set_xlim(-0.5, L + 0.5)

        self.fig.canvas.draw_idle()

    def _auto_solve(self):
        """Solve and update V/M diagrams. Silently skip if beam is invalid."""
        beam = self._build_beam()
        errors = beam.validate()
        if errors or (not self._point_loads and not self._dist_loads):
            self._last_reactions = None
            self._clear_diagrams()
            return

        try:
            reactions = solve_reactions(beam)
            diagrams = compute_diagrams(beam, reactions)
        except ValueError:
            self._last_reactions = None
            self._clear_diagrams()
            return

        self._last_reactions = reactions
        self._draw_diagrams(diagrams)
        # Redraw editor to show updated reactions
        self._redraw_editor()

    def _clear_diagrams(self):
        for ax, label in [(self.ax_vd, "V(x)  [kN]"), (self.ax_md, "M(x)  [kN·m]")]:
            ax.cla()
            ax.set_ylabel(label, fontsize=8)
            ax.set_xlabel("x (m)", fontsize=8)
            ax.axhline(0, color="#cccccc", linewidth=0.5)
            ax.text(
                0.5, 0.5, "Add loads to see diagrams",
                transform=ax.transAxes, ha="center", va="center",
                color="#aaaaaa", fontsize=9, style="italic",
            )
            ax.tick_params(labelsize=7)
        self.fig.canvas.draw_idle()

    def _draw_diagrams(self, diagrams):
        L = self.beam_length

        # Shear
        ax = self.ax_vd
        ax.cla()
        ax.axhline(0, color="#cccccc", linewidth=0.8)
        ax.fill_between(diagrams.x, diagrams.V, 0,
                        where=(diagrams.V >= 0), alpha=0.35, color="#2980b9")
        ax.fill_between(diagrams.x, diagrams.V, 0,
                        where=(diagrams.V < 0), alpha=0.35, color="#e74c3c")
        ax.plot(diagrams.x, diagrams.V, color="#1a252f", linewidth=1.2)
        ax.set_ylabel("V(x)  [kN]", fontsize=8)
        ax.set_xlabel("x (m)", fontsize=8)
        ax.set_xlim(0, L)
        ax.tick_params(labelsize=7)
        ax.annotate(
            f"Vmax={diagrams.V_max:.2f} kN",
            xy=(diagrams.x[np.argmax(diagrams.V)], diagrams.V_max),
            xytext=(5, 5), textcoords="offset points",
            fontsize=7, color="#2980b9",
        )

        # Moment
        ax = self.ax_md
        ax.cla()
        ax.axhline(0, color="#cccccc", linewidth=0.8)
        ax.fill_between(diagrams.x, diagrams.M, 0,
                        where=(diagrams.M >= 0), alpha=0.35, color="#27ae60")
        ax.fill_between(diagrams.x, diagrams.M, 0,
                        where=(diagrams.M < 0), alpha=0.35, color="#8e44ad")
        ax.plot(diagrams.x, diagrams.M, color="#1a252f", linewidth=1.2)
        ax.set_ylabel("M(x)  [kN·m]", fontsize=8)
        ax.set_xlabel("x (m)", fontsize=8)
        ax.set_xlim(0, L)
        ax.tick_params(labelsize=7)
        ax.annotate(
            f"Mmax={diagrams.M_max:.2f} kN·m",
            xy=(diagrams.x[np.argmax(diagrams.M)], diagrams.M_max),
            xytext=(5, 5), textcoords="offset points",
            fontsize=7, color="#27ae60",
        )

        self.fig.canvas.draw_idle()


# ── Drawing primitives ─────────────────────────────────────────────────────────

def _draw_arrow(ax, x: float, y_base: float, dy: float, color: str, alpha: float = 1.0):
    """Draw a vertical arrow from (x, y_base) with length dy."""
    ax.annotate(
        "", xy=(x, y_base + dy), xytext=(x, y_base),
        arrowprops=dict(
            arrowstyle="->" if dy > 0 else "<-",
            color=color, lw=1.5,
        ),
        alpha=alpha,
    )


def _draw_pin(ax, x: float, L: float):
    size = L * 0.025
    tri = plt.Polygon(
        [[x, -_BEAM_H], [x - size, -_BEAM_H - size * 2], [x + size, -_BEAM_H - size * 2]],
        closed=True, color="#5d6d7e", zorder=4,
    )
    ax.add_patch(tri)
    ax.plot([x - size * 1.5, x + size * 1.5], [-_BEAM_H - size * 2.1] * 2,
            color="#5d6d7e", linewidth=2, zorder=4)


def _draw_roller(ax, x: float, L: float):
    size = L * 0.025
    tri = plt.Polygon(
        [[x, -_BEAM_H], [x - size, -_BEAM_H - size * 2], [x + size, -_BEAM_H - size * 2]],
        closed=True, color="#5d6d7e", zorder=4,
    )
    ax.add_patch(tri)
    circle = plt.Circle((x, -_BEAM_H - size * 2 - size * 0.8), size * 0.7,
                         color="#5d6d7e", zorder=4)
    ax.add_patch(circle)
    ax.plot([x - size * 1.5, x + size * 1.5], [-_BEAM_H - size * 3.5] * 2,
            color="#5d6d7e", linewidth=2, zorder=4)


def _draw_dist_load(ax, dl: DistributedLoad, L: float, alpha: float = 1.0):
    """Draw distributed load as shaded trapezoidal region with arrows."""
    max_h = 0.38
    w_ref = max(dl.w_start, dl.w_end, 1.0)

    h_start = max_h * dl.w_start / w_ref
    h_end   = max_h * dl.w_end   / w_ref

    xs, xe = dl.start, dl.end

    # Shaded trapezoid
    verts = [
        (xs, _BEAM_H),
        (xs, _BEAM_H + h_start),
        (xe, _BEAM_H + h_end),
        (xe, _BEAM_H),
    ]
    patch = plt.Polygon(verts, closed=True, color=_COLOR_DL, alpha=0.25 * alpha)
    ax.add_patch(patch)
    ax.plot([xs, xs, xe, xe], [_BEAM_H, _BEAM_H + h_start, _BEAM_H + h_end, _BEAM_H],
            color=_COLOR_DL, linewidth=1, alpha=alpha)

    # Arrows every ~L/15
    n_arrows = max(2, int((xe - xs) / max(L / 15, 0.01)))
    for xi in np.linspace(xs, xe, n_arrows):
        h = h_start + (h_end - h_start) * (xi - xs) / max(xe - xs, 1e-9)
        ax.annotate(
            "", xy=(xi, _BEAM_H), xytext=(xi, _BEAM_H + h * 0.9),
            arrowprops=dict(arrowstyle="->", color=_COLOR_DL, lw=0.9),
            alpha=alpha,
        )

    # Labels
    ax.text(xs, _BEAM_H + h_start + 0.03, f"{dl.w_start:.1f}", ha="center",
            fontsize=6.5, color=_COLOR_DL, alpha=alpha)
    ax.text(xe, _BEAM_H + h_end + 0.03, f"{dl.w_end:.1f}", ha="center",
            fontsize=6.5, color=_COLOR_DL, alpha=alpha)


# ── Entry point ────────────────────────────────────────────────────────────────

def run_interactive(beam_length: float = 10.0):
    """Launch the interactive beam editor. Blocks until window is closed."""
    backend = matplotlib.get_backend()
    non_interactive = backend.lower() in ("agg", "pdf", "svg", "ps", "cairo")
    if non_interactive:
        print(
            f"Error: matplotlib backend '{backend}' does not support interactive windows.\n"
            "Set a GUI backend (e.g. TkAgg, Qt5Agg) before running:\n"
            "    import matplotlib; matplotlib.use('TkAgg')\n"
            "or install a GUI toolkit: pip install tk",
            file=sys.stderr,
        )
        sys.exit(1)

    editor = InteractiveBeamEditor(beam_length=beam_length)
    plt.tight_layout(rect=[0, 0.02, 1, 0.95])
    plt.show()
