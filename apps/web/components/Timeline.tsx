"use client";

import { useRoomContext, useTextStream, useVoiceAssistant } from "@livekit/components-react";
import { useMemo, useState } from "react";

type ActionEvent = {
  type: "action_event";
  id: string;
  ts: string;
  tool: string;
  tier: "R" | "W" | "A";
  status: "started" | "succeeded" | "failed" | "awaiting_approval" | "denied" | "undone";
  summary: string;
  trace_id?: string | null; // action_id for approvals
  result_redacted?: { text?: string; error?: string } | null;
};

const TIER_LABEL = { R: "Read", W: "Change", A: "Needs OK" } as const;
const STATUS_STYLE: Record<ActionEvent["status"], string> = {
  started: "text-[var(--muted)]",
  succeeded: "text-[var(--ok)]",
  failed: "text-[var(--danger)]",
  awaiting_approval: "text-[var(--warn)]",
  denied: "text-[var(--muted)]",
  undone: "text-[var(--muted)]",
};

export function Timeline() {
  const { textStreams } = useTextStream("rex.timeline");
  const room = useRoomContext();
  const { agent } = useVoiceAssistant();
  const [deciding, setDeciding] = useState<string | null>(null);

  const events = useMemo(() => {
    const parsed: ActionEvent[] = [];
    for (const s of textStreams) {
      try {
        const e = JSON.parse(s.text) as ActionEvent;
        if (e.type === "action_event") parsed.push(e);
      } catch {
        /* partial or non-JSON stream */
      }
    }
    return parsed.reverse();
  }, [textStreams]);

  // An approval is open until a later event for the same action_id (succeeded / denied / failed) arrives.
  const closed = new Set(
    events.filter((e) => e.status !== "awaiting_approval" && e.trace_id).map((e) => e.trace_id as string),
  );

  async function decide(actionId: string, decision: "approve" | "deny") {
    if (!agent) return;
    setDeciding(actionId);
    try {
      await room.localParticipant.performRpc({
        destinationIdentity: agent.identity,
        method: "rex.decide",
        payload: JSON.stringify({ action_id: actionId, decision }),
      });
    } finally {
      setDeciding(null);
    }
  }

  return (
    <section className="rounded-2xl bg-[var(--surface)] p-4 shadow-sm">
      <h2 className="mb-3 text-sm font-semibold text-[var(--muted)]">Actions</h2>
      {events.length === 0 ? (
        <p className="text-sm text-[var(--muted)]">Nothing yet. Try “How long from Koramangala to Indiranagar?”</p>
      ) : (
        <ol className="flex max-h-[35vh] flex-col gap-2 overflow-y-auto">
          {events.map((e) => {
            const open = e.status === "awaiting_approval" && e.trace_id && !closed.has(e.trace_id);
            return (
              <li key={e.id} className="rounded-xl border border-[var(--muted)]/20 px-3 py-2">
                <div className="flex items-center justify-between gap-2 text-xs">
                  <span className="font-mono">{e.tool}</span>
                  <span className="flex items-center gap-2">
                    <span className="rounded-full border border-[var(--muted)]/30 px-2 py-0.5">{TIER_LABEL[e.tier]}</span>
                    <span className={STATUS_STYLE[e.status]}>{e.status.replace("_", " ")}</span>
                    <time className="text-[var(--muted)]">
                      {new Date(e.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                    </time>
                  </span>
                </div>
                <p className="mt-1 text-sm">{e.summary}</p>
                {e.result_redacted?.error && (
                  <p className="mt-1 text-xs text-[var(--danger)]">{e.result_redacted.error}</p>
                )}
                {open && (
                  <div className="mt-2 flex gap-2">
                    <button
                      onClick={() => decide(e.trace_id as string, "approve")}
                      disabled={deciding === e.trace_id}
                      className="rounded-full bg-[var(--ok)] px-4 py-1.5 text-sm text-white disabled:opacity-50"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => decide(e.trace_id as string, "deny")}
                      disabled={deciding === e.trace_id}
                      className="rounded-full border border-[var(--danger)] px-4 py-1.5 text-sm text-[var(--danger)]"
                    >
                      Deny
                    </button>
                  </div>
                )}
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
