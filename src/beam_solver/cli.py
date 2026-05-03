"""Command-line interface for beam_solver."""


def main():
    """Dispatch to __main__.main (supports --interactive and --streamlit flags)."""
    from beam_solver.__main__ import main as _main
    _main()
