# Handoff Template

Use this structure for cross-agent continuity (Codex/Claude):

1. What changed
- Files touched
- Behavioral impact

2. Current runtime state
- Last run timestamp
- Auth status
- Scheduler status

3. Blockers / risks
- Top failure reasons
- What was already attempted

4. Next one-click command
- `cd /Users/michaelzhao/agents/apps/wordpress-ai-ops && ./scripts/run_auto_weekly_newcastle.sh`

5. Rollback command
- `PYTHONPATH=src python3 -m wp_ai_ops.cli rollback --original-task-id <task_id> --state-dir .wp-ai-ops-state-live --base-url https://newcastlehub.info`
