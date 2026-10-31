#!/usr/bin/env python3
import json, re, time, threading
from datetime import datetime
from urllib.parse import urlsplit, parse_qs
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

W=Path('/mnt/data/zhanglinfeng/workspace')
from deployment_paths import universe_root
UNIVERSE=universe_root(W)
ROOT=UNIVERSE/'.state/gewu-multiverse'
MODEL='deepseek-v4.1-flash-1017'
SECRET=re.compile(r'(?i)(api[_-]?key|token|password|authorization|secret)\s*[:=]\s*["\']?[^\s,"\'}]+')
BRIEF_DIR=W/'.state/universe-monitor-briefs'
BRIEF_DIR.mkdir(parents=True, exist_ok=True)
BRIEF_FILE=BRIEF_DIR/'latest.json'
SETTINGS=UNIVERSE/'.config/gewu-multiverse/multiverse.toml'
DISPATCH_STATE=UNIVERSE/'.state/gewu-multiverse/review-dispatcher'

def review_waits():
    try:
        rows=json.loads(tail_text(DISPATCH_STATE/'ledger.json',1024*1024))
        result={}
        for key,row in rows.items():
            role=row.get('role')
            if not role or row.get('updated_at',0)<result.get(role,{}).get('updated_at',0):continue
            result[role]=dict(key=key,state=row.get('state'),stage=safe(str(row.get('stage',''))),reason=safe(str(row.get('reason',''))),updated_at=row.get('updated_at',0))
        return result
    except (OSError,ValueError,TypeError):return {}

def controller_live():
    """Verify an actual deployment controller, rather than desired role settings."""
    universe=str(ROOT.parent.parent).encode()
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():continue
        try:
            argv=(entry/'cmdline').read_bytes().split(bytes([0]))
            if not argv or b'--run-agent' in argv:continue
            if b'gewu-multiverse' not in Path(argv[0].decode(errors='replace')).name.encode():continue
            if universe not in argv and (entry/'cwd').resolve()!=ROOT.parent.parent:continue
            if (entry/'stat').read_text().split()[2]!='Z':return True
        except (OSError,ValueError):continue
    return False

def role_status(desired, running, controller):
    if running:return '运行中'
    if desired!='started':return '已停用'
    return '等待调度' if controller else '控制器未运行'

def desired_roles():
    text=SETTINGS.read_text()
    roles={}
    for block in text.split('[[agents]]')[1:]:
        name=re.search(r'^name\s*=\s*"([^"]+)"',block,re.M)
        desired=re.search(r'^desired\s*=\s*"([^"]+)"',block,re.M)
        if name and desired: roles[name[1]]=desired[1]
    return roles

def live_run(run):
    try:
        pid=int((run/'session.pid').read_text().strip())
        cmd=(Path('/proc')/str(pid)/'cmdline').read_bytes().split(bytes([0]))
        state=(Path('/proc')/str(pid)/'stat').read_text().split()[2]
        return state!='Z' and b'--run-agent' in cmd and str(run).encode() in cmd
    except (OSError,ValueError): return False


def safe(s):
    return redact(s)[:1200]

def tail_text(path, budget=262144):
    """Bound snapshot I/O independently of multi-gigabyte trajectory history."""
    with Path(path).open('rb') as stream:
        stream.seek(0,2)
        size=stream.tell();start=max(0,size-budget);stream.seek(start)
        data=stream.read(budget)
    if start:
        data=data.partition(bytes([10]))[2]
    return data.decode(errors='replace')

def snapshot():
    out=[]
    desired=desired_roles()
    controller=controller_live()
    waits=review_waits()
    allowed={'curator'} | {f'author-{i:02}' for i in range(1,11)} | {f'evaluator-{i:02}' for i in range(1,4)}
    for role_dir in sorted((p for p in ROOT.iterdir() if p.is_dir() and p.name in allowed), key=lambda p:p.name):
        runs=sorted(role_dir.glob('run-*'),key=lambda p:p.stat().st_mtime,reverse=True)
        if not runs: continue
        run=runs[0]; log=run/'run.log'; tr=run/'transcript.jsonl'
        text=tail_text(log,8192)[-4000:] if log.exists() else ''
        events=[]
        if tr.exists():
            for line in tail_text(tr).splitlines()[-30:]:
                try:
                    e=json.loads(line); events.append({'event':e.get('event') or e.get('type'),'ts':e.get('ts'),'text':safe(str(e.get('text',''))), 'tool':safe(str(e.get('command','')) )})
                except Exception: pass
        status=role_status(desired.get(role_dir.name),live_run(run),controller)
        out.append({'status':status,'desired':desired.get(role_dir.name),'role':role_dir.name,'run':run.name,'updated':max((p.stat().st_mtime for p in run.iterdir() if p.is_file()),default=run.stat().st_mtime),'model':MODEL,'log':safe(text),'events':events[-12:],'review':waits.get(role_dir.name)})
    return {'now':time.time(),'controller_running':controller,'roles':out,'brief':read_brief()}

