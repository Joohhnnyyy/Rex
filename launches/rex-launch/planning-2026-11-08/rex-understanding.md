# Rex — current implementation understanding

Reviewed runtime code/config before script v3. Older README/architecture describe retired scope; current code, infra config and D-039/D-040 take precedence.

| What defines Rex | Source evidence | Script implication |
|---|---|---|
| Personal conversational sidekick, warm/quick/witty | apps/agent/src/rex_agent/prompts.py system_prompt | Human request/outcome and mascot personality lead the story. |
| Voice interaction via Gnani STT/TTS and LiveKit | apps/agent/src/rex_agent/main.py; models.py | Show actual voice, not a typed-only product tour. |
| Default is English; multilingual mode is configurable | config.py AgentConfig/from_env; tests/test_config.py | English main take; no assumed Hinglish response or language-count promise. |
| Real web research plus native Mac app actions | research.py; desktop.py; infra/mcp_servers.yaml | Research-to-WhatsApp is the central proof. Accessibility actions do not require screen sharing. |
| Verified chat sends | desktop.py Desktop.send | Checks intended chat and newest message, not recipient delivery/read status. |
| Reusable multi-step routines | infra/pipelines.yaml; pipelines.py PipelineRunner | Built-in share_research researches/writes/sends and checks each step. Routine stops on failures or pending approvals. |
| Files stores notes/downloads | packages/mcp_servers/src/rex_mcp_servers/files.py | A distinct follow-up saves links; not an invented auto-save in share_research. |
| Memory survives calls | memory.py; main.py Rex.__init__/save_session_summary | Explicit stored facts plus call summaries; demonstrate a later call. |
| Discover proactively researches interests | apps/api/src/rex_api/discover.py background_loop; main.py production app; discoveries.py | Scheduled and on-demand, service/config dependent. Correction to earlier partial note: production has a timed background loop, not manual-only. |
| Inbox/calendar/Notion/Slack are connected tool surfaces | infra/mcp_servers.yaml; tools_bridge.py | Brief supporting reach shot; no unsupported universal-app claim. |
| User-initiated screen understanding/control | screen.py; main.py look_at_screen/control_screen | Say the screen you share, not always watching. |
| Gateway permissions, approvals, action timeline and some undo | infra/mcp_servers.yaml; gateway.py; main.py approve/deny/undo | Approval only for actions configured to require it; no blanket always-asks promise. |
| Background coder/meeting executors exist | brain/specialists.py; supervisor.py | Keep out of core marketing claims until end-to-end outputs are demonstrated. |
| Dashboard is the interaction/control surface | apps/web/lib/dashboard.ts; components/dash/ | Mascot expresses state. DEMO metrics are illustrative, not product usage evidence. |
| Calling removed | DECISION_LOG.md D-039/D-040; current registry | No Twilio, phone booking or call-agent claims. |

This was a read-only source review, not a live integration test. It did not read private memories, credentials, conversations or account contents.
