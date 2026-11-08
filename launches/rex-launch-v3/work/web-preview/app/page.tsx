"use client";

import "@livekit/components-styles";

import { LiveKitRoom } from "@livekit/components-react";
import { DataStreamError, DataStreamErrorReason } from "livekit-client";
import { useState } from "react";
import { config as rxConfig } from "rxjs";

import { Dashboard } from "@/components/dash/Dashboard";

// LiveKit's transcript/timeline hooks subscribe to text streams without an error handler, so ending a call
// while Rex is mid-sentence surfaces "Room disconnected in the middle of receiving data" as an unhandled
// error. That cut-off stream is expected; drop just that one and keep reporting everything else.
rxConfig.onUnhandledError = (err) => {
  if (err instanceof DataStreamError && err.reason === DataStreamErrorReason.AbnormalEnd) return;
  setTimeout(() => {
    throw err;
  });
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Conn = { url: string; token: string; room: string };

export default function Home() {
  const [identity, setIdentity] = useState("johny");
  const [conn, setConn] = useState<Conn | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function start() {
    if (busy || conn) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/v1/livekit/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identity: identity || "guest", client: "web" }),
      });
      if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
      setConn(await res.json());
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg === "Failed to fetch" ? `Can't reach the Rex API at ${API_URL}. Is it running?` : msg);
    } finally {
      setBusy(false);
    }
  }

  // The room wraps the whole dashboard even when idle, so every panel can read live state once a call starts.
  return (
    <LiveKitRoom
      serverUrl={conn?.url}
      token={conn?.token}
      connect={!!conn}
      audio={!!conn}
      video={false}
      onDisconnected={() => setConn(null)}
      onError={(e) => {
        // First error wins: tearing the room down makes LiveKit also report
        // "Client initiated disconnect", which would hide the real cause.
        const msg =
          e.name === "NotAllowedError"
            ? "Microphone access was blocked. Allow the mic for this site and try again."
            : `Couldn't connect to LiveKit: ${e.message}`;
        setError((prev) => prev ?? msg);
        setConn(null);
      }}
    >
      <Dashboard
        identity={identity}
        setIdentity={setIdentity}
        connected={!!conn}
        busy={busy}
        error={error}
        onStart={start}
        onEnd={() => setConn(null)}
      />
    </LiveKitRoom>
  );
}
