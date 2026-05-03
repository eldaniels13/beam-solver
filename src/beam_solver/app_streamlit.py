"""Streamlit interactive frontend for beam_solver.

Run with:
    streamlit run streamlit_app.py
    python -m beam_solver --streamlit
"""

import uuid

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — must come before pyplot import
import matplotlib.pyplot as plt
import streamlit as st

try:
    from .model import Beam, PointLoad, DistributedLoad, Support
    from .solver import solve_reactions, compute_diagrams
    from .plotter import plot_beam_analysis
except ImportError:
    from beam_solver.model import Beam, PointLoad, DistributedLoad, Support  # noqa: E402
    from beam_solver.solver import solve_reactions, compute_diagrams  # noqa: E402
    from beam_solver.plotter import plot_beam_analysis  # noqa: E402

# ── Preset examples ────────────────────────────────────────────────────────────

PRESETS = {
    "— select a preset —": None,
    "Simply supported — 10 kN midspan point load": {
        "length": 6.0,
        "sup_a": 0.0,
        "sup_b": 6.0,
        "point_loads": [{"id": "pl0", "magnitude": 10.0, "position": 3.0}],
        "dist_loads": [],
    },
    "Uniform distributed load (30 kN/m)": {
        "length": 5.0,
        "sup_a": 0.0,
        "sup_b": 5.0,
        "point_loads": [],
        "dist_loads": [{"id": "dl0", "w_start": 30.0, "w_end": 30.0, "start": 0.0, "end": 5.0}],
    },
    "Combined: 2 point loads + UDL": {
        "length": 8.0,
        "sup_a": 0.0,
        "sup_b": 8.0,
        "point_loads": [
            {"id": "pl0", "magnitude": 15.0, "position": 2.0},
            {"id": "pl1", "magnitude": 10.0, "position": 6.0},
        ],
        "dist_loads": [{"id": "dl0", "w_start": 5.0, "w_end": 5.0, "start": 3.0, "end": 5.0}],
    },
    "Triangular distributed load": {
        "length": 6.0,
        "sup_a": 0.0,
        "sup_b": 6.0,
        "point_loads": [],
        "dist_loads": [{"id": "dl0", "w_start": 0.0, "w_end": 20.0, "start": 0.0, "end": 6.0}],
    },
}


# ── Session state helpers ───────────────────────────────────────────────────────

def _init_state():
    """Initialize session state defaults (runs once per session)."""
    if "beam_length" not in st.session_state:
        st.session_state.beam_length = 6.0
    if "sup_a" not in st.session_state:
        st.session_state.sup_a = 0.0
    if "sup_b" not in st.session_state:
        st.session_state.sup_b = 6.0
    if "point_loads" not in st.session_state:
        st.session_state.point_loads = []   # list of dicts: {id, magnitude, position}
    if "dist_loads" not in st.session_state:
        st.session_state.dist_loads = []    # list of dicts: {id, w_start, w_end, start, end}
    if "preset_applied" not in st.session_state:
        st.session_state.preset_applied = "— select a preset —"


def _apply_preset(name: str):
    preset = PRESETS[name]
    st.session_state.beam_length = preset["length"]
    st.session_state.sup_a = preset["sup_a"]
    st.session_state.sup_b = preset["sup_b"]
    st.session_state.point_loads = [dict(p) for p in preset["point_loads"]]
    st.session_state.dist_loads = [dict(d) for d in preset["dist_loads"]]


def build_beam_from_state() -> Beam:
    """Construct a Beam dataclass from current session state."""
    L = st.session_state.beam_length
    point_loads = [
        PointLoad(magnitude=pl["magnitude"], position=pl["position"])
        for pl in st.session_state.point_loads
    ]
    dist_loads = [
        DistributedLoad(
            w_start=dl["w_start"],
            w_end=dl["w_end"],
            start=dl["start"],
            end=dl["end"],
        )
        for dl in st.session_state.dist_loads
    ]
    return Beam(
        length=L,
        supports=[
            Support(kind="pin", position=st.session_state.sup_a),
            Support(kind="roller", position=st.session_state.sup_b),
        ],
        point_loads=point_loads,
        distributed_loads=dist_loads,
    )


# ── Sidebar ─────────────────────────────────────────────────────────────────────

