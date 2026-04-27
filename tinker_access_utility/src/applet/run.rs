use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;
use std::time::Duration;

use tao::event::{Event, StartCause};
use tao::event_loop::{ControlFlow, EventLoopBuilder};
use tray_icon::menu::MenuEvent;

use crate::applet::autostart::Autostart;
use crate::applet::keystrokes::{EnigoKeystrokes, Keystrokes};
use crate::applet::reader_loop;
use crate::applet::tray::{self, TrayUi};
use crate::parse::TagId;
use crate::reader::SerialTagReader;

#[derive(Debug)]
enum AppEvent {
    Menu(MenuEvent),
    Tag(TagId),
    ReaderError(String),
}

struct ReaderHandle {
    stop: Arc<AtomicBool>,
    join: Option<thread::JoinHandle<()>>,
}

impl ReaderHandle {
    fn shutdown(mut self) {
        self.stop.store(true, Ordering::Relaxed);
        if let Some(j) = self.join.take() {
            let _ = j.join();
        }
    }
}

pub fn run_main() -> ! {
    let event_loop = EventLoopBuilder::<AppEvent>::with_user_event().build();
    let proxy = event_loop.create_proxy();

    {
        let proxy = proxy.clone();
        thread::spawn(move || {
            let receiver = MenuEvent::receiver();
            while let Ok(event) = receiver.recv() {
                if proxy.send_event(AppEvent::Menu(event)).is_err() {
                    break;
                }
            }
        });
    }

    let mut tray_ui: Option<TrayUi> = None;
    let mut reader_handle: Option<ReaderHandle> = None;
    let paused = Arc::new(AtomicBool::new(false));
    let mut keystrokes: Option<EnigoKeystrokes> = None;
    let mut autostart: Option<Autostart> = None;

    event_loop.run(move |event, _, control_flow| {
        *control_flow = ControlFlow::Wait;

        match event {
            Event::NewEvents(StartCause::Init) => {
                match tray::build() {
                    Ok(ui) => tray_ui = Some(ui),
                    Err(e) => {
                        eprintln!("error: failed to build tray: {e}");
                        std::process::exit(1);
                    }
                }
                match EnigoKeystrokes::new() {
                    Ok(k) => keystrokes = Some(k),
                    Err(e) => {
                        eprintln!("warning: keystroke emitter unavailable: {e}");
                    }
                }
                match Autostart::new() {
                    Ok(a) => {
                        if let (Some(ui), Ok(enabled)) = (tray_ui.as_ref(), a.is_enabled()) {
                            ui.run_at_startup.set_checked(enabled);
                        }
                        autostart = Some(a);
                    }
                    Err(e) => {
                        eprintln!("warning: autostart unavailable: {e}");
                    }
                }
            }
            Event::UserEvent(AppEvent::Menu(menu_event)) => {
                let Some(ui) = tray_ui.as_ref() else { return };

                if menu_event.id == ui.quit_id {
                    if let Some(h) = reader_handle.take() {
                        h.shutdown();
                    }
                    std::process::exit(0);
                }

                if menu_event.id == ui.pause_resume_id {
                    let now_paused = ui.pause_resume.is_checked();
                    paused.store(now_paused, Ordering::Relaxed);
                    let label = if now_paused {
                        "Status: Paused"
                    } else {
                        "Status: Reading…"
                    };
                    tray::set_status(&ui.status, label);
                    return;
                }

                if menu_event.id == ui.run_at_startup_id {
                    let want = ui.run_at_startup.is_checked();
                    if let Some(a) = autostart.as_ref() {
                        if let Err(e) = a.set_enabled(want) {
                            eprintln!("autostart toggle failed: {e}");
                            // Revert the checkbox so the menu reflects reality.
                            ui.run_at_startup.set_checked(!want);
                        }
                    } else {
                        eprintln!("autostart unavailable; cannot toggle");
                        ui.run_at_startup.set_checked(!want);
                    }
                    return;
                }

                if let Some(port) = ui.ports.get(&menu_event.id).cloned() {
                    eprintln!("[applet] port selected: {port}");
                    if let Some(h) = reader_handle.take() {
                        h.shutdown();
                    }
                    let stop = Arc::new(AtomicBool::new(false));
                    let proxy_for_thread = proxy.clone();
                    let stop_for_thread = stop.clone();
                    let paused_for_thread = paused.clone();
                    let port_for_thread = port.clone();
                    let join = thread::spawn(move || {
                        match SerialTagReader::open(
                            &port_for_thread,
                            Duration::from_millis(500),
                        ) {
                            Ok(reader) => reader_loop::run(
                                reader,
                                paused_for_thread,
                                stop_for_thread,
                                |tag| {
                                    let _ = proxy_for_thread.send_event(AppEvent::Tag(tag));
                                },
                                |e| {
                                    let _ = proxy_for_thread
                                        .send_event(AppEvent::ReaderError(e));
                                },
                            ),
                            Err(e) => {
                                let _ = proxy_for_thread.send_event(AppEvent::ReaderError(
                                    format!("failed to open {}: {}", port_for_thread, e),
                                ));
                            }
                        }
                    });
                    reader_handle = Some(ReaderHandle {
                        stop,
                        join: Some(join),
                    });
                    tray::set_status(&ui.status, &format!("Status: Reading from {}", port));
                }
            }
            Event::UserEvent(AppEvent::Tag(tag)) => {
                eprintln!("[applet] tag received on UI thread: {tag}");
                if let Some(ui) = tray_ui.as_ref() {
                    if let Some(k) = keystrokes.as_mut() {
                        eprintln!("[applet] attempting keystroke emission");
                        match k.type_tag(&tag) {
                            Ok(()) => eprintln!("[applet] keystroke emission ok"),
                            Err(e) => eprintln!("[applet] keystroke error: {e}"),
                        }
                    } else {
                        eprintln!("[applet] keystrokes unavailable; skipping emission");
                    }
                    tray::set_status(&ui.status, &format!("Status: Last scan {}", tag));
                }
            }
            Event::UserEvent(AppEvent::ReaderError(msg)) => {
                if let Some(ui) = tray_ui.as_ref() {
                    tray::set_status(&ui.status, &format!("Status: Error — {}", msg));
                }
            }
            _ => {}
        }
    });
}
