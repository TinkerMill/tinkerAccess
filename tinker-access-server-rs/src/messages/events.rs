use chrono::{DateTime, Utc};
use serde::Deserialize;
use ulid::Ulid;

#[derive(Serialize, Deserialize)]
pub enum Context {
    ToHost,
    FromHost,
}

#[derive(Serialize, Deserialize)]
pub enum BootState {
    Running,
    Unknown,
    FatalError,
    WaitingOnNTP,
    WaitingForConfig,
}

#[derive(Serialize, Deserialize)]
pub struct LedState {
    red: Byte,
    green: Byte,
    blue: Byte,
    remaining: Option<u8>,
}

#[derive(Serialize, Deserialize)]
pub struct OutputState {
    state: bool,
    remaining: Option<u8>,
}

#[derive(Serialize, Deserialize)]
pub struct DisplayState {
    state: String,
    #[serde(flatten)]
    next_state: Option<DisplayTransition>,
}
#[derive(Serialize, Deserialize)]
pub struct DisplayTransition {
    state: String,
    remaining: u8,
}

#[derive(Serialize, Deserialize)]
pub enum IoState {
    LedState(LedState),
    OutputState(OutputState),
    DisplayState(DisplayState),
}

#[derive(Serialize, Deserialize)]
pub struct BinaryEventTrigger {
    trig_type: TriggerType,
    io_name: String,
    was: Option<bool>,
    is: bool,
}

#[derive(Serialize, Deserialize)]
pub struct DisplayEventTrigger {
    trig_type: TriggerType,
    io_name: String,
    was: Option<String>,
    is: String,
}

#[derive(Serialize, Deserialize)]
pub struct LedEventTrigger {
    trig_type: TriggerType,
    io_name: String,
    was: Option<LedState>,
    is: LedState,
}

#[derive(Serialize, Deserialize)]
pub struct CardEventTrigger {
    trig_type: TriggerType,
    io_name: String,
    is: String,
}

#[derive(Serialize, Deserialize)]
pub struct Header {
    api_version: String,
    context: Context,
    ulid: Ulid,
}

#[derive(Serialize, Deserialize)]
pub struct DeviceConfig {
    role: String,
    location: String,
    token: String,
    init_state: HashMap<String, IoState>,
}

#[derive(Serialize, Deserialize)]
pub struct IoOptions {
    count: Option<u8>,
    exists: bool,
}

#[derive(Serialize, Deserialize)]
pub struct PlatformInfo {
    device: String,
    chip_rev: String,
    mac_addr: String, // TODO: Change to a type for mac addresses
    features: HashMap<String, IoOptions>,
}

#[derive(Serialize, Deserialize)]
pub struct ApplicationInfo {
    name: String,
    version: String,
    framework_version: String,
    compile_time: DateTime<Utc>,
    elf_sha: String,
}

#[derive(Serialize, Deserialize)]
pub struct DeviceInfo {
    platform: PlatformInfo,
    application_info: ApplicationInfo,
}

#[derive(Serialize, Deserialize)]
#[serde(tag = "msgType")]
pub enum Events {
    EventReportBinary {
        #[serde(flatten)]
        header: Header,
        event_trigger: BinaryEventTrigger,
    },
    EventReportDisp {
        #[serde(flatten)]
        header: Header,
        event_trigger: DisplayEventTrigger,
    },
    EventReportLed {
        #[serde(flatten)]
        header: Header,
        event_trigger: LedEventTrigger,
    },
    EventReportCard {
        #[serde(flatten)]
        header: Header,
        event_trigger: CardEventTrigger,
    },
    EventReportPostBoot {
        #[serde(flatten)]
        header: Header,
        event_trigger: HashMap<String, IoState>,
    },
    SetStateCmd {
        #[serde(flatten)]
        header: Header,
        settings: HashMap<String, IoState>,
    },
    BadCmd {
        #[serde(flatten)]
        header: Header,
        cmd_msg_type: String,
        cmd_ulid: Ulid,
        succeeded: bool,
        error_message: String,
    },
    GetStateCmd {
        #[serde(flatten)]
        header: Header,
    },
    StateReport {
        #[serde(flatten)]
        header: Header,
        boot_state: BootState,
        current_io_state: HashMap<String, IoState>,
    },
    SetConfigCmd {
        #[serde(flatten)]
        header: Header,
        config: DeviceConfig,
    },
    SetDefaultConfigCmd {
        #[serde(flatten)]
        header: Header,
        config: DeviceConfig,
    },
    GetConfigCmd {
        #[serde(flatten)]
        header: Header,
    },
    ConfigReport {
        #[serde(flatten)]
        header: Header,
        config: DeviceConfig,
        device_info: Option<DeviceInfo>,
    },
}
