# Changelog

All notable changes will be documented here.

## [0.1.0] - Unreleased

### Added

- Windows process discovery and connection for Evenicle 2.
- Exact signed 32-bit value scanning and repeat-scan narrowing.
- Guarded writes limited to three or fewer candidate addresses.
- In-app backup warning, version information, and clearer errors.
- Unit tests for numeric validation, scan alignment, and non-mutation.
- PyInstaller build script for a standalone Windows executable.

### Changed

- Removed the unsupported direct-ASD editor from the production project.
- Moved slow first scans to a worker thread to keep the UI responsive.
- Added deterministic cleanup for Windows process and snapshot handles.
