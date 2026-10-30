//! Operator-invoked real SessionSpawner preparation, no model or agent spawn.
use gewu_multiverse::engine::session::{
    RealSpawner, SessionRepository, SessionRequest, SessionSpawner,
};
use gewu_multiverse::{confinement::Method, credentials};
use std::path::PathBuf;

fn main() -> Result<(), String> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 4 || std::env::var_os("GEWU_ROLE_BROKER_CONFIG").is_none() {
        return Err(
            "usage: science-role-session-check ROLE STATE_ROOT PRODUCT_BINARY (broker required)"
                .into(),
        );
    }
    let role = &args[1];
    let broker_path = std::env::var_os("GEWU_ROLE_BROKER_CONFIG")
        .ok_or("broker configuration missing")?;
    let broker: serde_json::Value = serde_json::from_str(
        &std::fs::read_to_string(broker_path).map_err(|e| e.to_string())?,
    ).map_err(|e| e.to_string())?;
    if broker["roles"].get(role).is_none() {
        return Err("unknown role".into());
    }
    let root = PathBuf::from(
        "/mnt/data/zhanglinfeng/workspace/universes/my-terminal-bench-science/.config/gewu-multiverse",
    );
    let state = PathBuf::from(&args[2]);
    let run_id = format!(
        "prepare-{}",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map_err(|e| e.to_string())?
            .as_nanos()
    );
    let credential = root.join("credentials.toml");
    let login = credentials::recorded_login(&credential, role)
        .map_err(|e| e.to_string())?
        .ok_or("role login missing")?;
    let request = SessionRequest {
        agent: role.clone(),
        run_id: run_id.clone(),
        run_dir: state.join(role).join(run_id),
        state_root: state,
        workspace: root.join("agents").join(role).join("workspace"),
        instruction: root.join("agents").join(role).join("instruction.md"),
        skills_dir: root.join("agents").join(role).join("skills"),
        endpoint: "https://dawnfm.gravarc.cn/v1/chat/completions".into(),
        model: "deepseek-v4.1-flash-1017".into(),
        max_turns: 0,
        timeout_secs: 300,
        credentials: credential,
        email: format!("{login}@example.invalid"),
        login,
        forgejo_url: "http://127.0.0.1:3000".into(),
        repositories: vec![
            SessionRepository {
                full_name: "team/terminal-bench-science".into(),
                directory: "terminal-bench-science".into(),
            },
            SessionRepository {
                // The operator sees this repository; production role tokens do not.
                full_name: "team/workspace".into(),
                directory: "workspace".into(),
            },
        ],
        confinement: Method::RoleBroker,
        hide: vec![],
    };
    let prepared = RealSpawner::new(&args[3]).prepare(&request)?;
    let context: serde_json::Value = serde_json::from_str(
        &std::fs::read_to_string(prepared.run_dir.join("forgejo.json"))
            .map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    assert_eq!(context["repositories"].as_array().map(Vec::len), Some(1));
    assert_eq!(
        context["repositories"][0]["full_name"],
        "team/terminal-bench-science"
    );
    println!(
        "role={role} preparation=passed workspace={} run={}",
        prepared.workspace.display(),
        prepared.run_dir.display()
    );
    Ok(())
}
