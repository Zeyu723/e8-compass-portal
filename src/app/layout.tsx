import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Sovereign E8",
  description: "AI-powered Essential Eight cyber security assessment — Australian sovereign capability",
  icons: { icon: [{ url: "/favicon.ico" }, { url: "/favicon.png", type: "image/png" }], apple: "/logo.png" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico?v=3" sizes="any" />
        <link rel="icon" type="image/png" sizes="32x32" href="/favicon.png?v=3" />
        <link rel="apple-touch-icon" href="/logo.png?v=3" />
      </head>
      <body className={inter.className} suppressHydrationWarning>{children}</body>
    </html>
  );
}
