"""Beam Solver v3 — entry point.

Run this file to test the solver with example beams.
Usage: python main.py
"""

import sys
sys.path.insert(0, "src")

from beam_solver.model import Beam, PointLoad, DistributedLoad, Support
from beam_solver.solver import solve_reactions, compute_diagrams
from beam_solver.plotter import plot_beam_analysis


def example_point_load():
    """Simply supported beam with a single point load at midspan."""
    beam = Beam(
        length=6.0,
        supports=[
            Support(kind="pin", position=0.0),
            Support(kind="roller", position=6.0),
        ],
        point_loads=[
            PointLoad(magnitude=10.0, position=3.0),
        ],
    )

    reactions = solve_reactions(beam)
    diagrams = compute_diagrams(beam, reactions)

    print("=== Simply Supported Beam — Point Load at Midspan ===")
    print(f"  Beam length: {beam.length} m")
    print(f"  Load: {beam.point_loads[0].magnitude} kN at x={beam.point_loads[0].position} m")
    for name, value in reactions.forces.items():
        print(f"  {name} = {value:.2f} kN")
    print()

    plot_beam_analysis(beam, reactions, diagrams,
                       title="Simply Supported — 10 kN Point Load at Midspan")


def example_uniform_distributed():
    """Simply supported beam with uniform distributed load (like the notebook)."""
    beam = Beam(
        length=5.0,
        supports=[
            Support(kind="pin", position=0.0),
            Support(kind="roller", position=5.0),
        ],
        distributed_loads=[
            DistributedLoad(w_start=30.0, w_end=30.0, start=0.0, end=5.0),
        ],
    )

    reactions = solve_reactions(beam)
    diagrams = compute_diagrams(beam, reactions)

    print("=== Simply Supported Beam — Uniform Load 30 kN/m ===")
    print(f"  Beam length: {beam.length} m")
    print(f"  Load: {beam.distributed_loads[0].w_start} kN/m over full span")
    for name, value in reactions.forces.items():
        print(f"  {name} = {value:.2f} kN")
    print()

    plot_beam_analysis(beam, reactions, diagrams,
                       title="Simply Supported — 30 kN/m Uniform Load (Notebook Example)")


def example_combined():
    """Beam with both point and distributed loads."""
    beam = Beam(
        length=8.0,
        supports=[
            Support(kind="pin", position=0.0),
            Support(kind="roller", position=8.0),
        ],
        point_loads=[
            PointLoad(magnitude=15.0, position=2.0),
            PointLoad(magnitude=10.0, position=6.0),
        ],
        distributed_loads=[
            DistributedLoad(w_start=5.0, w_end=5.0, start=3.0, end=5.0),
        ],
    )

    reactions = solve_reactions(beam)
    diagrams = compute_diagrams(beam, reactions)

    print("=== Combined Loading ===")
    print(f"  Beam length: {beam.length} m")
    print(f"  Point loads: 15 kN @ 2m, 10 kN @ 6m")
    print(f"  Distributed: 5 kN/m from 3m to 5m")
    for name, value in reactions.forces.items():
        print(f"  {name} = {value:.2f} kN")
    print()

    plot_beam_analysis(beam, reactions, diagrams,
                       title="Combined — Point + Distributed Loads")


if __name__ == "__main__":
    print("Beam Solver v3 — Phase 1 Examples")
    print("Close each plot window to see the next example.\n")

    example_point_load()
    example_uniform_distributed()
    example_combined()
