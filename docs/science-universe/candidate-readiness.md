# Candidate readiness audit

No current candidate is qualified for scientific acceptance. Infrastructure
readiness and a valid Harbor package do not substitute for an original,
scientifically meaningful task with independent verification and difficulty
evidence.

| Candidate | Verified current evidence | Decision / next requirement |
|---|---|---|
| robust-sensor-calibration | Three normal target-model trials succeeded. Independent numerical reproduction and rounded output pass the unchanged grader. A reviewer false-rejection claim was refuted. Remaining review claims are not fully adjudicated. | Infrastructure pilot only. No demonstrated target difficulty; redesign scientific work before more difficulty trials. |
| reactor-safety-control-pilot | Compared directly with Git objects at upstream commit1892516e4321ebffb307de3b638506582ef28916: all30upstream files identical,0modified,0missing;3extra workflow records. Instruction, reference controller and verifier are inherited. | Imported reference fixture, not a new universe task. Preserve attribution; do not count as original output or rename it to imply novelty. |
| science-image-publication-smoke | Real image build/publication, source registration and Beijing ACS runtime smoke passed. Diagnostic registrations are disabled. | Infrastructure fixture only; no scientific acceptance or difficulty claim. |

The reactor comparison used the import repository's actual original commit,
not the newer shallow comparison-corpus checkout, which lacks that historical
object. Git reads ran as the repository owner; no global safe-directory or
credential configuration was changed. File-by-file evidence stays in private
workspace state at `.state/harbor-eval/reactor-source-audit.json`.

The next scientific gate is a new author proposal, with independently sourced
scientific motivation, explicit data/model provenance and license, a precise
public contract, meaningful difference from both benchmark sources, and an
independent verification plan. Proposal review must precede implementation.
Do not manufacture low model success by tightening hidden tolerances or adding
ambiguous requirements. Difficulty trials must exclude infrastructure errors
and report designated-model token/tool counts as supporting evidence.

After a proposal is approved: freeze its implementation commit, perform source
and oracle-leak review, build matching digest-pinned images, validate Harbor
mechanics, run independent reference/negative checks and target-model trials,
complete factual/semantic/quality and applicable trajectory views, verify cleanup,
and prepare a concrete final review package. First-pilot user approval and
protected evaluator+owner approvals remain required before curator merge.
No real candidate has yet reached that approval stage.
