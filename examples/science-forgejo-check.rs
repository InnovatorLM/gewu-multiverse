//! Read-only check using the same client and credentials as the controller.
use gewu_multiverse::{credentials, forgejo::ForgejoClient};
use std::{path::Path, time::Duration};
fn main() -> Result<(), String> {
    let path = Path::new(
        "/mnt/data/zhanglinfeng/workspace/universes/my-terminal-bench-science/.config/gewu-multiverse/credentials.toml",
    );
    let token = credentials::forgejo_admin_token(path)
        .map_err(|e| e.to_string())?
        .ok_or("no admin token")?;
    let client = ForgejoClient::new("http://127.0.0.1:3000", token, Duration::from_secs(10))
        .map_err(|e| e.to_string())?;
    let repositories = client
        .organisation_repositories("team")
        .map_err(|e| e.to_string())?;
    for repository in repositories {
        println!("{}", repository.full_name);
    }
    Ok(())
}
