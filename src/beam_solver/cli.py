"""Terminal-based interactive beam input CLI."""

from .model import Beam, PointLoad, DistributedLoad, Support
from .solver import solve_reactions, compute_diagrams


def _prompt(msg: str, cast=str, *, default=None):
    suffix = f" [{default}]" if default is not None else ""
    while True:
        try:
            raw = input(f"  {msg}{suffix}: ").strip()
        except EOFError:
            raise KeyboardInterrupt
        if raw == "" and default is not None:
            return default
        try:
            return cast(raw)
        except (ValueError, TypeError):
            print(f"    Invalid input, expected {cast.__name__}.")


def _add_supports(beam: Beam):
    print("\nSupports  (pin | roller)  — type 'done' when finished")
    while True:
        try:
            raw = input("  kind position (e.g. 'pin 0'): ").strip().lower()
        except EOFError:
            break
        if raw in ("done", ""):
            break
        parts = raw.split()
        if len(parts) != 2 or parts[0] not in ("pin", "roller"):
            print("    Usage: pin <x>  or  roller <x>")
            continue
        try:
            pos = float(parts[1])
        except ValueError:
            print("    Position must be a number.")
            continue
        beam.supports.append(Support(kind=parts[0], position=pos))
        print(f"    + {parts[0]} @ x={pos} m")


def _add_point_loads(beam: Beam):
    print("\nPoint loads  (kN, positive = downward)  — 'done' to skip")
    while True:
        try:
            raw = input("  magnitude position (e.g. '10 3'): ").strip().lower()
        except EOFError:
            break
        if raw in ("done", ""):
            break
        parts = raw.split()
        if len(parts) != 2:
            print("    Usage: <magnitude> <position>")
            continue
        try:
            mag, pos = float(parts[0]), float(parts[1])
        except ValueError:
            print("    Both values must be numbers.")
            continue
        beam.point_loads.append(PointLoad(magnitude=mag, position=pos))
        print(f"    + {mag} kN @ x={pos} m")


def _add_distributed_loads(beam: Beam):
    print("\nDistributed loads  (kN/m)  — 'done' to skip")
    print("  Format: w_start w_end x_start x_end  (uniform: w_start == w_end)")
    while True:
        try:
            raw = input("  w_start w_end x_start x_end: ").strip().lower()
        except EOFError:
            break
        if raw in ("done", ""):
            break
        parts = raw.split()
        if len(parts) != 4:
            print("    Need exactly 4 numbers.")
            continue
        try:
            ws, we, xs, xe = (float(p) for p in parts)
        except ValueError:
            print("    All values must be numbers.")
            continue
        beam.distributed_loads.append(DistributedLoad(w_start=ws, w_end=we, start=xs, end=xe))
        print(f"    + {ws}→{we} kN/m over [{xs}, {xe}] m")


def _print_results(reactions, diagrams):
    print("\n" + "─" * 44)
    print("REACTIONS")
    for name, val in reactions.forces.items():
        print(f"  {name} = {val:+.3f} kN")

    print("\nSHEAR  V(x)")
    print(f"  max = {diagrams.V_max:+.3f} kN   min = {diagrams.V_min:+.3f} kN")

    print("\nBENDING MOMENT  M(x)")
    print(f"  max = {diagrams.M_max:+.3f} kN·m   min = {diagrams.M_min:+.3f} kN·m")
    print("─" * 44)


def main():
    try:
        _run()
    except KeyboardInterrupt:
        print("\nAborted.")


def _run():
    print("\n╔══════════════════════════════╗")
    print("║   beam-solver  —  CLI mode   ║")
    print("╚══════════════════════════════╝")

    length = _prompt("Beam length (m)", float)
    beam = Beam(length=length)

    _add_supports(beam)
    _add_point_loads(beam)
    _add_distributed_loads(beam)

    errors = beam.validate()
    if errors:
        print("\nConfiguration errors:")
        for e in errors:
            print(f"  ✗ {e}")
        return

    try:
        reactions = solve_reactions(beam)
        diagrams = compute_diagrams(beam, reactions)
    except ValueError as exc:
        print(f"\nSolver error: {exc}")
        return

    _print_results(reactions, diagrams)

    try:
        raw = input("\nShow diagram plot? [y/N]: ").strip().lower()
    except EOFError:
        raw = "n"
    if raw == "y":
        from .plotter import plot_beam
        plot_beam(beam, reactions, diagrams)
