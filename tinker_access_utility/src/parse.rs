use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TagId(String);

impl TagId {
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl fmt::Display for TagId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

// Mirrors scripts/RFIDTagRegister.py:36-41 — strip ASCII whitespace, then take
// bytes [1..13] (skip leading STX, keep 10 tag chars + 2 checksum chars).
pub fn parse_frame(line: &[u8]) -> Option<TagId> {
    let stripped = trim_ascii_whitespace(line);
    if stripped.len() < 13 {
        return None;
    }
    let tag_bytes = &stripped[1..13];
    let tag = std::str::from_utf8(tag_bytes).ok()?.to_string();
    Some(TagId(tag))
}

fn trim_ascii_whitespace(s: &[u8]) -> &[u8] {
    let start = s.iter().position(|b| !b.is_ascii_whitespace()).unwrap_or(s.len());
    let end = s
        .iter()
        .rposition(|b| !b.is_ascii_whitespace())
        .map(|i| i + 1)
        .unwrap_or(0);
    if start >= end { &[] } else { &s[start..end] }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn valid_frame_with_stx_etx() {
        let line = b"\x021234567890AB\x03";
        let tag = parse_frame(line).expect("should parse");
        assert_eq!(tag.as_str(), "1234567890AB");
    }

    #[test]
    fn valid_frame_with_trailing_crlf() {
        // strip() removes the trailing \r\n; STX and ETX are not whitespace and survive.
        let line = b"\x021234567890AB\x03\r\n";
        let tag = parse_frame(line).expect("should parse");
        assert_eq!(tag.as_str(), "1234567890AB");
    }

    #[test]
    fn surrounding_whitespace_is_trimmed_before_slicing() {
        let line = b"\r\n\x021234567890AB\x03\r\n";
        let tag = parse_frame(line).expect("should parse");
        assert_eq!(tag.as_str(), "1234567890AB");
    }

    #[test]
    fn frame_without_stx_still_slices_per_python_semantics() {
        // Python's [1:13] takes bytes 1..13 regardless of what's at [0]; we preserve that.
        let line = b"1234567890ABCD";
        let tag = parse_frame(line).expect("should parse");
        assert_eq!(tag.as_str(), "234567890ABC");
    }

    #[test]
    fn exactly_13_bytes_is_minimum_valid() {
        let too_short = b"\x0112345678901"; // 12 bytes total
        assert!(parse_frame(too_short).is_none());
        let just_right = b"\x01123456789012"; // 13 bytes total
        let tag = parse_frame(just_right).expect("should parse");
        assert_eq!(tag.as_str(), "123456789012");
    }

    #[test]
    fn empty_line_returns_none() {
        assert!(parse_frame(b"").is_none());
    }

    #[test]
    fn whitespace_only_line_returns_none() {
        assert!(parse_frame(b"   \r\n\t").is_none());
    }

    #[test]
    fn non_utf8_payload_returns_none() {
        let line = b"\x02\xFF\xFE\xFD\xFC\xFB\xFA\xF9\xF8\xF7\xF6\xF5\xF4\x03";
        assert!(parse_frame(line).is_none());
    }

    #[test]
    fn display_renders_as_inner_string() {
        let tag = parse_frame(b"\x021234567890AB\x03").unwrap();
        assert_eq!(format!("{tag}"), "1234567890AB");
    }
}
