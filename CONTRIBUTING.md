# Contributing

Thanks for helping improve the Evenicle 2 Live Stat Editor.

## Development setup

1. Use Windows 10 or 11 with Python 3.10 or newer.
2. Clone the repository and create a virtual environment: `python -m venv .venv`.
3. Activate it with `.venv\Scripts\activate`.
4. Install development tools with `python -m pip install -e ".[dev]"`.
5. Run tests with `python -m unittest discover -s tests -v`.
6. Start the source version with `python evenicle2_live_editor.py`.

## Code conventions

- Keep runtime dependencies at zero unless a dependency clearly improves safety or reliability.
- Add docstrings for public functions and classes.
- Keep Windows API calls isolated in `WindowsProcessMemory` so pure logic remains testable.
- Add tests for new parsing, scanning, filtering, or validation behavior.
- Never commit save files, memory dumps, credentials, or personal filesystem paths.

## Bug reports

Use the bug-report issue template. Include the game store/version, Windows version, application
version, exact steps, and the complete error message. Do not attach save files or memory dumps
unless you have checked them for personal or sensitive data.

## Pull requests

Keep changes focused, explain user-visible behavior, and include test results. By submitting a
pull request, you agree that your contribution may be distributed under the project's license
once the repository owner selects and adds one.
