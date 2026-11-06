"use client";

import { useRoomContext } from "@livekit/components-react";
import { useEffect, useState } from "react";

// Live view of Rex's browser: the agent streams a JPEG of the page (about 1 per second, only on change)
// on the "rex.browser" topic. Only the newest frame is kept, so memory stays flat.
type Frame = { url: string; title: string; ts: number; img: string };

export function BrowserView() {
  const room = useRoomContext();
  const [frame, setFrame] = useState<Frame | null>(null);

  useEffect(() => {
    room.registerTextStreamHandler("rex.browser", async (reader) => {
      try {
        const f = JSON.parse(await reader.readAll()) as Frame;
        setFrame((prev) => (prev && prev.ts >= f.ts ? prev : f));
      } catch {
        /* a dropped or partial frame: the next one replaces it */
      }
    });
    return () => room.unregisterTextStreamHandler("rex.browser");
  }, [room]);

  if (!frame) return null;

  const host = (() => {
    try {
      return new URL(frame.url).host;
    } catch {
      return frame.url;
    }
  })();

  return (
    <section className="overflow-hidden rounded-2xl bg-[var(--surface)] shadow-sm" aria-label="Rex's browser">
      <div className="flex items-center gap-2 border-b border-[var(--muted)]/15 px-4 py-2">
        <span className="flex gap-1.5" aria-hidden>
          <span className="size-2.5 rounded-full bg-[var(--danger)]/70" />
          <span className="size-2.5 rounded-full bg-[var(--warn)]/70" />
          <span className="size-2.5 rounded-full bg-[var(--ok)]/70" />
        </span>
        <span
          className="min-w-0 flex-1 truncate rounded-full bg-[var(--bg)] px-3 py-1 text-xs text-[var(--muted)]"
          title={frame.url}
        >
          {host}
        </span>
        <span className="flex items-center gap-1 text-[11px] text-[var(--muted)]">
          <span className="size-1.5 animate-pulse rounded-full bg-[var(--accent)]" aria-hidden /> Live
        </span>
      </div>
      {/* eslint-disable-next-line @next/next/no-img-element -- data: URL frames, next/image adds nothing */}
      <img src={frame.img} alt={`Rex's browser showing ${frame.title || host}`} className="block w-full" />
    </section>
  );
}