def read_brief():
    try: return json.loads(BRIEF_FILE.read_text(encoding='utf-8'))
    except Exception: return {'text':'简报正在生成…','generated_at':None,'periods':[]}

def write_brief():
    data=snapshot()
    roles=data['roles']; now=time.time()
    active=[]; stalled=[]; replies=tools=0
    for x in roles:
        events=x.get('events',[])
        def recent(event):
            try:return now-600 <= datetime.fromisoformat(event['ts'].replace('Z','+00:00')).timestamp() <= now
            except (ValueError,KeyError,TypeError):return False
        r=sum(e.get('event')=='model_reply' and recent(e) for e in events)
        t=sum(e.get('event') in ('tool_call','tool_result') and recent(e) for e in events)
        replies+=r; tools+=t
        age=now-x.get('updated',now)
        if x.get('status')=='运行中':
            (stalled if age>900 else active).append(x['role'])
    text=(f"当前启用 {sum(x.get('desired')=='started' for x in roles)} 个角色，运行中 {sum(x.get('status')=='运行中' for x in roles)} 个，最近摘要中包含 {replies} 次模型回复和 {tools} 次工具活动。"
          f"正在活跃推进的角色包括：{', '.join(active[:12]) or '暂无'}。")
    if stalled: text+=f" {', '.join(stalled[:8])} 最近活动较少，需继续观察。"
    brief={'text':text,'generated_at':now,'periods':[]}
    old=read_brief(); brief['periods']=(old.get('periods') or [])[-5:]
    brief['periods'].append({'text':text,'generated_at':now})
    with (BRIEF_DIR/'history.jsonl').open('a') as history:
        history.write(json.dumps({'text':text,'generated_at':now},ensure_ascii=False)+chr(10))
    BRIEF_FILE.write_text(json.dumps(brief,ensure_ascii=False,indent=2),encoding='utf-8')

def brief_loop():
    while True:
        try: write_brief()
        except Exception: pass
        time.sleep(600)