def _render_sidebar():
    st.sidebar.title("Beam Configuration")

    # ── Presets ──
    st.sidebar.subheader("Presets")
    selected = st.sidebar.selectbox(
        "Load example",
        options=list(PRESETS.keys()),
        index=0,
        key="preset_select",
    )
    if selected != "— select a preset —" and selected != st.session_state.preset_applied:
        _apply_preset(selected)
        st.session_state.preset_applied = selected
        st.rerun()

    st.sidebar.divider()

    # ── Beam geometry ──
    st.sidebar.subheader("Beam")
    L = st.sidebar.number_input(
        "Length (m)", min_value=0.5, max_value=50.0,
        value=st.session_state.beam_length, step=0.5, key="beam_length",
    )
    st.sidebar.caption("Supports")
    col1, col2 = st.sidebar.columns(2)
    col1.number_input(
        "Pin A pos (m)", min_value=0.0, max_value=float(L),
        value=min(st.session_state.sup_a, L), step=0.5, key="sup_a",
        help="Pin support — resists Ax and Ay",
    )
    col2.number_input(
        "Roller B pos (m)", min_value=0.0, max_value=float(L),
        value=min(st.session_state.sup_b, L), step=0.5, key="sup_b",
        help="Roller support — resists Ay only",
    )

    st.sidebar.divider()

    # ── Point loads ──
    st.sidebar.subheader("Point Loads")
    to_delete_pl = None
    for i, pl in enumerate(st.session_state.point_loads):
        with st.sidebar.container():
            cols = st.sidebar.columns([2, 2, 1])
            pl["magnitude"] = cols[0].number_input(
                "F (kN)", value=float(pl["magnitude"]),
                step=1.0, key=f"pl_mag_{pl['id']}",
                help="Positive = downward",
            )
            pl["position"] = cols[1].number_input(
                "x (m)", value=float(min(pl["position"], L)),
                min_value=0.0, max_value=float(L),
                step=0.5, key=f"pl_pos_{pl['id']}",
            )
            if cols[2].button("✕", key=f"pl_del_{pl['id']}", help="Remove"):
                to_delete_pl = pl["id"]

    if to_delete_pl:
        st.session_state.point_loads = [
            p for p in st.session_state.point_loads if p["id"] != to_delete_pl
        ]
        st.rerun()

    if st.sidebar.button("＋ Add Point Load", use_container_width=True):
        st.session_state.point_loads.append({
            "id": str(uuid.uuid4())[:8],
            "magnitude": 10.0,
            "position": round(L / 2, 2),
        })
        st.session_state.preset_applied = "— select a preset —"
        st.rerun()

    st.sidebar.divider()

    # ── Distributed loads ──
    st.sidebar.subheader("Distributed Loads")
    to_delete_dl = None
    for i, dl in enumerate(st.session_state.dist_loads):
        with st.sidebar.expander(f"DL {i + 1}", expanded=True):
            c1, c2 = st.columns(2)
            dl["w_start"] = c1.number_input(
                "w₁ (kN/m)", value=float(dl["w_start"]),
                step=1.0, key=f"dl_ws_{dl['id']}",
                help="Intensity at start",
            )
            dl["w_end"] = c2.number_input(
                "w₂ (kN/m)", value=float(dl["w_end"]),
                step=1.0, key=f"dl_we_{dl['id']}",
                help="Intensity at end",
            )
            c3, c4 = st.columns(2)
            dl["start"] = c3.number_input(
                "x₁ (m)", value=float(min(dl["start"], L)),
                min_value=0.0, max_value=float(L),
                step=0.5, key=f"dl_s_{dl['id']}",
            )
            dl["end"] = c4.number_input(
                "x₂ (m)", value=float(min(dl["end"], L)),
                min_value=0.0, max_value=float(L),
                step=0.5, key=f"dl_e_{dl['id']}",
            )
            if st.button("Remove", key=f"dl_del_{dl['id']}", use_container_width=True):
                to_delete_dl = dl["id"]

    if to_delete_dl:
        st.session_state.dist_loads = [
            d for d in st.session_state.dist_loads if d["id"] != to_delete_dl
        ]
        st.rerun()

    if st.sidebar.button("＋ Add Distributed Load", use_container_width=True):
        st.session_state.dist_loads.append({
            "id": str(uuid.uuid4())[:8],
            "w_start": 10.0,
            "w_end": 10.0,
            "start": round(L * 0.25, 2),
            "end": round(L * 0.75, 2),
        })
        st.session_state.preset_applied = "— select a preset —"
        st.rerun()

    st.sidebar.divider()
    if st.sidebar.button("Clear All Loads", use_container_width=True):
        st.session_state.point_loads = []
        st.session_state.dist_loads = []
        st.session_state.preset_applied = "— select a preset —"
        st.rerun()

    st.sidebar.divider()
    if st.sidebar.button("Quit", use_container_width=True, type="primary"):
        st.stop()


# ── Main area ──────────────────────────────────────────────────────────────────

def _render_main(beam: Beam):
    errors = beam.validate()

    if errors:
        for e in errors:
            st.error(e)
        st.info("Fix the errors above to see the analysis.")
        return

    if not beam.point_loads and not beam.distributed_loads:
        st.info("Add at least one load using the sidebar to see results.")
        return

    try:
        reactions = solve_reactions(beam)
        diagrams = compute_diagrams(beam, reactions)
    except ValueError as exc:
        st.error(f"Solver error: {exc}")
        return

    # ── Numerical summary ──
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Ay", f"{reactions.forces.get('Ay', 0):.2f} kN")
    col2.metric("By", f"{reactions.forces.get('By', 0):.2f} kN")
    col3.metric("Ax", f"{reactions.forces.get('Ax', 0):.2f} kN")
    col4.metric("V max", f"{diagrams.V_max:.2f} kN")
    col5.metric("M max", f"{diagrams.M_max:.2f} kN·m")

    st.divider()

    # ── 4-panel figure ──
    fig = plot_beam_analysis(
        beam, reactions, diagrams,
        title="Interactive Analysis",
        show=False,
    )
    st.pyplot(fig)
    plt.close(fig)  # prevent memory accumulation across reruns

    # ── Equilibrium equations ──
    if reactions.equations:
        st.subheader("Equilibrium Equations")
        for eq in reactions.equations:
            st.latex(eq.strip("$"))


# ── App entry point ────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Beam Solver",
        page_icon="⚙️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Beam Solver")
    st.caption("Statically determinate beam analysis — shear & moment diagrams")

    _init_state()
    _render_sidebar()

    beam = build_beam_from_state()
    _render_main(beam)


if __name__ == "__main__":
    main()
