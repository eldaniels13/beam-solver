# Beam Solver

A Python tool for analyzing statically determinate beams — reactions, shear force diagrams, and bending moment diagrams with visual output.

Originally developed as an academic project (ITESO, 2022). Now rewritten as a modular, portfolio-grade engineering utility with matplotlib visualization and step-by-step equation display.

## Project Structure

```
beam-solver/
├── src/
│   └── beam_solver/           # v3 core package
│       ├── __init__.py
│       ├── model.py           # dataclasses: Beam, Load, Support
│       ├── solver.py          # equilibrium solver, V(x), M(x)
│       ├── plotter.py         # matplotlib: beam schematic + V/M diagrams
│       └── cli.py             # terminal interface (Phase 3)
├── tests/
│   └── test_solver.py         # unit tests
├── archive/                   # original scripts — project history
│   ├── beam_v1_original.py    # first version — basic point + distributed
│   ├── beam_v2_original.py    # second version — trapezoidal decomposition
│   ├── BeamInF.ipynb          # Jupyter notebook with LaTeX equations
│   ├── BeamVyD.txt            # original "Libro de Newton" source
│   ├── Prueba.py              # early verificador test
│   └── fotos_y_videos/        # screenshots and demo recordings
├── main.py                    # entry point: python main.py
├── pyproject.toml             # project config and dependencies
├── README.md
├── LICENSE
└── .gitignore
```

## Features

- Point (concentrated) loads
- Distributed loads: uniform, triangular, trapezoidal
- Support configurations: pin + roller (at ends or offset)
- Reaction calculation via equilibrium (ΣFx=0, ΣFy=0, ΣM=0)
- Shear force and bending moment diagrams (matplotlib)
- Visual beam schematic with supports, load arrows, and reaction arrows
- LaTeX-rendered equilibrium equations on the plot
- Input validation (fixed `verificador` from v2)

## Usage

```bash
python main.py
```

Runs three example beams. Close each plot window to see the next.

## Dependencies

```bash
pip install numpy matplotlib
```

Or with pyproject.toml:

```bash
pip install .
```

## Roadmap

- [x] Modular package structure (model / solver / plotter)
- [x] Point loads + simply supported beams
- [x] Distributed loads (uniform, triangular, trapezoidal)
- [x] Visual beam schematic with supports and load arrows
- [x] LaTeX equation display on plots
- [x] Input validation (verificador v3)
- [ ] Interactive CLI — terminal-based beam input
- [ ] Moment loads (couples)
- [ ] Cantilever and overhang support configurations
- [ ] PNG/PDF export
- [ ] JSON/YAML input files (non-interactive mode)
- [ ] Streamlit or tkinter GUI
- [ ] Statically indeterminate beams (stiffness method)
- [ ] Learning mode: step-by-step walkthrough with theory notes
- [ ] Bilingual UI (ES/EN)

## Background

Written by J. Daniel Garcia Castro. The solver decomposes trapezoidal distributed loads into equivalent resultants using the standard approach taught in statics/structural mechanics courses.
