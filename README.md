# Beam Solver

A Python tool for calculating reactions, shear force, and bending moment in statically determinate horizontal beams.

Originally developed as an academic project (ITESO, 2022) to automate what would otherwise be tedious manual equilibrium calculations. Now being expanded into a full engineering utility with GUI and visualization.

## Current features

- Point (concentrated) loads
- Distributed loads: uniform, triangular, trapezoidal
- Support configurations: pinned-roller (ends or offset), fixed-end
- Reaction calculation via equilibrium equations (ΣF=0, ΣM=0)
- Shear force and bending moment diagram output (matplotlib)

## Roadmap

- [ ] Merge `beam_v1` and `beam_v2` into unified `beam_solver.py`
- [ ] Streamlit GUI — load input, beam visualization, V and M diagrams side by side
- [ ] JSON/YAML input file support (non-interactive mode)
- [ ] Multiple load types in a single run with a visual beam diagram showing applied loads
- [ ] Moment loads (couples)
- [ ] Statically indeterminate beams (requires stiffness method or scipy)
- [ ] Export results to PDF report
- [ ] Bilingual UI (ES/EN)
- [ ] Learning mode: step-by-step solution walkthrough with theory notes

## Usage (current — interactive CLI)

```bash
python beam_v2_original.py
```

Inputs are entered interactively. Units: kN and meters.

## Project structure

```
beam-solver/
├── beam_v1_original.py     # first version — point + distributed loads
├── beam_v2_original.py     # second version — adds distributed load decomposition
├── requirements.txt
└── README.md
```

## Background

Written by J. Daniel Garcia Castro as part of structural mechanics coursework. The solver decomposes trapezoidal distributed loads into triangle + rectangle resultants, which is the standard approach taught in statics courses.

## Dependencies

```bash
pip install -r requirements.txt
```
