use std::io;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;
use std::time::Duration;

use crate::parse::TagId;
use crate::reader::TagReader;

// Drives a TagReader on the current thread, invoking `on_tag` for each parsed
// tag. Designed to live on a background thread; the applet's UI thread sets
// `stop` to terminate, and `paused` to suspend without tearing down the
// underlying serial connection.
//
// Exits when:
//   - `stop` is set
//   - reader returns Err(UnexpectedEof) (the FakeTagReader's exhaustion signal,
//     used in tests)
//   - reader returns any other Err — the error is reported via `on_error` and
//     the loop returns; the caller is expected to spawn a fresh thread to
//     retry if desired.
pub fn run<R, TF, EF>(
    mut reader: R,
    paused: Arc<AtomicBool>,
    stop: Arc<AtomicBool>,
    on_tag: TF,
    on_error: EF,
) where
    R: TagReader,
    TF: Fn(TagId),
    EF: Fn(String),
{
    eprintln!("[reader_loop] start");
    loop {
        if stop.load(Ordering::Relaxed) {
            eprintln!("[reader_loop] stop flag observed; exiting");
            return;
        }
        if paused.load(Ordering::Relaxed) {
            thread::sleep(Duration::from_millis(50));
            continue;
        }
        match reader.next_tag() {
            Ok(Some(tag)) => {
                eprintln!("[reader_loop] tag: {}", tag);
                on_tag(tag);
            }
            Ok(None) => continue,
            Err(e) if e.kind() == io::ErrorKind::UnexpectedEof => {
                eprintln!("[reader_loop] EOF; exiting");
                return;
            }
            Err(e) => {
                eprintln!("[reader_loop] error: {e}");
                on_error(e.to_string());
                return;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::reader::FakeTagReader;
    use std::sync::Mutex;

    fn flag(v: bool) -> Arc<AtomicBool> {
        Arc::new(AtomicBool::new(v))
    }

    #[test]
    fn yields_each_valid_tag_via_callback() {
        let reader = FakeTagReader::new([
            b"\x021234567890AB\x03".as_slice(),
            b"\x02WXYZ789012CD\x03".as_slice(),
        ]);
        let collected = Arc::new(Mutex::new(Vec::<String>::new()));
        let errors = Arc::new(Mutex::new(Vec::<String>::new()));

        run(
            reader,
            flag(false),
            flag(false),
            {
                let c = collected.clone();
                move |t| c.lock().unwrap().push(t.as_str().to_string())
            },
            {
                let e = errors.clone();
                move |s| e.lock().unwrap().push(s)
            },
        );

        assert_eq!(*collected.lock().unwrap(), vec!["1234567890AB", "WXYZ789012CD"]);
        assert!(errors.lock().unwrap().is_empty());
    }

    #[test]
    fn skips_noise_frames_yielding_only_valid_tags() {
        let reader = FakeTagReader::new([
            b"".as_slice(),
            b"\x021234567890AB\x03".as_slice(),
            b"short".as_slice(),
            b"\x02WXYZ789012CD\x03".as_slice(),
        ]);
        let collected = Arc::new(Mutex::new(Vec::<String>::new()));

        run(
            reader,
            flag(false),
            flag(false),
            {
                let c = collected.clone();
                move |t| c.lock().unwrap().push(t.as_str().to_string())
            },
            |_| {},
        );

        assert_eq!(*collected.lock().unwrap(), vec!["1234567890AB", "WXYZ789012CD"]);
    }

    #[test]
    fn stops_immediately_when_stop_flag_preset() {
        let reader = FakeTagReader::new([b"\x021234567890AB\x03".as_slice()]);
        let collected = Arc::new(Mutex::new(Vec::<String>::new()));

        run(
            reader,
            flag(false),
            flag(true), // pre-set
            {
                let c = collected.clone();
                move |t| c.lock().unwrap().push(t.as_str().to_string())
            },
            |_| {},
        );

        assert!(collected.lock().unwrap().is_empty());
    }
}
