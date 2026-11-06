import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Rex",
  description: "Multilingual voice operator built on Gnani Prisma STT and Timbre TTS",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      {/* Extensions (e.g. ColorZilla's cz-shortcut-listen) add attributes to <body> before hydration. */}
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
