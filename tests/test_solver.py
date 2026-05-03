"""Basic tests for beam_solver."""

import sys
sys.path.insert(0, "src")

from beam_solver.model import Beam, PointLoad, DistributedLoad, Support
from beam_solver.solver import solve_reactions, compute_diagrams


def test_simply_supported_midspan_point_load():
    """Symmetric point load → equal reactions."""
    beam = Beam(
        length=6.0,
        supports=[Support("pin", 0.0), Support("roller", 6.0)],
        point_loads=[PointLoad(10.0, 3.0)],
    )
    r = solve_reactions(beam)
    assert abs(r.forces["Ay"] - 5.0) < 1e-10
    assert abs(r.forces["By"] - 5.0) < 1e-10
    assert r.forces["Ax"] == 0.0


def test_simply_supported_uniform_load():
    """Uniform load over full span → equal reactions = qL/2."""
    beam = Beam(
        length=5.0,
        supports=[Support("pin", 0.0), Support("roller", 5.0)],
        distributed_loads=[DistributedLoad(30.0, 30.0, 0.0, 5.0)],
    )
    r = solve_reactions(beam)
    assert abs(r.forces["Ay"] - 75.0) < 1e-10
    assert abs(r.forces["By"] - 75.0) < 1e-10


def test_asymmetric_point_load():
    """Point load at 1/3 span → Ay = 2P/3, By = P/3."""
    beam = Beam(
        length=6.0,
        supports=[Support("pin", 0.0), Support("roller", 6.0)],
        point_loads=[PointLoad(12.0, 2.0)],
    )
    r = solve_reactions(beam)
    assert abs(r.forces["Ay"] - 8.0) < 1e-10
    assert abs(r.forces["By"] - 4.0) < 1e-10


def test_validation_catches_out_of_bounds():
    """Load outside beam span should produce errors."""
    beam = Beam(
        length=5.0,
        supports=[Support("pin", 0.0), Support("roller", 5.0)],
        point_loads=[PointLoad(10.0, 7.0)],
    )
    errors = beam.validate()
    assert len(errors) == 1
    assert "outside beam span" in errors[0]


def test_diagrams_shape():
    """Diagram arrays should have the right length and V=0 at ends for UDL."""
    beam = Beam(
        length=5.0,
        supports=[Support("pin", 0.0), Support("roller", 5.0)],
        distributed_loads=[DistributedLoad(30.0, 30.0, 0.0, 5.0)],
    )
    r = solve_reactions(beam)
    d = compute_diagrams(beam, r, n_points=100)
    assert len(d.x) == 100
    assert len(d.V) == 100
    assert len(d.M) == 100
    # V should be ~0 at midspan for symmetric UDL
    mid_idx = 50
    assert abs(d.V[mid_idx]) < 1.0  # within discretization tolerance


if __name__ == "__main__":
    test_simply_supported_midspan_point_load()
    test_simply_supported_uniform_load()
    test_asymmetric_point_load()
    test_validation_catches_out_of_bounds()
    test_diagrams_shape()
    print("All tests passed!")
