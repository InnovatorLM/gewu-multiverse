# Restart isolation verification — 2026-10-30

Deployment target: my-terminal-bench-science. Selected roles: author-01 through author-04, evaluator-01/02, curator. Other configured roles remain stopped.

## Root causes and changes

The isolation probe previously enumerated retained physical role directories, including retired author/evaluator directories absent from the broker registry. Probe only configured roles, retaining missing configured paths so failures are not silently skipped. When a broker is explicitly configured but isolation is unavailable, refuse session scheduling.

A fixed one-second operator diagnostic delay also produced misleading connection failures before broker startup. Waiting for the actual socket verified all 14 configured roles: return code 0 and cleanup confirmed. Product diagnostic reported role-broker and session timeout 14400 seconds.

An orphaned Forgejo process serving this same instance had no PID record and conflicted with controller startup. Its command line and exact app.ini were checked before a graceful SIGTERM. The persistent controller is responsible for starting its replacement.

## Verification

- Configured workspace regression: passed.
- Engine regression suite: 47 passed, 0 failed.
- Production installed executable SHA256: f0db81713f6ec205a7f2b5536977792621f848e8440505d58bc0d3f79cc51ecc.
- Standalone broker/product diagnostic: all configured roles passed; role-broker; 14400 seconds.
- Monitor endpoint returned HTTP 200.

Runtime launch verification remains pending until fresh plans and growing transcripts prove real activity. Historical archives do not prove current role activity. Evaluators without eligible review assignments should remain idle.

## Live restart observation

The persistent supervisor launched successfully. After approximately three minutes of CPFS history recovery, the controller started one owned Forgejo child; Git health and monitor both returned HTTP 200. Fresh native sessions exist only for author-01 through author-04 and curator. All five actual plans specify role-broker, max_turns=0 and timeout_secs=14400. At the eight-minute observation, model replies were 27,14,15,20 for authors 01–04 and 20 for curator. Transcripts grew across observations. Both enabled evaluators remain intentionally idle without eligible assignments; no stopped role started a new session.

Two authors ran unbounded root filesystem searches; these consumed minutes of CPFS metadata access. The still-running matching search was terminated by verified UID/process identity. Runtime instructions and workspace notices now recommend scoped searches and reuse of installed scientific Python. A direct nonroot chroot probe for author-04 imported NumPy 2.4.6 and SciPy 1.17.1. Curator did not have the same preinstalled environment and is installing dependencies; this remains under observation. No complete task acceptance or five-rollout success is claimed.

## Follow-up monitoring and corrections

The monitor now derives desired roles from settings and verifies session.pid against the live process command line before showing Running. API verification returned five Running, two Waiting and seven Disabled roles; archive/status regression tests passed (3/3). The page remains bound to 127.0.0.1:8765 with a 60-second refresh.

Curator completed its own dependency install and successfully imported NumPy 2.5.4/SciPy 1.18.1. Its subsequent trajectory exposed a conflicting author instruction inherited by provisioning. Replaced the curator instruction with a dedicated coordination-only policy and corrected provisioning to use it. Refreshed only the curator session, retaining its previous transcript. The fresh session lists assigned issues and inspects branches/PR coordination rather than developing a new science task.

Final startup audit is stored at workspace .state/universe-restart/final-startup-audit.json. Author 01/02/03 reached 58/118/60 model replies and continued scientific prototype work. Author-04 remains on an independently created venv SciPy installation, despite a working preinstalled environment; this is an observed efficiency concern, not a completed task. Curator's refreshed session reached six model replies. All latest role plans use role-broker, unlimited turns and 14400-second timeouts. No disabled role started a new session. Git health remains 200 with one controller-owned server. Evaluators remain enabled and correctly waiting for an eligible assignment.

This verifies launch plus initial monitoring/problem diagnosis for the requested 4-author/2-evaluator/1-curator configuration. It does not claim every candidate task is finished, every model command succeeds, or the full five-rollout acceptance pipeline has passed on a new task.
