# tinker_access_utility — Specification

## Overview

`tinker_access_utility` is a cross-platform Rust rewrite and modernization of `scripts/RFIDTagRegister.py`. It reads tag IDs from a Sparkfun ID-12LA RFID badge reader (USB serial) and exposes that data in two modes:

- **Tray/menu-bar applet** — emits the parsed tag as simulated keystrokes to the focused window, followed by a Tab. This is the "drop badge → tag fills the form field" workflow used to register members.
- **CLI** — prints the parsed tag to stdout only. **Does not** emit keystrokes. Suitable for piping into other tools, debugging, scripting.

This split is deliberate: the original Python conflated console output and keystroke injection, which makes the CLI dangerous to run interactively (any focused window receives keystrokes). Splitting them lets each mode be the right tool.

## Platforms

| Platform | Status |
|---|---|
| Windows | Required |
| macOS | Required |
| Linux | Nice-to-have |

CI should build for all three; release artifacts are required for Windows and macOS.

## Hardware

- Reader: Sparkfun ID-12LA (or compatible) on USB serial.
- **Port discovery**: enumerate available serial ports at runtime via `serialport::available_ports()`. No hardcoded default — the legacy Python's `COM3` default is dropped; on a modern multi-OS tool, hardcoding a Windows COM number is a foot-gun.
  - **Applet**: the tray menu's *Select port…* submenu lists detected ports as a dropdown. The user picks one; the choice persists across launches (config file in the OS-appropriate user config dir).
  - **CLI**: requires `--port <PORT>` to be specified explicitly. A separate `--list-ports` flag enumerates detected ports (one per line, name + description) so users/scripts can discover what's available without launching the applet.
- Frame: 16 bytes — `STX` + 10 ASCII-hex tag chars + 2 ASCII-hex checksum chars + `CR` + `LF` + `ETX`. After `readline()` + `strip()` semantics, what remains is `STX` + 12 hex chars + `ETX`.

## Behavioral Spec

### Parsing (shared between CLI and applet)

Read a line from the serial port. Strip surrounding whitespace/control bytes. Keep characters at indices `[1..13]` — i.e. skip the leading `STX` byte, keep 10 tag chars + 2 checksum chars = **12 chars total**.

This matches `scripts/RFIDTagRegister.py:41` exactly. It is the regression target for unit tests.

If a line is shorter than 13 characters after stripping, treat it as a noise/partial frame and skip it — do not panic, do not emit partial output.

### CLI mode

- Invocation: `tinker_access_utility --port <PORT> [--once]` or `tinker_access_utility --list-ports`
- `--port <PORT>` is **required** when scanning. There is no default; if omitted, exit with a non-zero code and a message pointing the user at `--list-ports`.
- `--list-ports` enumerates detected serial ports (name + description, one per line) and exits `0`. Mutually exclusive with `--port`.
- Scanning behavior: connect to `<PORT>`, loop forever, print each parsed 12-char tag on its own line to stdout. Print connection status to stderr.
- `--once` (optional, decide during impl): exit after the first successful read. Useful for scripts.
- **Does not** emit keystrokes under any circumstances.
- Exit codes: `0` on graceful shutdown (SIGINT) or successful `--list-ports`, non-zero on serial open failure or missing required args.

### Tray applet mode

- Invocation: `tinker_access_utility --tray` (or default when launched via OS autostart / icon).
- Tray icon menu items:
  - **Status** (read-only label): "Connected to COMx" / "Disconnected" / "Last scan: ABC...".
  - **Select port…** (submenu listing detected serial ports).
  - **Pause / Resume** scanning.
  - **Run at startup** (checkbox; persists via OS autostart mechanism).
  - **Quit**.
- On each successful scan: type the 12-char tag via simulated keystrokes, then type Tab. Matches `scripts/RFIDTagRegister.py:43-44`.
- The applet is the only mode that emits keystrokes.

### Run-at-startup

Use the OS-native autostart mechanism (no custom service/daemon):

