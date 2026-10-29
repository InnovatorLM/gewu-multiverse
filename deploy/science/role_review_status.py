#!/usr/local/bin/python3
"""Report progress to the local review dispatcher; never starts cloud jobs."""
import argparse,json,os,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('state',choices=['reviewing','waiting_author','waiting_platform','completed']);p.add_argument('--stage',required=True);p.add_argument('--reason',required=True);a=p.parse_args()
home=Path('/home/role');assignment=json.loads((home/'review-assignment.json').read_text())
record={'key':assignment['key'],'generation':assignment['generation'],'state':a.state,'stage':a.stage,'reason':a.reason,'updated_at':time.time()}
stage=home/'review-status.pending';stage.write_text(json.dumps(record,ensure_ascii=False));stage.chmod(0o600);stage.replace(home/'review-status.json');print(json.dumps(record,ensure_ascii=False))
