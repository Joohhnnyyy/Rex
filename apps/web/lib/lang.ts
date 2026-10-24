// Script-based language chip for transcript lines (mirrors apps/agent/src/rex_agent/lang.py).
const SCRIPTS: [number, number, string][] = [
  [0x0900, 0x097f, "HI"],
  [0x0980, 0x09ff, "BN"],
  [0x0a00, 0x0a7f, "PA"],
  [0x0a80, 0x0aff, "GU"],
  [0x0b80, 0x0bff, "TA"],
  [0x0c00, 0x0c7f, "TE"],
  [0x0c80, 0x0cff, "KN"],
  [0x0d00, 0x0d7f, "ML"],
];
const HINGLISH = new Set(
  "kal aaj baje ke ki ka ko se mein main hai hain karo kar karke rakho saath bhejo batao kya nahi haan theek accha ruko mujhe mera aap wala hoga abhi phir liye yeh ye".split(
    " ",
  ),
);

export function langChip(text: string): string {
  const counts: Record<string, number> = {};
  for (const ch of text) {
    const cp = ch.codePointAt(0) ?? 0;
    for (const [lo, hi, code] of SCRIPTS) {
      if (cp >= lo && cp <= hi) {
        counts[code] = (counts[code] ?? 0) + 1;
        break;
      }
    }
  }
  const best = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
  if (best) return best[0];
  const words = text.toLowerCase().match(/[a-z]+/g) ?? [];
  const hindi = words.filter((w) => HINGLISH.has(w)).length;
  if (words.length && (hindi >= 2 || hindi / words.length >= 0.25)) return "HINGLISH";
  return "EN";
}
