# Evenicle 2 Live Stat Editor

A small Windows utility for changing numeric values in a running copy of **Evenicle 2**. It
scans for a value displayed by the game, narrows the results after that value changes, and
writes a replacement. You then use the game's normal Save command, allowing the game to write
its own native save format.

> **Prerelease software:** back up your saves before use. Edit only values you can verify and
> keep them within ranges the game normally supports.

This is an unofficial community project. It is not affiliated with or endorsed by AliceSoft or
the game's publishers. No game files or third-party assets are included.

## Features

- Finds exact signed 32-bit values such as money, EXP, HP, or skill points.
- Narrows results after a value changes in-game.
- Refuses to write until no more than three candidate addresses remain.
- Keeps long scans off the interface thread.
- Uses the game itself to persist changes; it does not overwrite save files directly.
- Contains no networking, telemetry, analytics, or automatic updates.
- Available as a standalone Windows executable with no Python installation required.

## Supported systems and versions

- Windows 10 and Windows 11, 64-bit.
- Evenicle 2 releases whose running process name contains `Evenicle2`, or both `Evenicle` and
  `2`.

The current release is not confirmed against every Steam, GOG, JAST, or Japanese game build.
macOS and Linux are not supported because the application uses the Windows process-memory API.

## Download and installation

After a GitHub release is published:

1. Download `Evenicle-2-Save-Editor.exe` and `SHA256SUMS.txt` from the release page.
2. Optionally verify the download with
   `Get-FileHash .\Evenicle-2-Save-Editor.exe -Algorithm SHA256` in PowerShell.
3. Put the executable in any folder. Installation is not required.

Windows SmartScreen may warn about an unsigned executable from a new project. Verify the
checksum and download only from the project's official GitHub Releases page. The current build
is not code-signed.

## Usage

1. Back up the Evenicle 2 save folder.
2. Start Evenicle 2 and load the save you want to change.
3. Run the editor and select **Connect to Evenicle 2**.
4. Enter the exact value currently displayed by the game and select **First scan**.
5. Change that value in-game—for example, spend money, gain EXP, or take damage.
6. Enter the changed value and select **Next scan**.
7. Repeat steps 5–6 until the editor reports between one and three candidates.
8. Enter the desired value and select **Write value**.
9. Verify the value in-game, then save through the game's normal Save menu.

## Why it edits live memory

Evenicle 2's main saves use AliceSoft's encrypted and compressed ASD envelope containing a
version-14 `RSM` resume state. The released `alice-tools` version tested during development can
decode the envelope but does not parse that resume format. Writing an assumed older layout
would risk corrupting saves. This editor therefore avoids direct serialization and lets the game
produce the final save.

## Known limitations

- It is a live-memory editor, not a direct offline save-file editor.
- Only exact signed 32-bit integer searches are supported.
- Some displayed values may be calculated, encoded, duplicated, or stored in another type.
- A stat often must be changed naturally in-game one or more times to isolate its address.
- Addresses are not retained between game sessions.
- Antivirus products may scrutinize the executable because reading and writing another process
  is the application's core function.
- The release is intentionally versioned `0.1.0` until end-to-end testing covers more game builds.

## Troubleshooting

**The editor cannot find the game**

Load a save before connecting. If the executable uses an unexpected process name, open an issue
and include that name—do not include a memory dump.

**Windows denied access**

Close the editor and run it as administrator. The game and editor should run under the same
Windows account and privilege level.

**Too many candidates remain**

Change the value again in-game, enter the new value, and select **Next scan**. The editor will
not write while more than three matches remain.

**The value did not persist**

Confirm the changed value in-game, then create a normal game save before exiting. Some values may
be recalculated by game logic and are not suitable for exact-memory editing.

## Run or build from source

Python 3.10 or newer with Tkinter is required for source development.

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python evenicle2_live_editor.py
```

To create the standalone executable:

```powershell
.\build.ps1
```

The executable and checksum file are written to `release\`. Builds are platform-specific; the
Windows build script does not produce or claim macOS/Linux support.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports should identify the editor version, Windows
version, game storefront/build, process name, and reproducible steps. Never commit or publicly
attach save files, memory dumps, credentials, or personal filesystem paths.

## License

Released under the [MIT License](LICENSE). The project contains original standard-library
Python code and redistributes no AliceSoft or `alice-tools` code. Standalone builds use the
PyInstaller bootloader under PyInstaller's GPL license exception.
