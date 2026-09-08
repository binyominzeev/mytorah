import type { Metadata } from "next";
import Script from "next/script";
import { Frank_Ruhl_Libre, Inter, Lora } from "next/font/google";
import "./globals.css";
import { getNavStructure } from "@/lib/content";
import Sidebar from "@/components/Sidebar";
import TopControls from "@/components/TopControls";

const fontHebrew = Frank_Ruhl_Libre({
  subsets: ["hebrew", "latin"],
  weight: ["400", "500", "700"],
  variable: "--font-hebrew",
  display: "swap",
});

const fontBody = Lora({
  subsets: ["latin", "latin-ext"],
  weight: ["400", "500", "600"],
  style: ["normal", "italic"],
  variable: "--font-body",
  display: "swap",
});

const fontUi = Inter({
  subsets: ["latin", "latin-ext"],
  weight: ["400", "500", "600"],
  variable: "--font-ui",
  display: "swap",
});

export const metadata: Metadata = {
  title: "The Essentialist Torah",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const nav = getNavStructure();

  return (
    <html lang="hu" className={`${fontHebrew.variable} ${fontBody.variable} ${fontUi.variable}`}>
      <body>
        <Script
          async
          src="https://www.googletagmanager.com/gtag/js?id=G-H8D9YRFC61"
          strategy="afterInteractive"
        />
        <TopControls />
        <Sidebar nav={nav} />
        {children}
      </body>
    </html>
  );
}
