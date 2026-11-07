import { Fragment, type ReactNode } from "react";

// Gnani timbre-v3.0 acts these out ("<laugh>"); they are stage directions, not words to show.
export const AUDIO_TAG = /<(laugh|giggle|excited|sigh|pauses|whispers|exhales|coughs|shouting|slow|sniffles|yawns|clears throat)>/gi;

export const stripTags = (text: string) => text.replace(AUDIO_TAG, "").replace(/[ \t]{2,}/g, " ").trim();

const INLINE = /(\*\*[^*]+\*\*|https?:\/\/[^\s)]+)/g;

function inline(text: string): ReactNode[] {
  return text.split(INLINE).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={i}>{part.slice(2, -2)}</strong>;
    if (/^https?:\/\//.test(part))
      return (
        <a key={i} href={part} target="_blank" rel="noreferrer noopener" className="break-all underline decoration-[var(--red-hi)]/60 underline-offset-2">
          {part.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, "")}
        </a>
      );
    return <Fragment key={i}>{part}</Fragment>;
  });
}

// Rex's replies: paragraphs, "- " bullet lists, **bold** and links. Nothing else, so it stays predictable.
export function RichText({ text }: { text: string }) {
  const blocks: ReactNode[] = [];
  let list: string[] = [];
  const flush = () => {
    if (!list.length) return;
    blocks.push(
      <ul key={blocks.length} className="my-1 list-disc space-y-0.5 pl-5">
        {list.map((item, i) => (
          <li key={i}>{inline(item)}</li>
        ))}
      </ul>,
    );
    list = [];
  };
  for (const line of stripTags(text).split("\n")) {
    const bullet = line.match(/^\s*(?:[-*•]|\d+[.)])\s+(.*)$/);
    if (bullet) list.push(bullet[1]);
    else {
      flush();
      if (line.trim()) blocks.push(<p key={blocks.length}>{inline(line)}</p>);
    }
  }
  flush();
  return <div className="flex flex-col gap-1.5">{blocks}</div>;
}
