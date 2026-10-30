//! Bounded model context; immutable transcripts retain all historical evidence.
use crate::model::Message;

pub const DEFAULT_CONTEXT_BYTES: usize = 240_000;
pub const RECENT_BYTES: usize = 48_000;

/// Exact JSON-value replay: replace the changed system note and append only new
/// messages. Non-prefix histories (including summaries) get a full checkpoint.
pub fn request_record(previous: &mut Option<serde_json::Value>, body: &str) -> String {
    let Ok(current) = serde_json::from_str::<serde_json::Value>(body) else { return body.to_owned(); };
    let mut recorded = current.clone();
    if let Some(old) = previous.as_ref() {
        if let (Some(before), Some(after)) = (old["messages"].as_array(), current["messages"].as_array()) {
            let mut old_options=old.clone(); old_options.as_object_mut().map(|v| v.remove("messages"));
            let mut new_options=current.clone(); new_options.as_object_mut().map(|v| v.remove("messages"));
            if !before.is_empty() && after.len() >= before.len() && before[1..] == after[1..before.len()] && old_options == new_options {
                recorded=serde_json::json!({"format":"gewu.request-delta.v1","base":"previous_model_request","base_message_count":before.len(),"system":after[0],"append":after[before.len()..],"options":new_options});
            }
        }
    }
    *previous=Some(current);
    serde_json::to_string(&recorded).unwrap_or_else(|_| body.to_owned())
}

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
    fn request_delta_preserves_new_messages_and_resets_on_summary() {
        let mut previous=None;
        let first=serde_json::json!({"model":"test","messages":[{"role":"system","content":"old"},{"role":"user","content":"task"}]});
        assert_eq!(serde_json::from_str::<serde_json::Value>(&request_record(&mut previous,&first.to_string())).unwrap(),first);
        let second=serde_json::json!({"model":"test","messages":[{"role":"system","content":"new"},{"role":"user","content":"task"},{"role":"assistant","content":"done"}]});
        let delta:serde_json::Value=serde_json::from_str(&request_record(&mut previous,&second.to_string())).unwrap();
        assert_eq!(delta["format"],"gewu.request-delta.v1");
        assert_eq!(delta["append"].as_array().unwrap().len(),1);
        assert_eq!(delta["system"],second["messages"][0]);
        assert_eq!(delta["base_message_count"],2);
        let summary=serde_json::json!({"model":"test","messages":[{"role":"system","content":"new"},{"role":"user","content":"summary"}]});
        assert_eq!(serde_json::from_str::<serde_json::Value>(&request_record(&mut previous,&summary.to_string())).unwrap(),summary);
    }
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
