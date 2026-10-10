"""Windows live-memory stat editor for Evenicle 2.

Evenicle 2's version-14 RSM resume saves are not supported by released
AliceSoft tooling. This application changes a value in the running game and
leaves serialization to the game itself.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import struct
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Iterable

APP_NAME = "Evenicle 2 Live Stat Editor"
APP_VERSION = "0.1.0"
MAX_SAFE_RESULTS = 3
MAX_REGION_SIZE = 256 * 1024 * 1024
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
TH32CS_SNAPPROCESS = 0x00000002
MEM_COMMIT = 0x1000
PAGE_NOACCESS = 0x01
PAGE_GUARD = 0x100
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class ProcessEntry32(ctypes.Structure):
    """Windows PROCESSENTRY32A structure used for process enumeration."""

    _fields_ = [
        ("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260),
    ]


class MemoryBasicInformation(ctypes.Structure):
    """64-bit Windows MEMORY_BASIC_INFORMATION structure."""

    _fields_ = [
        ("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD), ("PartitionId", wintypes.WORD),
        ("RegionSize", ctypes.c_size_t), ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD),
    ]


def parse_int32(text: str) -> int:
    """Parse a signed 32-bit decimal value with a clear validation error."""

    try:
        value = int(text.strip(), 10)
    except ValueError as exc:
        raise ValueError("Enter a whole number, such as 2500 or -10.") from exc
    if not -(2**31) <= value < 2**31:
        raise ValueError("The value must be between -2,147,483,648 and 2,147,483,647.")
    return value


def find_aligned_int32(data: bytes, value: int, base_address: int = 0) -> list[int]:
    """Return four-byte-aligned addresses matching ``value`` in ``data``."""

    needle = struct.pack("<i", value)
    matches: list[int] = []
    offset = 0
    while True:
        offset = data.find(needle, offset)
        if offset < 0:
            return matches
        if (base_address + offset) % 4 == 0:
            matches.append(base_address + offset)
        offset += 4


class WindowsProcessMemory:
    """Explicit wrapper around the Windows process-memory APIs."""

    def __init__(self) -> None:
        if not hasattr(ctypes, "WinDLL"):
            raise OSError("This application supports Windows only.")
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.handle: int | None = None
        self.pid: int | None = None
        self.name: str | None = None
        self._configure_signatures()

    def _configure_signatures(self) -> None:
        """Declare pointer-sized signatures to avoid truncation on 64-bit Windows."""

        k32 = self.kernel32
        k32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        k32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry32)]
        k32.Process32FirstW.restype = wintypes.BOOL
        k32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry32)]
        k32.Process32NextW.restype = wintypes.BOOL
        k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.CloseHandle.argtypes = [wintypes.HANDLE]
        k32.CloseHandle.restype = wintypes.BOOL
        k32.VirtualQueryEx.argtypes = [
            wintypes.HANDLE, ctypes.c_void_p, ctypes.POINTER(MemoryBasicInformation), ctypes.c_size_t
        ]
        k32.VirtualQueryEx.restype = ctypes.c_size_t
        k32.ReadProcessMemory.argtypes = [
            wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        k32.ReadProcessMemory.restype = wintypes.BOOL
        k32.WriteProcessMemory.argtypes = [
            wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        k32.WriteProcessMemory.restype = wintypes.BOOL

    def enumerate_processes(self) -> list[tuple[int, str]]:
        """List running process IDs and executable names."""

        snapshot = self.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snapshot == INVALID_HANDLE_VALUE:
            raise ctypes.WinError(ctypes.get_last_error())
        result: list[tuple[int, str]] = []
        entry = ProcessEntry32()
        entry.dwSize = ctypes.sizeof(entry)
        try:
            has_entry = self.kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
            while has_entry:
                result.append((entry.th32ProcessID, entry.szExeFile))
                has_entry = self.kernel32.Process32NextW(snapshot, ctypes.byref(entry))
        finally:
            self.kernel32.CloseHandle(snapshot)
        return result

    def connect(self) -> tuple[int, str]:
        """Connect to the first process whose name clearly identifies Evenicle 2."""

        candidates = [
            process for process in self.enumerate_processes()
            if "evenicle2" in process[1].lower()
            or ("evenicle" in process[1].lower() and "2" in process[1])
        ]
        if not candidates:
            raise RuntimeError("Evenicle 2 was not found. Start the game and load a save first.")
        self.close()
        self.pid, self.name = candidates[0]
        access = PROCESS_QUERY_INFORMATION | PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION
        self.handle = self.kernel32.OpenProcess(access, False, self.pid)
        if not self.handle:
            self.pid = self.name = None
            raise PermissionError(
                "Windows denied access to the game. Close the editor and run it as administrator."
            )
        return self.pid, self.name

    def close(self) -> None:
        """Release the Windows process handle, if one is open."""

        if self.handle:
            self.kernel32.CloseHandle(self.handle)
        self.handle = self.pid = self.name = None

    def require_handle(self) -> int:
        """Return the active handle or raise a user-facing error."""

        if not self.handle:
            raise RuntimeError("Connect to the running game first.")
        return self.handle

    def read(self, address: int, size: int) -> bytes:
        """Read bytes, returning an empty value for an unreadable page."""

        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t()
        ok = self.kernel32.ReadProcessMemory(
            self.require_handle(), ctypes.c_void_p(address), buffer, size, ctypes.byref(bytes_read)
        )
        return buffer.raw[: bytes_read.value] if ok else b""

    def iter_readable_regions(self) -> Iterable[tuple[int, int]]:
        """Yield committed readable ranges, capped to avoid huge allocations."""

        handle = self.require_handle()
        address = 0
        info = MemoryBasicInformation()
        while self.kernel32.VirtualQueryEx(
            handle, ctypes.c_void_p(address), ctypes.byref(info), ctypes.sizeof(info)
        ):
            base, size = info.BaseAddress or 0, info.RegionSize
            if (info.State == MEM_COMMIT and not info.Protect & (PAGE_GUARD | PAGE_NOACCESS)
                    and 0 < size <= MAX_REGION_SIZE):
                yield base, size
            next_address = base + size
            if next_address <= address:
                break
            address = next_address

    def scan(self, value: int) -> list[int]:
        """Find aligned signed 32-bit occurrences across readable memory."""

        matches: list[int] = []
        for base, size in self.iter_readable_regions():
            matches.extend(find_aligned_int32(self.read(base, size), value, base))
        return matches

    def filter_matches(self, addresses: Iterable[int], value: int) -> list[int]:
        """Keep candidate addresses that still contain ``value``."""

        expected = struct.pack("<i", value)
        return [address for address in addresses if self.read(address, 4) == expected]

    def write(self, addresses: Iterable[int], value: int) -> int:
        """Write ``value`` and return the number of successful writes."""

        handle = self.require_handle()
        raw = struct.pack("<i", value)
        written_count = 0
        for address in addresses:
            bytes_written = ctypes.c_size_t()
            ok = self.kernel32.WriteProcessMemory(
                handle, ctypes.c_void_p(address), raw, len(raw), ctypes.byref(bytes_written)
            )
            if ok and bytes_written.value == len(raw):
                written_count += 1
        return written_count


class EditorApp(tk.Tk):
    """Tkinter interface for the scan, narrow, write, and in-game-save flow."""

    def __init__(self, memory: WindowsProcessMemory | None = None) -> None:
        super().__init__()
        self.memory = memory or WindowsProcessMemory()
        self.matches: list[int] = []
        self.current_value = tk.StringVar()
        self.new_value = tk.StringVar()
        self.status = tk.StringVar(value="Start Evenicle 2, load a save, then select Connect.")
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry("790x500")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=18)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=APP_NAME, font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(frame, text=f"Version {APP_VERSION} · Windows", foreground="#555").pack(anchor="w")
        ttk.Label(frame, text="Back up your save first. Save normally in-game after editing.",
                  foreground="#9b1c1c").pack(anchor="w", pady=(8, 14))
        connection = ttk.Frame(frame)
        connection.pack(fill="x")
        self.connect_button = ttk.Button(connection, text="Connect to Evenicle 2", command=self._connect)
        self.connect_button.pack(side="left")
        self.process_label = ttk.Label(connection, text="Not connected")
        self.process_label.pack(side="left", padx=12)
        scan = ttk.LabelFrame(frame, text="1. Find the value", padding=14)
        scan.pack(fill="x", pady=16)
        ttk.Label(scan, text="Exact value currently shown in-game").grid(row=0, column=0, sticky="w")
        ttk.Entry(scan, textvariable=self.current_value, width=24).grid(row=1, column=0, padx=(0, 12))
        self.first_button = ttk.Button(scan, text="First scan", command=self._first_scan)
        self.first_button.grid(row=1, column=1, padx=4)
        self.next_button = ttk.Button(scan, text="Next scan", command=self._next_scan)
        self.next_button.grid(row=1, column=2, padx=4)
        ttk.Button(scan, text="Reset", command=self._reset).grid(row=1, column=3, padx=4)
        ttk.Label(scan, text="Change the value in-game after the first scan, enter the new value, "
                  "then select Next scan. Repeat until 1–3 candidates remain.",
                  wraplength=710).grid(row=2, column=0, columnspan=4, sticky="w", pady=(12, 0))
        write = ttk.LabelFrame(frame, text="2. Change the value", padding=14)
        write.pack(fill="x")
        ttk.Label(write, text="Desired value").pack(side="left")
        ttk.Entry(write, textvariable=self.new_value, width=24).pack(side="left", padx=10)
        self.write_button = ttk.Button(write, text="Write value", command=self._write_value)
        self.write_button.pack(side="left")
        ttk.Label(frame, textvariable=self.status, wraplength=735).pack(anchor="w", pady=16)
        ttk.Label(frame, text="Only edit values you can verify. The editor refuses to write while "
                  "more than three candidates remain.", foreground="#555", wraplength=735).pack(anchor="w")

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        for button in (self.connect_button, self.first_button, self.next_button, self.write_button):
            button.configure(state=state)

    def _connect(self) -> None:
        try:
            pid, name = self.memory.connect()
            self.matches.clear()
            self.process_label.configure(text=f"{name} (PID {pid})")
            self.status.set("Connected. Enter the exact value currently displayed in the game.")
        except (OSError, RuntimeError) as exc:
            messagebox.showerror("Connection failed", str(exc))

    def _first_scan(self) -> None:
        try:
            value = parse_int32(self.current_value.get())
            self.memory.require_handle()
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Cannot scan", str(exc))
            return
        self._set_busy(True)
        self.status.set("Scanning game memory…")

        def worker() -> None:
            try:
                matches = self.memory.scan(value)
                self.after(0, lambda: self._finish_first_scan(matches))
            except Exception as exc:
                self.after(0, lambda error=exc: self._background_error(error))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_first_scan(self, matches: list[int]) -> None:
        self.matches = matches
        self._set_busy(False)
        self.status.set(f"Found {len(matches):,} candidates. Change the value in-game, "
                        "enter its new value, then select Next scan.")

    def _next_scan(self) -> None:
        try:
            value = parse_int32(self.current_value.get())
            if not self.matches:
                raise RuntimeError("There are no candidates. Run First scan before narrowing results.")
            self.matches = self.memory.filter_matches(self.matches, value)
            suffix = " Ready to write." if 0 < len(self.matches) <= MAX_SAFE_RESULTS else " Repeat after another change."
            self.status.set(f"{len(self.matches):,} candidates remain.{suffix}")
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Cannot narrow scan", str(exc))

    def _write_value(self) -> None:
        try:
            value = parse_int32(self.new_value.get())
            if not self.matches:
                raise RuntimeError("There are no candidates to write. Complete a scan first.")
            if len(self.matches) > MAX_SAFE_RESULTS:
                raise RuntimeError(f"{len(self.matches):,} candidates remain. Narrow the scan to "
                                   f"{MAX_SAFE_RESULTS} or fewer before writing.")
            if not messagebox.askyesno("Confirm memory edit", f"Write {value} to "
                                       f"{len(self.matches)} candidate address(es)?\n\n"
                                       "Verify the result in-game before saving."):
                return
            written = self.memory.write(self.matches, value)
            if written != len(self.matches):
                raise RuntimeError(f"Windows wrote {written} of {len(self.matches)} values. "
                                   "The game may have closed or changed state.")
            self.status.set(f"Wrote {value}. Verify it in-game, then use the game's normal Save command.")
        except (OSError, ValueError, RuntimeError) as exc:
            messagebox.showerror("Write failed", str(exc))

    def _background_error(self, exc: Exception) -> None:
        self._set_busy(False)
        messagebox.showerror("Scan failed", str(exc))
        self.status.set("The scan failed. Reconnect if the game was restarted or closed.")

    def _reset(self) -> None:
        self.matches.clear()
        self.status.set("Scan reset. Enter the current value and select First scan.")

    def _on_close(self) -> None:
        self.memory.close()
        self.destroy()


def main() -> None:
    """Start the graphical application."""

    EditorApp().mainloop()


if __name__ == "__main__":
    main()
