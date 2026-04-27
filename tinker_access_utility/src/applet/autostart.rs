use std::error::Error;
use std::fmt;

use auto_launch::{AutoLaunch, AutoLaunchBuilder, MacOSLaunchMode};

const APP_NAME: &str = "tinker_access_utility_applet";

#[derive(Debug)]
pub struct AutostartError(String);

impl fmt::Display for AutostartError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "autostart: {}", self.0)
    }
}

impl Error for AutostartError {}

impl AutostartError {
    fn from<E: fmt::Display>(e: E) -> Self {
        Self(e.to_string())
    }
}

pub struct Autostart {
    inner: AutoLaunch,
}

impl Autostart {
    pub fn new() -> Result<Self, AutostartError> {
        let exe = std::env::current_exe().map_err(AutostartError::from)?;
        let exe_str = exe
            .to_str()
            .ok_or_else(|| AutostartError("executable path is not valid UTF-8".into()))?;
        let inner = AutoLaunchBuilder::new()
            .set_app_name(APP_NAME)
            .set_app_path(exe_str)
            .set_macos_launch_mode(MacOSLaunchMode::LaunchAgent)
            .build()
            .map_err(AutostartError::from)?;
        Ok(Self { inner })
    }

    pub fn is_enabled(&self) -> Result<bool, AutostartError> {
        self.inner.is_enabled().map_err(AutostartError::from)
    }

    pub fn set_enabled(&self, enabled: bool) -> Result<(), AutostartError> {
        if enabled {
            self.inner.enable().map_err(AutostartError::from)
        } else {
            self.inner.disable().map_err(AutostartError::from)
        }
    }
}