- **Windows**: registry `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
- **macOS**: `LaunchAgent` plist in `~/Library/LaunchAgents/`.
- **Linux**: `~/.config/autostart/tinker_access_utility.desktop`.

The `auto-launch` crate handles all three. Toggling the checkbox in the tray menu registers/unregisters; the OS is the source of truth for current state.

## Stack

- Rust 2024 edition (already pinned in `Cargo.toml`).
- `serialport` — cross-platform USB serial.
- `enigo` — cross-platform keystroke synthesis.
- `tray-icon` — cross-platform tray/menu-bar icon.
- `clap` — CLI parsing.
- `auto-launch` — OS-native run-at-startup registration.
- Test deps: stdlib `#[test]`, `assert_cmd` for CLI integration tests.

## Module Layout (target)

```
src/
  lib.rs          # re-exports core types
  parse.rs        # pure parsing logic — heavily unit-tested
  reader.rs       # `TagReader` trait + serialport-backed impl + test fake
  cli.rs          # CLI entrypoint (reader → parse → stdout)
  applet/
    mod.rs        # tray entrypoint
    tray.rs       # icon, menu, event loop
    keystrokes.rs # enigo wrapper
    autostart.rs  # auto-launch wrapper
  bin/
    cli.rs        # thin: calls cli::run()
    applet.rs     # thin: calls applet::run()
```

Two binaries (CLI and applet) keep dependencies cleanly partitioned: the CLI binary should not link `enigo` or `tray-icon`. Alternatively, one binary with a `--tray` flag — decide during scaffolding based on binary-size impact.

## Testing Strategy

- **Unit tests** on `parse.rs`: golden inputs from real ID-12LA frames, partial frames, empty lines, oversized lines, non-ASCII garbage. This is the regression target.
- **Reader fake**: `TagReader` trait with an in-memory test impl that yields a scripted sequence of frames. Lets the CLI logic be tested without hardware.
- **CLI integration test** via `assert_cmd`: feed the fake reader, assert stdout contains expected tag lines.
- **Keystroke + tray + autostart**: not unit-testable. Document a manual smoke-test checklist per OS in `tests/MANUAL.md` once those modules exist.

## Non-Goals

