"use client";

import {
  DisconnectButton,
  RoomAudioRenderer,
  StartAudio,
  TrackToggle,
  VoiceAssistantControlBar,
  useTrackVolume,
  useTranscriptions,
  useVoiceAssistant,
} from "@livekit/components-react";
import { Track } from "livekit-client";
import { useEffect, useRef } from "react";

import { BrowserView } from "@/components/BrowserView";
import { Connections } from "@/components/Connections";
import { RexOrb } from "@/components/RexOrb";
import { Timeline } from "@/components/Timeline";
import { LANG_NAME, langChip } from "@/lib/lang";

const STATE_LABEL: Record<string, string> = {
  disconnected: "Disconnected",
  connecting: "Connecting…",
  initializing: "Waking up Rex…",
  listening: "Listening",
  thinking: "Thinking",
  speaking: "Speaking",
};

export function RexSession({ identity }: { identity: string }) {
  const { state, audioTrack, agent } = useVoiceAssistant();
  const level = useTrackVolume(audioTrack);
  const transcriptions = useTranscriptions();
  const endRef = useRef<HTMLDivElement>(null);
  const lastMine = [...transcriptions].reverse().find((t) => t.participantInfo.identity === identity);
  const heard = lastMine ? langChip(lastMine.text) : null;

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcriptions.length]);

  return (
    <div className="flex w-full max-w-2xl flex-col gap-6">
      <section className="flex flex-col items-center gap-4 rounded-2xl bg-[var(--surface)] p-5 shadow-sm sm:p-8">
        <RexOrb state={state} level={level} />
        <div className="flex flex-wrap items-center justify-center gap-2" aria-live="polite">
          <p className="text-sm font-medium text-[var(--muted)]">
            {agent ? STATE_LABEL[state] ?? state : "Waiting for Rex to join…"}
          </p>
          {heard && (
            <span className="rounded-full bg-[var(--accent)]/15 px-2.5 py-0.5 text-xs font-medium text-[var(--accent)]">
              {LANG_NAME[heard] ?? heard}
            </span>
          )}
        </div>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <VoiceAssistantControlBar controls={{ leave: false }} />
          {/* Rex only looks when asked (look_at_screen); frames stay in memory, nothing is saved. */}
          <TrackToggle
            source={Track.Source.ScreenShare}
            captureOptions={{ audio: false }}
            className="rounded-full border border-[var(--muted)]/40 px-4 py-2 text-sm"
          >
            Share screen
          </TrackToggle>
          <DisconnectButton className="rounded-full border border-[var(--danger)] px-4 py-2 text-sm text-[var(--danger)]">
            End
          </DisconnectButton>
        </div>
        <StartAudio label="Tap to enable audio" className="rounded-full bg-[var(--accent)] px-4 py-2 text-white" />
      </section>

      <section className="rounded-2xl bg-[var(--surface)] p-4 shadow-sm">
        <h2 className="mb-3 text-sm font-semibold text-[var(--muted)]">Live transcript</h2>
        <ol className="flex max-h-[45vh] flex-col gap-3 overflow-y-auto" aria-live="polite">
          {transcriptions.length === 0 && <li className="text-sm text-[var(--muted)]">Say “Namaste Rex”…</li>}
          {transcriptions.map((t) => {
            const mine = t.participantInfo.identity === identity;
            return (
              <li key={t.streamInfo.id} className={`flex flex-col ${mine ? "items-end" : "items-start"}`}>
                <span className="mb-1 text-[11px] tracking-wide text-[var(--muted)]">
                  {mine ? "You" : "Rex"} · {langChip(t.text)}
                </span>
                <span
                  className={`max-w-[85%] rounded-2xl px-4 py-2 text-[15px] leading-relaxed ${
                    mine ? "bg-[var(--accent)] text-white" : "bg-[var(--bg)]"
                  }`}
                >
                  {t.text}
                </span>
              </li>
            );
          })}
          <div ref={endRef} />
        </ol>
      </section>
      <BrowserView />
      <Timeline />
      <Connections />
      <RoomAudioRenderer />
    </div>
  );
}
