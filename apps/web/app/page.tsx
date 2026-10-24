"use client";

import "@livekit/components-styles";

import { LiveKitRoom } from "@livekit/components-react";
import { useState } from "react";

import { RexSession } from "@/components/RexSession";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Conn = { url: string; token: string; room: string };

export default function Home() {
  const [identity, setIdentity] = useState("johny");
  const [conn, setConn] = useState<Conn | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function start() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/v1/livekit/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identity, client: "web" }),
      });
      if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
      setConn(await res.json());
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(
        msg === "Failed to fetch" ? `Can't reach the Rex API at ${API_URL} — is it running?` : msg,
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center gap-8 px-4 py-10">
      <header className="flex w-full max-w-2xl items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">
          Rex <span className="text-[var(--accent)]">●</span>
        </h1>
        <span className="text-xs text-[var(--muted)]">Gnani Prisma + Timbre · LiveKit</span>
      </header>

      {!conn ? (
        <section className="flex w-full max-w-2xl flex-col items-center gap-4 rounded-2xl bg-[var(--surface)] p-10 shadow-sm">
          <div className="orb orb-idle" aria-hidden />
          <p className="text-center text-[var(--muted)]">
            Speak in English, Hinglish or your own language. Rex listens, acts, and asks before anything risky.
          </p>
          <label className="flex items-center gap-2 whitespace-nowrap text-sm">
            Your name
            <input
              value={identity}
              onChange={(e) => setIdentity(e.target.value.replace(/[^A-Za-z0-9_-]/g, ""))}
              className="rounded-lg border border-[var(--muted)]/30 bg-transparent px-3 py-1.5"
            />
          </label>
          <button
            onClick={start}
            disabled={busy || !identity}
            className="rounded-full bg-[var(--accent)] px-6 py-3 font-medium text-white disabled:opacity-50"
          >
            {busy ? "Connecting…" : "Talk to Rex"}
          </button>
          {error && <p className="text-sm text-[var(--danger)]">{error}</p>}
        </section>
      ) : (
        <LiveKitRoom
          serverUrl={conn.url}
          token={conn.token}
          connect
          audio
          video={false}
          onDisconnected={() => setConn(null)}
          onError={(e) => {
            setError(`Couldn't connect to LiveKit (${conn.url}): ${e.message}`);
            setConn(null);
          }}
          className="flex w-full justify-center"
        >
          <RexSession identity={identity} />
        </LiveKitRoom>
      )}
    </main>
  );
}