- The CLI does not and will not emit keystrokes.
- Not a daemon/service. Run-at-startup uses OS user-session autostart, not system services.
- No tag deduplication logic — the ID-12LA only emits a tag once per badge presentation, so this is unnecessary (per the original Python's comment).
- No server-side integration. This tool only produces tag IDs locally; the existing `tinker_access_server` is unrelated to this utility's scope.

## Open Questions (resolve before or during the relevant phase)

1. **Logging** — file rotation, stderr only, or both? Probably stderr-only is fine for v1.
2. **Reader-disconnect UX in tray** — silent retry forever, or surface a notification? Probably retry-with-backoff and reflect state in the Status label.
3. **Tray icon asset** — Phase 5 ships a solid-blue 16×16 placeholder. Replace with a real asset (macOS prefers a monochrome template image; Windows/Linux are flexible).
4. **Persisted port config location** — `~/.config/tinker_access_utility/config.toml` (XDG) on Linux, `%APPDATA%\tinker_access_utility\config.toml` on Windows, `~/Library/Application Support/tinker_access_utility/config.toml` on macOS. Confirm during applet phase; the `directories` crate handles the per-OS lookup.
5. **Dynamic port refresh in the tray** — Phase 6 builds the *Select port…* submenu once at applet startup; if the user plugs the reader in afterwards, they have to quit and relaunch. Three approaches in increasing effort: (a) add a manual *Refresh ports* menu item that rebuilds the submenu — simplest, ships in one commit; (b) poll `list_ports()` on a timer (every ~2s) and rebuild when the set changes — invisible to the user but burns CPU when idle; (c) subscribe to OS USB hotplug events (libudev on Linux, `WM_DEVICECHANGE` on Windows, IOKit on macOS) — best UX, most platform-specific code. Recommendation: ship (a) first since it unblocks the use-case in a few lines; reach for (c) only if real users complain.

6. **Linux keystroke injection on Wayland** — Diagnosed from a real test on Hyprland (Wayland-only): the full reader → channel → UI-thread → enigo pipeline runs cleanly and `enigo.text(...)` returns `Ok`, but no characters reach the focused window. Cause: enigo 0.6's Linux backend uses `x11rb` to push synthetic X events. Under a pure-Wayland compositor those events go to XWayland's X server, which only forwards them to XWayland clients (Firefox in default mode, GIMP, older Electron apps). Native Wayland windows never see them, and enigo can't detect the failure. Diagnostic log evidence is in `src/applet/reader_loop.rs` and `src/applet/run.rs` — `eprintln!`s tagged `[reader_loop]` and `[applet]` print to stderr; the failing run shows tags being read and "keystroke emission ok" while nothing reaches the window. Three paths forward:

    - **(a) Accept and document.** Linux is "nice-to-have" per platform priorities. Win/Mac use enigo's native backends and work fine. Note in user-facing docs that Linux/Wayland users must focus an XWayland app. Zero code change. Recommended unless a Linux user complains.
    - **(b) ydotool backend.** Add a Linux-only path that talks to a running `ydotoold` daemon over a Unix socket; `ydotoold` writes to `/dev/uinput` which bypasses Wayland and works for any focused window. Cost: an optional dep (`ydotool` crate or hand-rolled socket client), runtime requirement that the user has installed and started `ydotoold`, and `/dev/uinput` permissions (typically a `uinput` group). Heaviest UX setup but most reliable.
    - **(c) enigo Wayland feature / virtual-keyboard protocol.** enigo has experimental Wayland support via the `zwp_virtual_keyboard_v1` protocol. Works on `wlroots`-based compositors (Hyprland, Sway, Niri) but not GNOME (Mutter doesn't expose the protocol to unprivileged clients). Cost: enable the feature, runtime support varies by compositor. Middle ground.

    Pending verification before committing to a path: open Firefox (or any default-XWayland app) on the test machine, focus a text field, scan a badge. If the 12-char tag appears, it confirms the diagnosis end-to-end and rules out any non-Wayland bug. Only then is choosing among (a)/(b)/(c) meaningful.

## Resolved Decisions

- **Two binaries, not one** — `tinker_access_utility` (CLI; no GUI deps referenced from its code path) and `tinker_access_utility_applet` (tray applet). They share the same library crate. Resolved in Phase 5.
- **`dist` (formerly `cargo-dist`) for packaging + CI** — Phase 8. Configured at parent repo root in `dist-workspace.toml` referencing `cargo:tinker_access_utility`; release workflow at `.github/workflows/release.yml`. Targets: `x86_64-pc-windows-msvc`, `aarch64-apple-darwin`, `x86_64-apple-darwin`, `x86_64-unknown-linux-gnu`. Installer: Windows MSI (via WiX, generated WiX defs at `tinker_access_utility/wix/main.wxs`); Mac/Linux ship as `.tar.xz`. Both binaries packaged in every artifact. **Unsigned** — Windows users will see SmartScreen, macOS users will need to right-click → Open or `xattr -d com.apple.quarantine`. Signing is a deliberate follow-up.
- **macOS `.app` bundle + `.dmg`** — Phase 8. Built by `tinker_access_utility/scripts/build-macos-app.sh` and orchestrated by the reusable workflow `.github/workflows/publish-mac-app.yml`, which `dist` invokes as a custom publish-job (`publish-jobs = ["./publish-mac-app"]`). The job builds both Apple targets, `lipo`-merges into a universal binary, and produces `TinkerAccessUtility.app` containing **both** the applet and CLI under `Contents/MacOS/`. Bundle ID `org.tinkermill.tinker-access-utility`. `Info.plist` sets `LSUIElement = true` so the applet runs as a menu-bar agent (no Dock icon). The `.dmg` ships with a `/Applications` symlink for drag-to-install. Icon is generated at build time on the macOS runner via `sips` + `iconutil` from `assets/taicon-app.png` (square 1024×1024 derivation of `taicon.png`). The `.dmg` is uploaded to the GitHub Release alongside dist's `.tar.xz` (CLI users who don't want a `.app` can still grab the tarball).

---

## Development Order

Each phase produces something testable on its own. Stop points are natural — a session can pause after any phase.

### Phase 1 — Parsing core + tests (no I/O)

- Create `src/parse.rs` with a `parse_frame(&str) -> Option<TagId>` function implementing the `[1..13]` slice + length checks.
- Define a `TagId` newtype (12 ASCII chars) with simple validation.
- Write unit tests covering: valid frame, frame missing STX, short frame, empty line, frame with CR/LF still attached, all-whitespace.
- **Done when**: `cargo test` passes, parsing layer has no dependencies beyond stdlib.

### Phase 2 — Reader abstraction + serial impl + port enumeration

- Define `TagReader` trait: `fn next_tag(&mut self) -> io::Result<Option<TagId>>` (returns `None` on timeout, error on hard failure).
- Implement `SerialTagReader` using `serialport`, taking an explicit port name (no default).
- Implement `list_ports()` wrapping `serialport::available_ports()` — returns `(name, description)` pairs. Used by both the CLI's `--list-ports` and the applet's dropdown.
- Implement `FakeTagReader` for tests (vec of scripted lines).
- **Done when**: a small smoke binary or test can read from a real reader on the dev machine and print tags, and `list_ports()` returns sensible output on the dev machine.

### Phase 3 — CLI binary

- Wire `clap` for `--port`, `--list-ports`, `--once`. Enforce `--port` ↔ `--list-ports` mutual exclusion.
- `--list-ports`: call `list_ports()` and print results.
- Otherwise loop: `reader.next_tag()` → print to stdout.
- Handle SIGINT for graceful shutdown.
- Add an `assert_cmd` integration test using the fake reader pattern (may require a `--test-fake` hidden flag or a dependency-injection seam).
- **Done when**: `cargo run -- --list-ports` shows real ports on the dev machine; `cargo run -- --port <real-port>` reads tags; integration test passes on all CI platforms.

### Phase 4 — Keystroke emitter

- Wrap `enigo` in `applet/keystrokes.rs`: `type_tag(&TagId)` types 12 chars then Tab.
- Manually smoke-test on Windows and macOS: focus a text field, run a tiny harness, confirm characters appear correctly (watch for case sensitivity and modifier-key races on macOS).
- **Done when**: manually verified on both required platforms. Document in `tests/MANUAL.md`.

### Phase 5 — Tray applet shell

- New binary (or `--tray` mode) that shows a tray icon with a placeholder menu (Status, Quit).
- No scanning yet — just confirm the icon appears and the menu works on Windows + macOS.
- **Done when**: the icon shows up and quitting works on both platforms.

### Phase 6 — Wire scanning into the applet

- Spawn the reader loop on a background thread.
- Channel scanned `TagId`s to the UI thread; update Status label and call `keystrokes::type_tag`.
- Add Pause/Resume and Select-port menu items.
- **Done when**: presenting a badge while a text editor has focus types the 12-char tag + Tab.

### Phase 7 — Autostart toggle

- Wrap `auto-launch` in `applet/autostart.rs`.
- Add the "Run at startup" checkbox to the tray menu; reflect current OS state on launch.
- **Done when**: toggling the checkbox creates/removes the registry entry / LaunchAgent / .desktop file, and the app launches on next login.

### Phase 8 — Packaging + CI

- Windows: produce a signed `.exe` (or `.msi` if installer is preferred).
- macOS: produce a `.app` bundle, code-signed and notarized if distributing externally.
- CI matrix building all three OSes; cache cargo registry.
- **Done when**: a tagged release produces downloadable artifacts for Windows and macOS.

### Phase 9 — Linux best-effort

- Verify everything compiles and runs on Linux.
- Tray-icon support on Linux is uneven (depends on desktop environment / `libayatana-appindicator`); document known-good DEs.
- **Done when**: documented support level and any known limitations.

---

## Picking Up in a New Session

If a future session starts cold:

1. Read this file (`SPEC.md`) for the contract.
2. Read `scripts/RFIDTagRegister.py` for the original behavioral source of truth (specifically lines 41–44).
3. Check which phase is in progress by looking at `src/` — phases roughly map to the modules listed under **Module Layout**.
4. Phase 1's `parse.rs` is the easiest entry point if no code exists yet.