HTML='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Terminal-Bench Science Universe</title><style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#151d31;--panel2:#10182a;--line:#2b3956;--text:#edf3ff;--muted:#94a6c4;--accent:#73b7ff;--good:#5ee0a0;--warn:#ffd166}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 10% 0,#172849 0,#0b1020 38%);color:var(--text);font:14px/1.5 Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:1500px;margin:0 auto;padding:32px 24px 48px}header{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;margin-bottom:24px}h1{font-size:clamp(24px,3vw,38px);letter-spacing:-.03em;margin:0 0 5px}.subtitle{color:var(--muted);font-size:14px}.meta{color:var(--muted);text-align:right}.meta strong{color:var(--text);font-size:18px}.brief{background:linear-gradient(135deg,#172b4b,#13233d);border:1px solid #36577f;border-radius:14px;padding:18px 20px;margin:0 0 20px;box-shadow:0 10px 25px #05091444}.brief-title{color:#9ccaff;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin-bottom:7px}.brief-time{color:var(--muted);font-size:11px;margin-top:8px}.history-panel{background:rgba(15,24,43,.72);border:1px solid #263957;border-radius:14px;padding:18px 20px;margin-bottom:28px}.section-title{display:flex;align-items:center;justify-content:space-between;gap:12px;color:#dce9ff;font-weight:700;font-size:15px;margin-bottom:14px}.section-note{color:var(--muted);font-size:11px;font-weight:400}.roles-title{margin:4px 0 14px}.history{display:grid;gap:0}.history-item{display:flex;gap:14px;position:relative;min-height:62px}.history-item:not(:last-child):before{content:"";position:absolute;left:5px;top:14px;bottom:0;border-left:1px solid #395176}.history-dot{width:11px;height:11px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 4px #24466b;flex:none;margin-top:5px;z-index:1}.history-content{background:#111c31;border:1px solid #263957;border-radius:10px;padding:10px 13px;margin-bottom:10px;color:#c6d5eb;flex:1}.history-date{color:#8dbcf0;font-size:11px;margin-bottom:4px}.latest{background:#245b87;color:#dff1ff;border-radius:10px;padding:2px 7px;margin-left:5px;font-size:10px}.empty{color:var(--muted);font-size:13px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:16px}.card{background:linear-gradient(145deg,rgba(21,29,49,.98),rgba(16,24,42,.98));border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:0 12px 30px #05091455;min-width:0}.card:hover{border-color:#4d76a8}.head{display:flex;align-items:center;justify-content:space-between;gap:10px}.role{font-size:17px;font-weight:700}.model{color:var(--accent);font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.badge{display:inline-flex;align-items:center;gap:6px;color:var(--good);font-size:12px}.badge:before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor;box-shadow:0 0 10px currentColor}.run{color:#9ccaff;font:12px ui-monospace,SFMono-Regular,Menlo,monospace;margin:8px 0 14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.activity{font-size:12px;color:var(--muted);margin-bottom:12px}.activity b{color:var(--text)}details{border-top:1px solid var(--line);padding-top:10px;margin-top:10px}summary{cursor:pointer;color:#c8d7ef;font-weight:600;user-select:none}.event{border-top:1px solid #26334c;padding:8px 0;color:#aebed7;font:11px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;overflow-wrap:anywhere}.event:first-of-type{margin-top:8px}select,button{background:#172849;color:#edf3ff;border:1px solid #4d76a8;border-radius:7px;padding:9px;margin:4px}pre{white-space:pre-wrap;max-height:240px;overflow:auto;background:#0a1020;border:1px solid #202e49;padding:12px;border-radius:9px;color:#b8c8df;font:11px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace} .error{color:#ff8f8f}@media(max-width:650px){main{padding:22px 14px}header{display:block}.meta{text-align:left;margin-top:14px}.grid{grid-template-columns:1fr}}
</style><main><header><div><h1>Terminal-Bench Science Universe</h1><div class="subtitle">角色运行、模型调用与工具轨迹</div></div><div class="meta" id="meta">正在连接…</div></header><section class="brief"><div class="brief-title">十分钟世界简报</div><div id="brief">简报正在生成…</div><div class="brief-time" id="brief-time"></div></section><section class="history-panel"><div class="section-title"><span>简报时间线</span><span class="section-note">每 10 分钟更新 · 保留最近 6 期</span></div><div id="history" class="history"></div></section><div class="section-title roles-title"><span>角色运行明细</span><span class="section-note">每 1 分钟刷新</span></div><section class="grid" id="grid"></section></main><script>
const metaEl=document.getElementById('meta'), gridEl=document.getElementById('grid');
const esc=s=>String(s??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
async function tick(){try{let r=await fetch('/api/state',{cache:'no-store'});if(!r.ok)throw Error('API HTTP '+r.status);let d=await r.json();let now=d.now;metaEl.innerHTML=`<strong>${d.roles.length}</strong> 个角色<br><span>最后更新 ${new Date(now*1000).toLocaleTimeString()} · 每 1 分钟刷新</span>`;if(d.brief){document.getElementById('brief').textContent=d.brief.text;document.getElementById('brief-time').textContent=d.brief.generated_at?'生成于 '+new Date(d.brief.generated_at*1000).toLocaleString():'';document.getElementById('history').innerHTML=(d.brief.periods||[]).slice().reverse().map((b,i)=>`<article class="history-item"><div class="history-dot"></div><div class="history-content"><div class="history-date">${new Date(b.generated_at*1000).toLocaleString()} ${i===0?'<span class="latest">最新</span>':''}</div><div>${esc(b.text)}</div></div></article>`).join('')||'<div class="empty">暂时还没有历史简报。</div>'}gridEl.innerHTML=d.roles.map(x=>{let age=Math.max(0,Math.round(now-x.updated));let latest=x.events?.[x.events.length-1];return `<article class="card"><div class="head"><div class="role">${esc(x.role)}</div><span class="badge">${esc(x.status)}</span></div><div class="model">${esc(x.model)}</div><div class="run">${esc(x.run)}</div><div class="activity">最近活动：<b>${age<60?age+' 秒前':Math.round(age/60)+' 分钟前'}</b>${latest?' · '+esc(latest.event):''}</div>${x.review?`<div class="activity">评审状态：${esc(x.review.state)} · ${esc(x.review.stage)}<br>${esc(x.review.reason||"")}</div>`:""}<details open><summary>事件轨迹（${x.events.length}）</summary>${x.events.map(e=>`<div class="event">${esc(e.ts)} · ${esc(e.event)} · ${esc(e.tool||e.text)}</div>`).join('')}</details><details><summary>运行日志</summary><pre>${esc(x.log)}</pre></details></article>`}).join('')}catch(e){metaEl.innerHTML='<span class="error">监控 API 错误</span>';gridEl.innerHTML='<div class="card error">无法读取状态，请检查监控服务。</div>'}setTimeout(tick,60000)}tick();
</script>'''
ROLES_ROOT=UNIVERSE/'.config/gewu-multiverse/agents'
ROLE_RE=re.compile(r'(author-[0-9]{2,4}|evaluator-[0-9]{2,4}|curator)')

def redact(value):
    if isinstance(value,dict):
        return {k:('[REDACTED]' if re.search(r'(?i)(api.?key|token|password|authorization|credential)',k) else redact(v)) for k,v in value.items()}
    if isinstance(value,list): return [redact(v) for v in value]
    if isinstance(value,str):
        value=re.sub(r'(?i)Bearer +[a-z0-9._:/+-]+','Bearer [REDACTED]',value)
        value=re.sub(r'\bsk-[A-Za-z0-9_-]{12,}','[REDACTED]',value)
        for secret in KNOWN_SECRETS:
            value=value.replace(secret,'[REDACTED]')
        return SECRET.sub(lambda m:m.group(1)+'=[REDACTED]',value)
    return value

KNOWN_SECRETS=[]
# Exact replacements also protect credentials echoed in tool output. Never return config files.
for secret_path in (W/'.config/universe-roles').glob('*.json'):
    try:
        obj=json.loads(secret_path.read_text())
        KNOWN_SECRETS.extend(v for k,v in obj.items() if re.search('token|password|key',k,re.I) and isinstance(v,str) and len(v)>8)
    except (OSError,ValueError): pass
try:
    for line in (W/'.config/llm/dawnfm.env').read_text().splitlines():
        if 'API_KEY=' in line:
            KNOWN_SECRETS.append(line.split('=',1)[1].strip().strip(chr(34)+chr(39)))
except OSError: pass

def runs_for(role):
    if not ROLE_RE.fullmatch(role): raise ValueError('invalid role')
    rows=[]
    for kind,base,pattern,filename in [('native',ROOT/role,'run-*','transcript.jsonl'),('codex',ROLES_ROOT/role/'home/role/trajectories','*','events.jsonl')]:
        if not base.exists(): continue
        for run in base.glob(pattern):
            if run.is_symlink() or not run.is_dir(): continue
            path=run/filename
            if path.is_file() and not path.is_symlink():
                rows.append({'id':kind+':'+run.name,'updated':path.stat().st_mtime,'bytes':path.stat().st_size})
                if kind=='codex':
                    for extra,fn in [('stderr','stderr.log'),('final','final-message.txt')]:
                        if (run/fn).is_file(): rows.append({'id':extra+':'+run.name,'updated':(run/fn).stat().st_mtime,'bytes':(run/fn).stat().st_size})
                if kind=='native' and (run/'run.log').is_file():
                    rows.append({'id':'log:'+run.name,'updated':(run/'run.log').stat().st_mtime,'bytes':(run/'run.log').stat().st_size})
    return sorted(rows,key=lambda r:r['updated'],reverse=True)

def events_for(role,run_id,offset=0,limit=100):
    if not ROLE_RE.fullmatch(role): raise ValueError('invalid role')
    kind,name=run_id.split(':',1)
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',name): raise ValueError('invalid run')
    if kind=='native': base=ROOT/role; filename='transcript.jsonl'
    elif kind=='codex': base=ROLES_ROOT/role/'home/role/trajectories'; filename='events.jsonl'
    elif kind=='log': base=ROOT/role; filename='run.log'
    elif kind in ('stderr','final'): base=ROLES_ROOT/role/'home/role/trajectories'; filename='stderr.log' if kind=='stderr' else 'final-message.txt'
    else: raise ValueError('invalid harness')
    path=base/name/filename
    if path.is_symlink() or (base/name).is_symlink() or not path.resolve().is_relative_to(base.resolve()): raise ValueError('invalid path')
    events=[]; next_offset=offset
    with path.open('rb') as f:
        size=path.stat().st_size
        if offset<0 or offset>size: raise ValueError('invalid offset')
        f.seek(offset)
        for _ in range(min(max(limit,1),200)):
            line=f.readline()
            if not line: break
            if not line.endswith(bytes([10])) and kind not in ('final','log','stderr'): break
            next_offset=f.tell()
            try: events.append({'event':'log','text':redact(line.decode(errors='replace'))} if kind in ('log','stderr','final') else redact(json.loads(line)))
            except ValueError: events.append({'event':'raw_output','text':redact(line.decode(errors='replace'))})
    return {'events':events,'next_offset':next_offset,'bytes':size,'has_more':next_offset<size}

BROWSER='''<section class="history-panel"><div class="section-title">完整轨迹档案 · 每分钟自动同步</div><select id="tr-role"></select> <select id="tr-run"></select> <button id="tr-load">加载轨迹</button> <button id="tr-more">继续加载</button><div id="tr-status"></div><div id="tr-events"></div></section>'''
BROWSER_JS='''<script>
let trajectoryOffset=0;const roleSelect=document.getElementById('tr-role'),runSelect=document.getElementById('tr-run');
const addOptions=(el,items)=>{el.replaceChildren();for(const [value,label] of items){let o=document.createElement('option');o.value=value;o.textContent=label;el.append(o)}};
async function loadRuns(){let r=await fetch('/api/trajectories?role='+encodeURIComponent(roleSelect.value));let d=await r.json();addOptions(runSelect,d.runs.map(x=>[x.id,x.id+' · '+Math.round(x.bytes/1024)+' KB']));}
async function loadEvents(reset=false){try{if(!runSelect.value)return;if(reset){trajectoryOffset=0;document.getElementById('tr-events').replaceChildren();}let r=await fetch('/api/trajectory?'+new URLSearchParams({role:roleSelect.value,run:runSelect.value,offset:trajectoryOffset}));if(!r.ok)throw Error('HTTP '+r.status);let d=await r.json();for(let event of d.events){let details=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent=(event.ts||'')+' '+(event.event||event.type||'event');pre.textContent=JSON.stringify(event,null,2);details.append(summary,pre);document.getElementById('tr-events').append(details);}trajectoryOffset=d.next_offset;document.getElementById('tr-status').textContent='已读取 '+trajectoryOffset+' / '+d.bytes+' 字节（展示内容已脱敏）';}catch(e){document.getElementById('tr-status').textContent=String(e)}}
roleSelect.onchange=loadRuns;document.getElementById('tr-load').onclick=()=>loadEvents(true);document.getElementById('tr-more').onclick=()=>loadEvents();
fetch('/api/state').then(r=>r.json()).then(d=>{addOptions(roleSelect,d.roles.map(x=>[x.role,x.role]));return loadRuns()}).catch(e=>document.getElementById('tr-status').textContent=String(e));setInterval(()=>loadEvents(),60000);
</script>'''
HTML=HTML.replace('</main>',BROWSER+'</main>')+BROWSER_JS
HTML=HTML.replace('<span class="badge">有运行记录</span>','<span class="badge">有运行记录</span>')
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url=urlsplit(self.path);q=parse_qs(url.query)
        try:
            if url.path=='/api/state': data=snapshot()
            elif url.path=='/api/trajectories': data={'runs':runs_for(q.get('role',[''])[0])}
            elif url.path=='/api/trajectory': data=events_for(q.get('role',[''])[0],q.get('run',[''])[0],int(q.get('offset',['0'])[0]))
            elif url.path=='/':
                self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(HTML.encode());return
            else: self.send_error(404);return
            body=json.dumps(data,ensure_ascii=False).encode()
            self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
        except (ValueError,KeyError,FileNotFoundError): self.send_error(400)
    def log_message(self,*args): pass
if __name__=='__main__':
    threading.Thread(target=brief_loop,daemon=True).start()
    ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
