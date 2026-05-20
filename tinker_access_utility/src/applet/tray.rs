use std::collections::HashMap;
use std::error::Error;

use tray_icon::{
    Icon, TrayIcon, TrayIconBuilder,
    menu::{CheckMenuItem, Menu, MenuId, MenuItem, PredefinedMenuItem, Submenu},
};

use crate::reader::list_ports;

pub struct TrayUi {
    pub _tray: TrayIcon,
    pub status: MenuItem,
    pub pause_resume: CheckMenuItem,
    pub pause_resume_id: MenuId,
    pub run_at_startup: CheckMenuItem,
    pub run_at_startup_id: MenuId,
    pub quit_id: MenuId,
    // Map menu-item id → port name, populated for each detected port.
    pub ports: HashMap<MenuId, String>,
}

pub fn build() -> Result<TrayUi, Box<dyn Error>> {
    let menu = Menu::new();

    let status = MenuItem::new("Status: Idle (no port selected)", false, None);

    let port_submenu = Submenu::new("Select port…", true);
    let mut ports = HashMap::new();
    match list_ports() {
        Ok(detected) if detected.is_empty() => {
            let none = MenuItem::new("(no ports detected)", false, None);
            port_submenu.append(&none)?;
        }
        Ok(detected) => {
            for p in detected {
                let label = format!("{} — {}", p.name, p.description);
                let item = MenuItem::new(&label, true, None);
                ports.insert(item.id().clone(), p.name);
                port_submenu.append(&item)?;
            }
        }
        Err(e) => {
            let err_item = MenuItem::new(format!("(error listing ports: {e})"), false, None);
            port_submenu.append(&err_item)?;
        }
    }

    let pause_resume = CheckMenuItem::new("Pause", true, false, None);
    let pause_resume_id = pause_resume.id().clone();

    let run_at_startup = CheckMenuItem::new("Run at startup", true, false, None);
    let run_at_startup_id = run_at_startup.id().clone();

    let quit = MenuItem::new("Quit", true, None);
    let quit_id = quit.id().clone();

    menu.append(&status)?;
    menu.append(&PredefinedMenuItem::separator())?;
    menu.append(&port_submenu)?;
    menu.append(&pause_resume)?;
    menu.append(&run_at_startup)?;
    menu.append(&PredefinedMenuItem::separator())?;
    menu.append(&quit)?;

    let tray = TrayIconBuilder::new()
        .with_menu(Box::new(menu))
        .with_tooltip("tinker_access_utility")
        .with_icon(tray_icon_image())
        .with_icon_as_template(cfg!(target_os = "macos"))
        .build()?;

    Ok(TrayUi {
        _tray: tray,
        status,
        pause_resume,
        pause_resume_id,
        run_at_startup,
        run_at_startup_id,
        quit_id,
        ports,
    })
}

pub fn set_status(item: &MenuItem, text: &str) {
    item.set_text(text);
}

fn tray_icon_image() -> Icon {
    // Source is 172×350; the template variant is a luminance-as-alpha
    // monochrome derived from it (see assets/README or regenerate via
    // `magick taicon.png ... PNG32:taicon-template.png`).
    #[cfg(target_os = "macos")]
    const ICON_PNG: &[u8] = include_bytes!("../../assets/taicon-template.png");
    #[cfg(not(target_os = "macos"))]
    const ICON_PNG: &[u8] = include_bytes!("../../assets/taicon.png");
    const TARGET: u32 = 32;

    let img = image::load_from_memory(ICON_PNG)
        .expect("embedded tray icon decodes")
        .to_rgba8();
    let (w, h) = img.dimensions();
    let side = w.max(h);

    // Pad to a square transparent canvas so the figure isn't squished on resize.
    let mut square = image::RgbaImage::from_pixel(side, side, image::Rgba([0, 0, 0, 0]));
    let dx = (side - w) / 2;
    let dy = (side - h) / 2;
    image::imageops::overlay(&mut square, &img, dx as i64, dy as i64);

    let resized = image::imageops::resize(
        &square,
        TARGET,
        TARGET,
        image::imageops::FilterType::Lanczos3,
    );

    Icon::from_rgba(resized.into_raw(), TARGET, TARGET).expect("valid RGBA tray icon")
}
