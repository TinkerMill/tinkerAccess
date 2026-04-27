# Manual smoke-test checklists

Phases that touch the OS keyboard, tray, or autostart hooks can't be unit
tested. Run these checklists when you bring the build up on a new platform.

Build the applet binary on the target OS:

```
cargo build --release --bin tinker_access_utility_applet
```

Launch it manually for these tests (don't enable autostart yet):

```
./target/release/tinker_access_utility_applet
```

## Phase 4 — Keystroke emitter (enigo)

For each of: **Windows**, **macOS**, (Linux nice-to-have).

1. Open a plain text editor (Notepad / TextEdit / gedit) and put the cursor in a focused text field.
2. Pick a port from the tray's *Select port…* submenu.
3. Present a known badge to the ID-12LA reader.
4. Confirm: the 12-char tag appears in the editor exactly as the Python script would have typed it.
5. Confirm: a Tab is typed after the tag (cursor advances / focus moves to the next field if there is one).
6. Repeat with 3+ different badges to confirm no garbled characters or stuck modifier keys.

**macOS gotcha:** first run will prompt for Accessibility permission. Grant it via System Settings → Privacy & Security → Accessibility, then relaunch the applet.

## Phase 5 — Tray applet shell

1. Launch the applet. Confirm a tray icon (solid blue 16×16 placeholder) appears in the menu bar (macOS) / system tray (Windows) / status area (Linux).
2. Open the menu. Confirm items: *Status: Idle…*, *Select port…*, *Pause*, *Run at startup*, *Quit*.
3. Click *Quit*. Process exits cleanly (no orphaned tray icon, exit code 0).

## Phase 6 — Scanning + port selection + pause

1. Launch the applet with the ID-12LA plugged in.
2. Confirm *Select port…* lists at least the reader's port. (Windows shows `COMx`, macOS `/dev/tty.usbserial-XXX`, Linux `/dev/ttyUSBx`.)
3. Pick the reader's port. Status updates to *Reading from <port>*.
4. Present a badge with the keystroke target (text editor) focused. Tag is typed + Tab. Status updates to *Last scan <tag>*.
5. Toggle *Pause*. Status updates to *Paused*. Present a badge — no keystrokes appear.
6. Toggle *Pause* off. Status updates to *Reading…*. Next badge presentation types again.
7. Pick a different port (or pick the same one again). Status updates accordingly; no thread leak (check Activity Monitor / Task Manager — only one applet process, only one extra worker thread).
8. Unplug the reader mid-session. Status reflects an error after the next read attempt.

## Phase 7 — Autostart

For each OS:

1. Launch the applet. *Run at startup* should be unchecked initially (assuming no prior install).
2. Click *Run at startup* — checkbox becomes checked.
3. Verify the OS-native artifact:
   - **Windows:** `reg query HKCU\Software\Microsoft\Windows\CurrentVersion\Run` shows `tinker_access_utility_applet`.
   - **macOS:** `~/Library/LaunchAgents/tinker_access_utility_applet.plist` exists and points at the binary.
   - **Linux:** `~/.config/autostart/tinker_access_utility_applet.desktop` exists.
4. Quit the applet. Log out and back in (or reboot). Confirm the applet starts automatically.
5. Re-launch (or wait for autostart), open the menu — *Run at startup* should reflect the enabled state.
6. Click *Run at startup* off. Verify the artifact above is gone.

## Known gaps to flag during testing

- The *Select port…* submenu is built once at applet startup. Plug a reader in after launch and it won't appear — you have to Quit and relaunch. Tracked as SPEC Open Question #5; planned fix is a *Refresh ports* menu item.
- Port selection is not persisted across applet restarts (SPEC Open Question #4). After autostart fires, the user must re-pick their port. Worth fixing before a real rollout.
- Tray icon is a solid blue square. macOS would prefer a monochrome template image; replace before any real release.
- Linux tray support depends on the desktop environment (X11 with `libayatana-appindicator` is what tray-icon expects). KDE works; GNOME needs the AppIndicator extension; Wayland-only sessions may not show the icon at all.
- **Linux + Wayland keystroke injection is broken** — confirmed on Hyprland: full pipeline works, enigo returns Ok, but characters never reach native Wayland windows. SPEC Open Question #6 has the diagnosis and the three remediation options. Test with an XWayland app (Firefox URL bar) to confirm the diagnosis if you suspect a different bug.

## Diagnostic logging

The applet emits `[applet]` and `[reader_loop]` markers on stderr at each stage of the scan→keystroke pipeline (port selection, reader-loop start/exit, tag parsed, tag received on UI thread, keystroke emission attempted, keystroke emission result). When triaging "scan doesn't work," launch with `2> /tmp/applet.stderr` and read the log to see which stage fails — adding more eprintlns at uncovered points has been the fastest path to localising.
