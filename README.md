# Beam Solver

A Python tool for analyzing statically determinate beams — reactions, shear force diagrams, and bending moment diagrams with visual output.

Originally developed as an academic project (ITESO, 2022). Rewritten as a modular, portfolio-grade engineering utility with three interfaces: terminal CLI, matplotlib interactive editor, and Streamlit web app.

## Project Structure

```
beam-solver/
├── src/
│   └── beam_solver/           # core package
│       ├── __init__.py
│       ├── __main__.py        # entry point dispatcher
│       ├── model.py           # dataclasses: Beam, PointLoad, DistributedLoad, Support
│       ├── solver.py          # equilibrium solver, V(x), M(x)
│       ├── plotter.py         # matplotlib: beam schematic + V/M diagrams
│       ├── cli.py             # terminal interactive mode
│       ├── interactive.py     # matplotlib click-to-place editor
│       └── app_streamlit.py   # Streamlit web app
├── tests/
│   └── test_solver.py
├── archive/                   # original scripts — project history
│   ├── beam_v1_original.py
│   ├── beam_v2_original.py
│   ├── BeamInF.ipynb
│   ├── BeamVyD.txt
│   ├── Prueba.py
│   └── fotos_y_videos/
├── streamlit_app.py           # convenience launcher: streamlit run streamlit_app.py
├── main.py                    # demo: runs three example beams
├── pyproject.toml
├── README.md
└── .gitignore
```

## Usage

### Terminal CLI (default)

```bash
uv run python -m beam_solver
# or
beam_solver
```

Prompts for beam length, supports, point loads, and distributed loads. Prints reactions and V/M extremes. Optional plot at the end.

### Matplotlib interactive editor

```bash
uv run python -m beam_solver --interactive
```

Click to place supports and loads on a graphical beam canvas. Solve and display diagrams without leaving the desktop.

### Streamlit web app

```bash
uv run python -m beam_solver --streamlit
# or
streamlit run streamlit_app.py
```

Browser-based form UI. Displays reaction equations and interactive V/M diagrams.

### Demo (three example beams)

```bash
uv run python main.py
```

## Features

- Point (concentrated) loads
- Distributed loads: uniform, triangular, trapezoidal
- Support configurations: pin + roller (at arbitrary positions)
- Reaction calculation via equilibrium (ΣFx=0, ΣFy=0, ΣM=0)
- Shear force and bending moment diagrams
- Visual beam schematic with supports, load arrows, and reaction labels
- LaTeX-rendered equilibrium equations on the plot
- Input validation (fixed `verificador` from v2)
- Three independent interfaces: CLI, matplotlib editor, Streamlit

## Installation

```bash
# Standard
pip install .

# With Streamlit
pip install ".[streamlit]"

# With uv
uv sync
uv sync --extra streamlit
```

## Roadmap

- [x] Modular package structure (model / solver / plotter)
- [x] Point loads + simply supported beams
- [x] Distributed loads (uniform, triangular, trapezoidal)
- [x] Visual beam schematic with supports and load arrows
- [x] LaTeX equation display on plots
- [x] Input validation (verificador v3)
- [x] Interactive CLI — terminal-based beam input
- [x] Matplotlib click-to-place interactive editor
- [x] Streamlit web app
- [ ] Moment loads (couples)
- [ ] Cantilever and overhang support configurations
- [ ] PNG/PDF export
- [ ] JSON/YAML input files (non-interactive mode)
- [ ] Statically indeterminate beams (stiffness method)
- [ ] Learning mode: step-by-step walkthrough with theory notes
- [ ] Bilingual UI (ES/EN)

## Background

Written by J. Daniel Garcia Castro. The solver decomposes trapezoidal distributed loads into equivalent resultants using the standard approach from statics and structural mechanics.
