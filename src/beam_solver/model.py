"""Data model for beams, loads, and supports."""

from dataclasses import dataclass, field


@dataclass
class PointLoad:
    """A concentrated force on the beam.

    magnitude: force value in kN (positive = downward)
    position:  distance from left end in m
    """
    magnitude: float
    position: float


@dataclass
class DistributedLoad:
    """A linearly varying distributed load.

    w_start: intensity at start in kN/m (positive = downward)
    w_end:   intensity at end in kN/m
    start:   start coordinate in m
    end:     end coordinate in m

    Uniform load: w_start == w_end
    Triangular:   one of them is 0
    Trapezoidal:  w_start != w_end, both nonzero
    """
    w_start: float
    w_end: float
    start: float
    end: float

    @property
    def length(self) -> float:
        return self.end - self.start

    @property
    def resultant_force(self) -> float:
        """Equivalent concentrated force (positive = downward)."""
        return (self.w_start + self.w_end) / 2 * self.length

    @property
    def resultant_position(self) -> float:
        """Position of equivalent force measured from left end of beam."""
        L = self.length
        if L == 0:
            return self.start
        # Centroid of a trapezoid measured from start
        if self.w_start + self.w_end == 0:
            return self.start + L / 2
        centroid = L * (self.w_start + 2 * self.w_end) / (3 * (self.w_start + self.w_end))
        return self.start + centroid


@dataclass
class Support:
    """A beam support.

    kind: 'pin' (Ax, Ay reactions) or 'roller' (Ay only)
    position: distance from left end in m
    """
    kind: str  # 'pin' or 'roller'
    position: float


@dataclass
class Beam:
    """A horizontal beam with supports and loads."""
    length: float
    supports: list[Support] = field(default_factory=list)
    point_loads: list[PointLoad] = field(default_factory=list)
    distributed_loads: list[DistributedLoad] = field(default_factory=list)

    def validate(self) -> list[str]:
        """Check that all loads and supports are within the beam span.
        Returns list of error messages (empty = valid).
        This is the fixed 'verificador' from v2.
        """
        errors = []
        for i, load in enumerate(self.point_loads):
            if load.position < 0 or load.position > self.length:
                errors.append(
                    f"Point load {i+1} at x={load.position}m "
                    f"is outside beam span [0, {self.length}]m"
                )
        for i, load in enumerate(self.distributed_loads):
            if load.start < 0 or load.end > self.length:
                errors.append(
                    f"Distributed load {i+1} [{load.start}, {load.end}]m "
                    f"is outside beam span [0, {self.length}]m"
                )
            if load.start >= load.end:
                errors.append(
                    f"Distributed load {i+1}: start ({load.start}m) "
                    f"must be less than end ({load.end}m)"
                )
        for i, sup in enumerate(self.supports):
            if sup.position < 0 or sup.position > self.length:
                errors.append(
                    f"Support {i+1} at x={sup.position}m "
                    f"is outside beam span [0, {self.length}]m"
                )
        return errors
