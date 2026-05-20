use std::io::{self, Write};
use std::process::ExitCode;
use std::time::Duration;

use clap::Parser;

use crate::reader::{SerialTagReader, TagReader, list_ports};

#[derive(Parser, Debug)]
#[command(
    name = "tinker_access_utility",
    about = "Read RFID tag IDs from a Sparkfun ID-12LA badge reader and print them to stdout.",
    long_about = "Read RFID tag IDs from a Sparkfun ID-12LA badge reader and print them to stdout. \
                  This is the CLI mode — it does NOT emit simulated keystrokes. \
                  Use the tray applet for keystroke emulation."
)]
pub struct Args {
    /// Serial port to read from (e.g. COM3 on Windows, /dev/ttyUSB0 on Linux).
    #[arg(
        long,
        conflicts_with = "list_ports",
        required_unless_present = "list_ports"
    )]
    pub port: Option<String>,

    /// List available serial ports and exit.
    #[arg(long)]
    pub list_ports: bool,

    /// Exit after the first successful tag read (useful for scripting).
    #[arg(long)]
    pub once: bool,
}

pub fn run_main() -> ExitCode {
    let args = Args::parse();
    match dispatch(args) {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            let _ = writeln!(io::stderr(), "error: {e}");
            ExitCode::FAILURE
        }
    }
}

fn dispatch(args: Args) -> io::Result<()> {
    let mut stdout = io::stdout().lock();
    if args.list_ports {
        return print_ports(&mut stdout);
    }
    let port_name = args.port.as_deref().expect("clap enforces required");
    let reader = SerialTagReader::open(port_name, Duration::from_millis(500))?;
    eprintln!("Reading from {port_name} (Ctrl+C to stop)");
    run_loop(reader, args.once, &mut stdout)
}

pub fn print_ports(out: &mut impl Write) -> io::Result<()> {
    let ports = list_ports()?;
    if ports.is_empty() {
        writeln!(out, "(no serial ports detected)")?;
        return Ok(());
    }
    for p in ports {
        writeln!(out, "{}\t{}", p.name, p.description)?;
    }
    Ok(())
}

pub fn run_loop<R: TagReader>(
    mut reader: R,
    once: bool,
    out: &mut impl Write,
) -> io::Result<()> {
    loop {
        match reader.next_tag() {
            Ok(Some(tag)) => {
                writeln!(out, "{tag}")?;
                out.flush()?;
                if once {
                    return Ok(());
                }
            }
            Ok(None) => continue,
            Err(e) if e.kind() == io::ErrorKind::UnexpectedEof => return Ok(()),
            Err(e) => return Err(e),
        }
    }
}
