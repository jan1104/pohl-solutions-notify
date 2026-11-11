# Project instructions

## Current user handoff

On 11 November 2026 the user authorized publishing the checked 0.5.17 checkpoint
and then waiting. The recurring development automation is paused. After this
release, wait for new user instructions or device-test results before further
development. Preserve the documented open plan and all existing checkpoints.

Work in `D:\depot\pohl-solutions-notify` and read `docs/WORK_PLAN.md` first.
User preferences: communicate in plain German, make cohesive local commits,
use subagents for suitable isolated programming tasks to save the main agent context.
Routine well-scoped implementation or checks can use a smaller available model;
the coordinating agent reviews changes and runs the integrated checks. Do not have
agents edit the same files concurrently; subagents must not commit or change branches.

## Version preservation

- Continue development on `develop`; keep `main` at the saved 0.3.27 baseline.
- `v0.3.27` is the frozen current source snapshot; `v0.3.25` is the local source
  checkpoint associated with the version the user reported as having run in HA.
- Never move/delete these tags or reset the baseline branch as routine work.
- Read `git status` first and preserve unrelated/uncommitted work.
- Keep source snapshots, installation ZIPs and HA runtime-data backups distinct.
- No push, hosted release or deployment without explicit user instruction.
- Do not claim real HA/Android/browser tests when only local adapters were tested.
- On a new functional version, retain existing checkpoints and update tests/docs.
