use tinker_access_utility::cli::run_loop;
use tinker_access_utility::reader::FakeTagReader;

#[test]
fn once_prints_first_tag_and_exits() {
    let reader = FakeTagReader::new([b"\x021234567890AB\x03\r\n".as_slice()]);
    let mut out = Vec::new();
    run_loop(reader, true, &mut out).unwrap();
    assert_eq!(String::from_utf8(out).unwrap(), "1234567890AB\n");
}

#[test]
fn once_skips_noise_until_a_valid_frame() {
    let reader = FakeTagReader::new([
        b"".as_slice(),
        b"\r\n".as_slice(),
        b"short".as_slice(),
        b"\x02WXYZ789012CD\x03".as_slice(),
    ]);
    let mut out = Vec::new();
    run_loop(reader, true, &mut out).unwrap();
    assert_eq!(String::from_utf8(out).unwrap(), "WXYZ789012CD\n");
}

#[test]
fn loop_prints_all_tags_until_exhausted() {
    let reader = FakeTagReader::new([
        b"\x021234567890AB\x03\r\n".as_slice(),
        b"\x02WXYZ789012CD\x03\r\n".as_slice(),
        b"\x02ABCDEF012345\x03\r\n".as_slice(),
    ]);
    let mut out = Vec::new();
    run_loop(reader, false, &mut out).unwrap();
    assert_eq!(
        String::from_utf8(out).unwrap(),
        "1234567890AB\nWXYZ789012CD\nABCDEF012345\n"
    );
}

#[test]
fn loop_exits_cleanly_on_empty_reader() {
    let reader = FakeTagReader::new(Vec::<&[u8]>::new());
    let mut out = Vec::new();
    run_loop(reader, false, &mut out).unwrap();
    assert!(out.is_empty());
}
