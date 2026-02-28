# Project Status (2026-02-22 22:10:14Z)

## Environment
- base_url: `https://newcastlehub.info`
- state_dir: `.wp-ai-ops-state-live`
- auth: use local `.env` / secret manager (do not paste passwords into chat)

## State Files
- audit_log: `.wp-ai-ops-state-live/audit_log.jsonl`
- executed_tasks: `.wp-ai-ops-state-live/executed_tasks.json` (count=0)
- write_limits: `.wp-ai-ops-state-live/write_limits.json`

## Recent Changes (from audit_log tail)
- 2026-02-18T06:28:39.192265+00:00 task=f3fcd922-4852-4421-ad46-cc59f8b8bdd9 skipped target=https://newcastlehub.info:page:403
- 2026-02-18T06:28:39.334416+00:00 task=f96db36d-2de0-4822-a72a-80f8a1ecd52f skipped target=https://newcastlehub.info:page:718
- 2026-02-18T06:28:39.404340+00:00 task=fac2f86f-dd43-401d-97ff-50b0da382769 skipped target=https://newcastlehub.info:page:39
- 2026-02-18T06:28:39.473193+00:00 task=ffde4947-03f7-4319-95e8-b4dcd2988acd skipped target=https://newcastlehub.info:page:718
- 2026-02-22T22:10:08.295138+00:00 task=042e19a7-1f54-46d0-94cc-913f7652705a skipped target=https://newcastlehub.info:page:39
- 2026-02-22T22:10:08.936885+00:00 task=0f00c574-3ea5-4034-a39b-f9a24627268f skipped target=https://newcastlehub.info:page:403
- 2026-02-22T22:10:10.219788+00:00 task=17a53398-8d3b-414b-9657-c18fd3370a67 skipped target=https://newcastlehub.info:page:39
- 2026-02-22T22:10:10.322736+00:00 task=18429911-98f2-4c15-804e-e6f49faf6e08 skipped target=https://newcastlehub.info:page:403
- 2026-02-22T22:10:10.471552+00:00 task=25339949-24fc-45b4-80e7-b1eb10c30945 skipped target=https://newcastlehub.info:page:718
- 2026-02-22T22:10:10.996545+00:00 task=356a67d6-3f86-4d7a-9430-dd56c028293b updated target=https://newcastlehub.info:page:28 fields=content,modified_gmt
- 2026-02-22T22:10:12.062684+00:00 task=52b730a3-da9c-4708-aee7-e3a6cfe6fac1 skipped target=https://newcastlehub.info:page:718
- 2026-02-22T22:10:12.135817+00:00 task=5a433358-9cdf-4166-a738-dbc65d00c484 skipped target=https://newcastlehub.info:page:718
- 2026-02-22T22:10:12.214605+00:00 task=78fa9a47-c646-44c3-90c3-7946b3aeaf8c skipped target=https://newcastlehub.info:page:403
- 2026-02-22T22:10:12.368512+00:00 task=841920a8-f5f8-42d2-bf6e-2a92de7fdf10 skipped target=https://newcastlehub.info:page:39
- 2026-02-22T22:10:12.430002+00:00 task=92753e17-50d1-4eb7-b0aa-2333b919906b skipped target=https://newcastlehub.info:page:39
- 2026-02-22T22:10:12.512492+00:00 task=a4942af6-2859-40f0-b2ab-480d63eb8859 skipped target=https://newcastlehub.info:page:403
- 2026-02-22T22:10:12.669481+00:00 task=af3ba11d-9a66-4c49-bb46-c0e3ed8ce780 skipped target=https://newcastlehub.info:page:28
- 2026-02-22T22:10:12.771117+00:00 task=bd058c7b-b7f9-4fd2-b168-8e22c0fa7d4b skipped target=https://newcastlehub.info:page:28
- 2026-02-22T22:10:12.874710+00:00 task=da35a50f-8c5d-41f4-96ef-7d657534e1d3 skipped target=https://newcastlehub.info:page:718
- 2026-02-22T22:10:12.950188+00:00 task=fe3acd76-7bf4-4467-a8cb-756e7d41ad35 skipped target=https://newcastlehub.info:page:28

## Next Actions (suggested)
1. Run plan-only before any write:
   - `PYTHONPATH=src python3 -m wp_ai_ops.cli run --task <task.json> --state-dir .wp-ai-ops-state-live --plan-only`
2. Execute after confirmation:
   - `PYTHONPATH=src python3 -m wp_ai_ops.cli run --task <task.json> --state-dir .wp-ai-ops-state-live --confirm`
3. Rollback if needed:
   - `PYTHONPATH=src python3 -m wp_ai_ops.cli rollback --original-task-id <task_id> --state-dir .wp-ai-ops-state-live --base-url https://newcastlehub.info`
4. One-click next run:
   - `cd /Users/michaelzhao/agents/apps/wordpress-ai-ops && ./scripts/run_auto_weekly_newcastle.sh`

