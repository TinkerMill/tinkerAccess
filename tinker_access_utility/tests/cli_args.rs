use assert_cmd::Command;
use predicates::prelude::*;
use predicates::str::contains;

fn bin() -> Command {
    Command::cargo_bin("tinker_access_utility").unwrap()
}

#[test]
fn missing_required_args_fails_with_helpful_message() {
    bin()
        .assert()
        .failure()
        .stderr(contains("--port").or(contains("--list-ports")));
}

#[test]
fn port_and_list_ports_are_mutually_exclusive() {
    bin()
        .args(["--port", "/dev/null", "--list-ports"])
        .assert()
        .failure()
        .stderr(contains("cannot be used with"));
}

#[test]
fn list_ports_exits_zero_and_writes_to_stdout() {
    // Output content depends on the host. Just verify the flag is accepted,
    // exits 0, and produces some output (either ports or the empty marker).
    bin()
        .arg("--list-ports")
        .assert()
        .success()
        .stdout(predicates::function::function(|s: &str| !s.is_empty()));
}

#[test]
fn help_mentions_no_keystrokes() {
    bin()
        .arg("--help")
        .assert()
        .success()
        .stdout(contains("does NOT emit simulated keystrokes"));
}
