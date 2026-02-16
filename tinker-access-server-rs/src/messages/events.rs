use chrono::DateTime;

pub enum Context {
    ToHost,
    FromHost,
}

pub struct Header {
    context: Context,
    ulid: Option<Ulid>,
}

pub enum CmdMsgType {
    SetStateCmd,
}

#[derive(Serialize, Deserialize)]
#[serde(tag = "trigType")]
pub enum EventTrigger {
    IO {
        io_name: String,         // TODO: Change to Enum?
        previous_state: Boolean, // was
        current_state: Boolean,  // is
    },
    FreshScan {
        badge_id: String,
    },
    BootUp {},
    FatalError {},
}

pub enum BootState {
    Running,
    Unknown,
    FatalError,
    WaitingOnNTP,
    WaitingForConfig,
}

// TODO: Is this an OK encoding for ESP32's LED settings?
pub struct LedState {
    red: Byte,
    green: Byte,
    blue: Byte,
}

type IoName = String;
pub enum IoSettings {
    BinarySettings {
        state: Boolean,
        next_state: Option<Boolean>,
        duration: Option<Duration>,
    },
    LCDSettings {
        state: String,
        next_state: Option<String>,
        duration: Option<Duration>,
    },
    LEDSettings {
        state: LedState,
        next_state: Option<LedState>,
        duration: Option<Duration>,
    },
}

pub struct Config {
    role: Option<String>,
    location: Option<String>,
    token: String,
    init_state: IoSettings,
}

type DeviceFeatures = String;
pub struct DeviceInfoPlatform {
    device: String,
    chip_rev: String,
    mac_addr: String,
    features: Set<DeviceFeatures>,
}

pub struct DeviceInfoApplication {
    name: String,
    version: String,
    esp_idf: String, // TODO: Maybe bury this so we aren't locked to ESP in the API?
    compile_datetime: DateTime<Utc>,
    elf_sha: String,
}

pub struct DeviceInfo {
    platform: DeviceInfoPlatform,
    application: DeviceInfoApplication,
}

#[derive(Serialize, Deserialize)]
#[serde(tag = "msgType")]
pub enum Message {
    CmdResponse {
        header: Header,
        cmd_msg_type: CmdMsgType,
        origin_message_ulid: Ulid,
        succeeded: Boolean,
        error_message: Option<String>,
    },
    GetStateCmd {
        header: Header,
    },
    EventReport {
        header: Header,
        event_trigger: EventTrigger,
        boot_state: BootState,
    },
    SetStateCmd {
        header: Header,
        settings: Map<IoName, IoSettings>,
    },
    GetConfigCmd {
        header: Header,
        config: Config,
    },
    SetConfigCmd {
        header: Header,
        config: Config,
    },
    ConfigReport {
        header: Header,
        config: Config,
        device_info: DeviceInfo,
    },
}
