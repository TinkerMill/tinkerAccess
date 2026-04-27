use std::io;
use std::time::Duration;

use serialport::{ClearBuffer, SerialPort, SerialPortType};

use crate::parse::{TagId, parse_frame};

pub trait TagReader {
    fn next_tag(&mut self) -> io::Result<Option<TagId>>;
}

#[derive(Debug, Clone)]
pub struct PortInfo {
    pub name: String,
    pub description: String,
}

pub fn list_ports() -> io::Result<Vec<PortInfo>> {
    let ports = serialport::available_ports().map_err(io::Error::other)?;
    Ok(ports.into_iter().map(port_info).collect())
}

fn port_info(p: serialport::SerialPortInfo) -> PortInfo {
    let description = match p.port_type {
        SerialPortType::UsbPort(usb) => {
            let mut parts = Vec::new();
            if let Some(m) = usb.manufacturer.as_deref().filter(|s| !s.is_empty()) {
                parts.push(m.to_string());
            }
            if let Some(prod) = usb.product.as_deref().filter(|s| !s.is_empty()) {
                parts.push(prod.to_string());
            }
            if parts.is_empty() {
                format!("USB {:04x}:{:04x}", usb.vid, usb.pid)
            } else {
                parts.join(" ")
            }
        }
        SerialPortType::BluetoothPort => "Bluetooth".into(),
        SerialPortType::PciPort => "PCI".into(),
        SerialPortType::Unknown => "Unknown".into(),
    };
    PortInfo { name: p.port_name, description }
}

pub struct SerialTagReader {
    port: Box<dyn SerialPort>,
}

impl SerialTagReader {
    pub fn open(port_name: &str, read_timeout: Duration) -> io::Result<Self> {
        let port = serialport::new(port_name, 9600)
            .timeout(read_timeout)
            .open()
            .map_err(io::Error::other)?;
        Ok(Self { port })
    }

    fn read_line(&mut self) -> io::Result<Vec<u8>> {
        let mut line = Vec::with_capacity(32);
        let mut byte = [0u8; 1];
        loop {
            match self.port.read_exact(&mut byte) {
                Ok(()) => {
                    line.push(byte[0]);
                    if byte[0] == b'\n' {
                        return Ok(line);
                    }
                }
                Err(e) if e.kind() == io::ErrorKind::TimedOut => return Ok(line),
                Err(e) => return Err(e),
            }
        }
    }
}

impl TagReader for SerialTagReader {
    // Mirrors the Python loop in scripts/RFIDTagRegister.py:35-36 — clear any
    // pending input (residual ETX from the previous frame would shift the
    // [1..13] slice by one byte), then read the next line.
    fn next_tag(&mut self) -> io::Result<Option<TagId>> {
        self.port.clear(ClearBuffer::Input).map_err(io::Error::other)?;
        let line = self.read_line()?;
        Ok(parse_frame(&line))
    }
}

pub struct FakeTagReader {
    frames: Vec<Vec<u8>>,
    cursor: usize,
}

impl FakeTagReader {
    pub fn new<I, F>(frames: I) -> Self
    where
        I: IntoIterator<Item = F>,
        F: Into<Vec<u8>>,
    {
        Self {
            frames: frames.into_iter().map(Into::into).collect(),
            cursor: 0,
        }
    }
}

impl TagReader for FakeTagReader {
    // Returns `UnexpectedEof` on exhaustion so the CLI loop can exit cleanly
    // in tests. Real serial readers never produce that error in normal
    // operation — they return `Ok(None)` on timeout.
    fn next_tag(&mut self) -> io::Result<Option<TagId>> {
        if self.cursor >= self.frames.len() {
            return Err(io::Error::new(
                io::ErrorKind::UnexpectedEof,
                "fake reader exhausted",
            ));
        }
        let frame = &self.frames[self.cursor];
        self.cursor += 1;
        Ok(parse_frame(frame))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fake_reader_yields_parsed_tags() {
        let mut reader = FakeTagReader::new([
            b"\x021234567890AB\x03\r\n".as_slice(),
            b"\x02WXYZ789012CD\x03\r\n".as_slice(),
        ]);
        assert_eq!(reader.next_tag().unwrap().unwrap().as_str(), "1234567890AB");
        assert_eq!(reader.next_tag().unwrap().unwrap().as_str(), "WXYZ789012CD");
    }

    #[test]
    fn fake_reader_skips_bad_frames_as_none() {
        let mut reader = FakeTagReader::new([
            b"".as_slice(),
            b"\x021234567890AB\x03".as_slice(),
        ]);
        assert!(reader.next_tag().unwrap().is_none());
        assert_eq!(reader.next_tag().unwrap().unwrap().as_str(), "1234567890AB");
    }

    #[test]
    fn fake_reader_errors_unexpected_eof_when_exhausted() {
        let mut reader = FakeTagReader::new([b"\x021234567890AB\x03".as_slice()]);
        assert!(reader.next_tag().unwrap().is_some());
        let err = reader.next_tag().expect_err("should error on exhaustion");
        assert_eq!(err.kind(), io::ErrorKind::UnexpectedEof);
    }

    #[test]
    fn fake_reader_accepts_owned_vecs() {
        let mut reader = FakeTagReader::new(vec![b"\x021234567890AB\x03".to_vec()]);
        assert_eq!(reader.next_tag().unwrap().unwrap().as_str(), "1234567890AB");
    }

    // SerialTagReader is exercised manually with hardware; no unit tests here.
    // list_ports() depends on the host environment and is also manual.
}
