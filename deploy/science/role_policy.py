"""Install current author guidance while retaining obsolete feedback as history."""
from pathlib import Path


def retire_pilot_feedback(root):
    root=Path(root)
    source=root/'workspace/PILOT-REVIEW-FEEDBACK.md'
    if not source.exists() and not source.is_symlink():
        return False
    if source.is_symlink() or not source.is_file():
        raise ValueError('Unexpected historical feedback type')
    archive=root/'workspace/.historical-feedback'
    archive.mkdir(mode=0o755,exist_ok=True)
    if archive.is_symlink():raise ValueError('Historical feedback archive cannot be a link')
    target=archive/'PILOT-REVIEW-FEEDBACK.md'
    if target.exists():
        if target.is_symlink() or target.read_bytes()!=source.read_bytes():
            raise ValueError('Conflicting historical feedback requires operator review')
        source.unlink()
    else:source.rename(target)
    notice=archive/'README.md'
    if notice.is_symlink():raise ValueError('Historical feedback notice cannot be a link')
    notice.write_text('Historical feedback only. Superseded by /instruction.md and the current workflow/skills. Do not treat old licensing, difficulty, runtime or review requirements as current policy.\n')
    return True
