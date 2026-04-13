# Project Status (2026-04-12 23:10:53Z)

## Environment
- base_url: `https://newcastlehub.info`
- state_dir: `.wp-ai-ops-state-live`
- auth: use local `.env` / secret manager (do not paste passwords into chat)

## State Files
- audit_log: `.wp-ai-ops-state-live/audit_log.jsonl`
- executed_tasks: `.wp-ai-ops-state-live/executed_tasks.json` (count=393)
- write_limits: `.wp-ai-ops-state-live/write_limits.json`

## Recent Changes (from audit_log tail)
- 2026-03-29T22:10:25.887645+00:00 task=b744bf72-ddf0-4f70-916d-7b2a5a8eea5b updated target=https://newcastlehub.info:page:684 fields=content,modified_gmt
- 2026-03-29T22:10:26.518654+00:00 task=d31ed2c3-b1c2-4c4a-98d1-e6c0787c6699 skipped target=https://newcastlehub.info:page:403
- 2026-03-29T22:10:26.668836+00:00 task=defc69a8-d7fc-4037-82d7-f4d8e3182d49 skipped target=https://newcastlehub.info:page:684
- 2026-03-29T22:10:26.742211+00:00 task=f05c68e6-8b28-4eaf-94e6-fba5786d796a skipped target=https://newcastlehub.info:page:30
- 2026-03-29T22:10:26.812793+00:00 task=f51fccd8-dae9-474d-a416-d3eb976f46bb skipped target=https://newcastlehub.info:page:684
- 2026-04-05T23:10:14.742980+00:00 task=5deffef3-fc80-453e-b436-f3d949d2f9ce updated target=https://newcastlehub.info:page:403 fields=rank_math_description,rank_math_focus_keyword,rank_math_title
- 2026-04-05T23:10:16.657147+00:00 task=76dfcf36-2cb7-499f-8a61-0c956f15d4d2 skipped target=https://newcastlehub.info:page:403
- 2026-04-05T23:10:16.843335+00:00 task=7b5538b6-4d94-473e-b7ab-e04a266b0cf0 skipped target=https://newcastlehub.info:page:403
- 2026-04-05T23:10:17.049995+00:00 task=c9c7bc17-9401-4016-b74f-74c0ce566dd3 skipped target=https://newcastlehub.info:page:403
- 2026-04-12T23:10:29.061592+00:00 task=023fefd8-ffa9-412b-9f36-76bdb856c28d updated target=https://newcastlehub.info:page:30 fields=content,modified_gmt
- 2026-04-12T23:10:31.954866+00:00 task=2f7776fa-c0d5-4ef0-baa1-8906c9ba3ba8 skipped target=https://newcastlehub.info:page:30
- 2026-04-12T23:10:33.521848+00:00 task=3799d485-cd50-43ad-a6a2-12eda409a59c updated target=https://newcastlehub.info:page:713 fields=content,modified_gmt
- 2026-04-12T23:10:36.146196+00:00 task=4a08a9cb-af51-4bec-b435-1f06b77856ba skipped target=https://newcastlehub.info:page:30
- 2026-04-12T23:10:37.470957+00:00 task=579430b0-7508-45c2-87b2-5b416c6bfc43 skipped target=https://newcastlehub.info:page:713
- 2026-04-12T23:10:40.744867+00:00 task=73748d1b-200e-423f-8a6c-dc06bda5fe10 skipped target=https://newcastlehub.info:page:30
- 2026-04-12T23:10:42.113195+00:00 task=86a27e8d-4ddf-4c92-ad16-4719b58c00bc updated target=https://newcastlehub.info:page:403 fields=content,modified_gmt
- 2026-04-12T23:10:45.468234+00:00 task=9197aaa6-3f1e-41f9-a4ee-7f560bdf0fec skipped target=https://newcastlehub.info:page:403
- 2026-04-12T23:10:47.416917+00:00 task=93d19773-72cd-486a-b9d8-50f3721fb9a6 skipped target=https://newcastlehub.info:page:403
- 2026-04-12T23:10:49.473799+00:00 task=c2096b89-154b-4d51-867a-20df7f1acd54 skipped target=https://newcastlehub.info:page:713
- 2026-04-12T23:10:50.666412+00:00 task=eb260e61-03c9-41d9-962f-5fe2ba590535 skipped target=https://newcastlehub.info:page:713

## Next Actions (suggested)
1. Run plan-only before any write:
   - `PYTHONPATH=src python3 -m wp_ai_ops.cli run --task <task.json> --state-dir .wp-ai-ops-state-live --plan-only`
2. Execute after confirmation:
   - `PYTHONPATH=src python3 -m wp_ai_ops.cli run --task <task.json> --state-dir .wp-ai-ops-state-live --confirm`
3. Rollback if needed:
   - `PYTHONPATH=src python3 -m wp_ai_ops.cli rollback --original-task-id <task_id> --state-dir .wp-ai-ops-state-live --base-url https://newcastlehub.info`
4. One-click next run:
   - `cd /Users/michaelzhao/agents/apps/wordpress-ai-ops && ./scripts/run_auto_weekly_newcastle.sh`

