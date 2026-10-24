import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Rex",
  description: "Multilingual voice operator built on Gnani Prisma STT and Timbre TTS",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
