import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";

import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "Rex Control Center",
  description: "Multilingual voice operator built on Gnani Prisma STT and Timbre TTS",
  // favicon.ico, icon.svg and apple-icon.png in app/ are picked up automatically (design/logo/kit).
  manifest: "/site.webmanifest",
};

export const viewport: Viewport = { themeColor: "#090A0D" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={inter.variable}>
      {/* Extensions (e.g. ColorZilla's cz-shortcut-listen) add attributes to <body> before hydration. */}
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
