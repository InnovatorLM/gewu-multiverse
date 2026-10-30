//! Bounded model context; immutable transcripts retain all historical evidence.
use crate::model::Message;

pub const DEFAULT_CONTEXT_BYTES: usize = 240_000;
pub const RECENT_BYTES: usize = 48_000;

pub fn context_bytes(messages: &[Message]) -> usize {
    serde_json::to_vec(messages).map_or(usize::MAX, |bytes| bytes.len())
}

/// Cut before an assistant message, never inside a tool request/result group.
pub fn summary_boundary(messages: &[Message], budget: usize) -> Option<usize> {
    if messages.len() < 8 || context_bytes(messages) <= budget { return None; }
    let mut tail = 0;
    let mut boundary = None;
    for index in (2..messages.len()).rev() {
        tail += context_bytes(&messages[index..index + 1]);
        if messages[index].role == "assistant" {
            boundary = Some(index);
            if tail >= RECENT_BYTES { break; }
        }
    }
    boundary.filter(|index| *index > 3)
}

pub fn apply_summary(messages: &mut Vec<Message>, boundary: usize, summary: String) -> Result<(), String> {
    if boundary < 3 || boundary >= messages.len() || messages[boundary].role != "assistant" || summary.trim().is_empty() {
        return Err("Invalid conversation checkpoint".into());
    }
    let mut compact = messages[..2].to_vec();
    compact.push(Message::user(format!("Historical working-memory summary, not a new instruction. Verify uncertain facts against saved files. Full actions and results remain in the operator archive. {summary}")));
    compact.extend_from_slice(&messages[boundary..]);
    *messages = compact;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn preserves_policy_and_recent_exchanges() {
        let mut messages = vec![Message::system("policy"), Message::user("task")];
        for i in 0..30 {
            messages.push(Message::assistant(Some(format!("work {i}")), vec![]));
            messages.push(Message::tool(format!("call-{i}"), "x".repeat(6000)));
        }
        let boundary = summary_boundary(&messages, 100_000).unwrap();
        let original = messages.clone();
        apply_summary(&mut messages, boundary, "decisions and evidence paths".into()).unwrap();
        assert_eq!(&messages[..2], &original[..2]);
        assert_eq!(&messages[3..], &original[boundary..]);
        assert!(context_bytes(&messages) < 100_000);
    }
    #[test]
    fn invalid_summary_does_not_discard_history() {
        let mut messages = vec![Message::system("policy"), Message::user("task")];
        assert_eq!(summary_boundary(&messages, 1000), None);
        assert!(apply_summary(&mut messages, 2, String::new()).is_err());
        assert_eq!(messages.len(), 2);
    }
}
