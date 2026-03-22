# gstack

Use the `/browse` skill from gstack for all web browsing. Never use `mcp__claude-in-chrome__*` tools.

Available skills:
- `/office-hours` — structured async thinking / planning session
- `/plan-ceo-review` — review a plan from a CEO perspective
- `/plan-eng-review` — review a plan from an engineering perspective
- `/plan-design-review` — review a plan from a design perspective
- `/design-consultation` — get design feedback and direction
- `/review` — code review
- `/ship` — ship a feature end-to-end
- `/land-and-deploy` — land and deploy changes
- `/canary` — canary deploy
- `/benchmark` — run benchmarks
- `/browse` — browse the web (use this for ALL web browsing)
- `/qa` — full QA pass
- `/qa-only` — QA without implementation
- `/design-review` — design review checklist
- `/setup-browser-cookies` — set up browser cookies for authenticated browsing
- `/setup-deploy` — set up deployment configuration
- `/retro` — run a retrospective
- `/investigate` — investigate a bug or incident
- `/document-release` — document a release
- `/codex` — run with OpenAI Codex
- `/careful` — careful/high-stakes change mode
- `/freeze` — freeze a branch
- `/guard` — guard against regressions
- `/unfreeze` — unfreeze a branch
- `/gstack-upgrade` — upgrade gstack to the latest version

If gstack skills aren't working, run `cd .claude/skills/gstack && ./setup` to build the binary and register skills.
