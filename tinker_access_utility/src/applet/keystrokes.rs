use std::error::Error;
use std::fmt;

use enigo::{Direction, Enigo, Key, Keyboard, Settings};

use crate::parse::TagId;

pub trait Keystrokes {
    fn type_tag(&mut self, tag: &TagId) -> Result<(), KeystrokeError>;
}

#[derive(Debug)]
pub struct KeystrokeError(String);

impl fmt::Display for KeystrokeError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "keystroke error: {}", self.0)
    }
}

impl Error for KeystrokeError {}

impl KeystrokeError {
    fn new(msg: impl fmt::Display) -> Self {
        Self(msg.to_string())
    }
}

pub struct EnigoKeystrokes {
    enigo: Enigo,
}

impl EnigoKeystrokes {
    pub fn new() -> Result<Self, KeystrokeError> {
        let enigo = Enigo::new(&Settings::default()).map_err(KeystrokeError::new)?;
        Ok(Self { enigo })
    }
}

impl Keystrokes for EnigoKeystrokes {
    fn type_tag(&mut self, tag: &TagId) -> Result<(), KeystrokeError> {
        self.enigo
            .text(tag.as_str())
            .map_err(KeystrokeError::new)?;
        self.enigo
            .key(Key::Tab, Direction::Click)
            .map_err(KeystrokeError::new)?;
        Ok(())
    }
}

// Records what would have been typed. Used by Phase 6 wiring tests so the
// applet's scan→keystroke loop can be exercised without a desktop session.
#[derive(Debug, Default)]
pub struct FakeKeystrokes {
    pub typed: Vec<String>,
    pub keys: Vec<String>,
}

impl Keystrokes for FakeKeystrokes {
    fn type_tag(&mut self, tag: &TagId) -> Result<(), KeystrokeError> {
        self.typed.push(tag.as_str().to_string());
        self.keys.push("Tab".to_string());
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::parse::parse_frame;

    #[test]
    fn fake_keystrokes_records_tag_and_tab_in_order() {
        let mut fake = FakeKeystrokes::default();
        let tag = parse_frame(b"\x021234567890AB\x03").unwrap();
        fake.type_tag(&tag).unwrap();
        assert_eq!(fake.typed, vec!["1234567890AB"]);
        assert_eq!(fake.keys, vec!["Tab"]);
    }

    #[test]
    fn fake_keystrokes_accumulates_across_multiple_tags() {
        let mut fake = FakeKeystrokes::default();
        fake.type_tag(&parse_frame(b"\x021234567890AB\x03").unwrap())
            .unwrap();
        fake.type_tag(&parse_frame(b"\x02WXYZ789012CD\x03").unwrap())
            .unwrap();
        assert_eq!(fake.typed, vec!["1234567890AB", "WXYZ789012CD"]);
        assert_eq!(fake.keys, vec!["Tab", "Tab"]);
    }

    // EnigoKeystrokes hits real OS APIs and is verified manually per the
    // SPEC.md Phase 4 checklist on Windows and macOS.
}
