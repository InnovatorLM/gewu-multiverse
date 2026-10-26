import json
import sys
from pathlib import Path
from reference_fit import solve
cases=json.loads(Path(sys.argv[1]).read_text())
reports={key:solve(case)[0] for key,case in cases.items()}
Path(sys.argv[2]).write_text(json.dumps(reports,indent=2)+'\n')
