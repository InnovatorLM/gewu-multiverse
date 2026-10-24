//! Black-box tests run the real supervisor with a deterministic Codex executable.
use gewu_multiverse::{run::RunPlan, transcript};
use std::os::unix::fs::PermissionsExt;
use std::{fs, path::PathBuf, process::Command};

fn fixture(tag: &str, script: &str) -> (PathBuf, PathBuf, PathBuf) {
    let root = std::env::temp_dir().join(format!(
        "codex-test-{}-{}-{}",
        std::process::id(),
        tag,
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    let workspace = root.join("workspace with spaces");
    let run = root.join("run-1");
    fs::create_dir_all(&workspace).unwrap();
    fs::create_dir_all(&run).unwrap();
    fs::create_dir_all(root.join("skills")).unwrap();
    fs::write(root.join("instruction.md"), "Perform the fixture task.\n").unwrap();
    let fake = root.join("fake codex");
    fs::write(&fake, format!("#!/bin/sh\nset -eu\n{script}\n")).unwrap();
    fs::set_permissions(&fake, fs::Permissions::from_mode(0o700)).unwrap();
    RunPlan {
        run_id: "run-1".into(),
        agent: "fixture".into(),
        workspace,
        instruction: root.join("instruction.md"),
        skills_dir: root.join("skills"),
        endpoint: String::new(),
        model: String::new(),
        credentials: root.join("missing-credentials.toml"),
        max_turns: 3,
        steps: vec![],
        timeout_secs: if tag == "git" { 30 } else { 2 },
        confinement: "none".into(),
        hide: vec![],
    }
    .write(&run)
    .unwrap();
    (root, run, fake)
}
fn launch(root: &PathBuf, run: &PathBuf, fake: &PathBuf) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_gewu-multiverse"))
        .arg("--run-agent")
        .arg(run)
        .env_remove("GEWU_CODEX_SANDBOX")
        .env_remove("GEWU_HARNESS")
        .env_remove("CODEX_HOME")
        .env_remove("GEWU_CODEX_HOME")
        .env("HOME", root)
        .env("GEWU_CODEX_BIN", fake)
        .output()
        .unwrap()
}
#[test]
fn default_codex_receives_instruction_identity_and_private_storage_without_native_key() {
    let (root, run, fake) = fixture(
        "success",
        r#"
[ "$1" = exec ]
case "$CODEX_HOME" in "$GEWU_WORKSPACE"/*) ;; *) exit 41 ;; esac
[ -d "$CODEX_HOME" ]
[ -n "$GIT_ASKPASS" ]
[ "$GIT_TERMINAL_PROMPT" = 0 ]
[ "$GEWU_AGENT" = fixture ]
grep -q 'Perform the fixture task' 
while [ "$#" -gt 0 ]; do
  if [ "$1" = -o ]; then shift; printf 'Fixture completed successfully.\n' > "$1"; fi
  shift
done
printf '{"type":"turn.completed"}\n'
"#,
    );
    let out = launch(&root, &run, &fake);
    assert!(
        out.status.success(),
        "{}",
        fs::read_to_string(run.join("run.log")).unwrap()
    );
    let records = transcript::read(&run).unwrap();
    assert!(records.records.iter().any(|r| matches!(r, transcript::Record::ToolResult {tool, exit_code:Some(0), ..} if tool == "codex")));
    assert!(
        matches!(records.records.last(), Some(transcript::Record::RunFinished {outcome, reason:Some(s),..}) if outcome == "succeeded" && s.contains("Fixture completed"))
    );
}
#[test]
fn nonzero_cli_exit_is_failure() {
    let (root, run, fake) = fixture("nonzero", "echo fixture-error >&2; exit 7");
    assert!(!launch(&root, &run, &fake).status.success());
    assert!(
        fs::read_to_string(run.join("run.log"))
            .unwrap()
            .contains("exit 7")
    );
}
#[test]
fn zero_exit_without_final_message_is_failure() {
    let (root, run, fake) = fixture("empty", "cat >/dev/null; exit 0");
    assert!(!launch(&root, &run, &fake).status.success());
    assert!(
        fs::read_to_string(run.join("run.log"))
            .unwrap()
            .contains("without a final message")
    );
}
#[test]
fn hung_codex_is_timed_out() {
    let (root, run, fake) = fixture("timeout", "cat >/dev/null; sleep 30");
    let start = std::time::Instant::now();
    assert!(!launch(&root, &run, &fake).status.success());
    assert!(start.elapsed().as_secs() < 10);
}
#[test]
fn missing_cli_is_failure() {
    let (root, run, _) = fixture("missing", "exit 0");
    assert!(
        !launch(&root, &run, &root.join("not-installed"))
            .status
            .success()
    );
}

#[test]
fn verbose_codex_output_does_not_break_the_pipe() {
    let (root, run, fake) = fixture(
        "verbose",
        r#"
cat >/dev/null
head -c 200000 /dev/zero | tr '\000' x
while [ "$#" -gt 0 ]; do
 if [ "$1" = -o ]; then shift; printf 'Verbose task completed.\n' > "$1"; fi
 shift
done
"#,
    );
    let out = launch(&root, &run, &fake);
    assert!(
        out.status.success(),
        "{}",
        fs::read_to_string(run.join("run.log")).unwrap()
    );
}

#[test]
fn codex_preserves_git_commit_identity_and_can_push_to_a_local_remote() {
    let (root, run, fake) = fixture(
        "git",
        r#"
cat >/dev/null
printf 'collaboration proof\n' > proof.txt
git add proof.txt
git commit -qm 'Codex fixture change'
git push -q origin HEAD:refs/heads/agent-fixture
while [ "$#" -gt 0 ]; do
 if [ "$1" = -o ]; then shift; printf 'Committed and pushed proof.\n' > "$1"; fi
 shift
done
"#,
    );
    let workspace = RunPlan::read(&run).unwrap().workspace;
    let remote = root.join("remote.git");
    fn git(args: &[&str]) {
        let out = Command::new("git").args(args).output().unwrap();
        assert!(
            out.status.success(),
            "{}",
            String::from_utf8_lossy(&out.stderr)
        );
    }
    git(&["init", "--bare", remote.to_str().unwrap()]);
    git(&["init", workspace.to_str().unwrap()]);
    git(&[
        "-C",
        workspace.to_str().unwrap(),
        "config",
        "user.name",
        "gewu-fixture",
    ]);
    git(&[
        "-C",
        workspace.to_str().unwrap(),
        "config",
        "user.email",
        "gewu-fixture@agents.invalid",
    ]);
    git(&[
        "-C",
        workspace.to_str().unwrap(),
        "remote",
        "add",
        "origin",
        remote.to_str().unwrap(),
    ]);
    assert!(launch(&root, &run, &fake).status.success());
    let author = Command::new("git")
        .args([
            "--git-dir",
            remote.to_str().unwrap(),
            "log",
            "-1",
            "--format=%an <%ae>",
            "agent-fixture",
        ])
        .output()
        .unwrap();
    assert!(author.status.success());
    assert_eq!(
        String::from_utf8_lossy(&author.stdout).trim(),
        "gewu-fixture <gewu-fixture@agents.invalid>"
    );
}

#[test]
fn provider_auth_is_private_redacted_and_removed_after_run() {
    let (root, run, fake) = fixture(
        "auth",
        r#"
cat >/dev/null
[ "$OPENAI_API_KEY" = "fixture-auth-secret-123456789" ]
[ "$(stat -c %a "$CODEX_HOME/auth.json")" = 600 ]
printf '%s\n' "$OPENAI_API_KEY"
while [ "$#" -gt 0 ]; do
 if [ "$1" = -o ]; then shift; printf 'Authentication fixture completed.\n' > "$1"; fi
 shift
done
"#,
    );
    fs::create_dir_all(root.join(".codex")).unwrap();
    gewu_multiverse::mode::write_private(
        root.join(".codex/auth.json"),
        br#"{"OPENAI_API_KEY":"fixture-auth-secret-123456789"}"#,
    )
    .unwrap();
    let out = Command::new(env!("CARGO_BIN_EXE_gewu-multiverse"))
        .arg("--run-agent")
        .arg(&run)
        .env_remove("GEWU_CODEX_SANDBOX")
        .env_remove("GEWU_HARNESS")
        .env_remove("CODEX_HOME")
        .env_remove("GEWU_CODEX_HOME")
        .env_remove("OPENAI_API_KEY")
        .env("HOME", &root)
        .env("GEWU_CODEX_BIN", &fake)
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "{}",
        fs::read_to_string(run.join("run.log")).unwrap()
    );
    let runtime = RunPlan::read(&run)
        .unwrap()
        .workspace
        .join(".gewu-codex-run-1");
    assert!(!runtime.join("auth.json").exists());
    assert!(!runtime.join("provider-env.sh").exists());
    for name in ["run.log", "transcript.jsonl"] {
        assert!(
            !fs::read_to_string(run.join(name))
                .unwrap()
                .contains("fixture-auth-secret-123456789")
        );
    }
}

#[test]
fn explicit_sandbox_override_is_passed_and_invalid_values_fail_closed() {
    let (root, run, fake) = fixture(
        "sandbox",
        r#"
case " $* " in *" --sandbox danger-full-access "*) ;; *) exit 45 ;; esac
cat >/dev/null
while [ "$#" -gt 0 ]; do
 if [ "$1" = -o ]; then shift; printf 'Completed.\n' > "$1"; fi
 shift
done
"#,
    );
    let output = Command::new(env!("CARGO_BIN_EXE_gewu-multiverse"))
        .args(["--run-agent", run.to_str().unwrap()])
        .env_remove("GEWU_HARNESS")
        .env("HOME", &root)
        .env("GEWU_CODEX_HOME", &root)
        .env("GEWU_CODEX_BIN", &fake)
        .env("GEWU_CODEX_SANDBOX", "danger-full-access")
        .output()
        .unwrap();
    assert!(output.status.success());
    let output = Command::new(env!("CARGO_BIN_EXE_gewu-multiverse"))
        .args(["--run-agent", run.to_str().unwrap()])
        .env_remove("GEWU_HARNESS")
        .env("HOME", &root)
        .env("GEWU_CODEX_HOME", &root)
        .env("GEWU_CODEX_BIN", &fake)
        .env("GEWU_CODEX_SANDBOX", "invalid")
        .output()
        .unwrap();
    assert!(!output.status.success());
}
