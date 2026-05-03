"""Allow `python -m beam_solver [--interactive | --streamlit]`."""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="beam_solver",
        description="Beam Solver v3 — statically determinate beam analysis",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--interactive",
        action="store_true",
        help="Launch matplotlib interactive mode (no extra deps required)",
    )
    group.add_argument(
        "--streamlit",
        action="store_true",
        help="Launch Streamlit web app (requires: pip install beam-solver[streamlit])",
    )
    args = parser.parse_args()

    if args.interactive:
        from .interactive import run_interactive
        run_interactive()

    elif args.streamlit:
        try:
            import streamlit  # noqa: F401
        except ImportError:
            print(
                "Streamlit is not installed.\n"
                "Install it with:  pip install 'beam-solver[streamlit]'\n"
                "  or:             pip install streamlit",
                file=sys.stderr,
            )
            sys.exit(1)

        import subprocess
        from pathlib import Path

        app_path = Path(__file__).parent / "app_streamlit.py"
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(app_path)],
            check=True,
        )

    else:
        from .cli import main as cli_main
        cli_main()


if __name__ == "__main__":
    main()
