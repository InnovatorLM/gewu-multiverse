"""Resolve original external FROM references without changing build semantics."""
import re
from pathlib import Path

PINNED = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:/-]*@sha256:[a-f0-9]{64}$')

def pin_bases(path, python_base, resolve):
    path=Path(path);source=path.read_text();stages=set();mapping=[];lines=[]
    for line in source.splitlines(keepends=True):
        if not re.match(r'^\s*FROM\s',line,re.I):
            lines.append(line);continue
        match=re.fullmatch(r'(\s*FROM\s+(?:--platform=\S+\s+)?)(\S+)(\s+AS\s+([A-Za-z0-9_.-]+))?(\s*)',line,re.I)
        if not match:raise ValueError('Unsupported FROM syntax; explicit reviewed base required')
        image=match[2];effective=image.replace('$'+'{PYTHON_BASE}',python_base).replace('$'+'PYTHON_BASE',python_base)
        replacement=image
        if effective!='scratch' and effective.lower() not in stages and not PINNED.fullmatch(effective):
            if '$' in effective:raise ValueError('Unresolved base build argument')
            replacement=resolve(effective)
            if not PINNED.fullmatch(replacement):raise ValueError('Base resolver did not return a digest')
            mapping.append({'source':effective,'resolved':replacement})
        lines.append(match[1]+replacement+(match[3] or '')+match[5])
        if match[4]:stages.add(match[4].lower())
    path.write_text(''.join(lines))
    return mapping
