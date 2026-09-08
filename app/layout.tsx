import type { Metadata } from "next";
import Script from "next/script";
import { Frank_Ruhl_Libre, Inter, Lora } from "next/font/google";
import localFont from "next/font/local";
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

// Self-hosted so the biblical Hebrew text renders correctly even for readers
// who don't have Taamey Frank installed locally. Files are GPLv2-licensed
// (Culmus project), fetched from Sefaria's public static assets.
const fontHebrewText = localFont({
  src: [
    { path: "../public/fonts/taamey-frank/TaameyFrankCLM-Medium.ttf", weight: "400", style: "normal" },
    { path: "../public/fonts/taamey-frank/TaameyFrankCLM-Bold.ttf", weight: "700", style: "normal" },
    { path: "../public/fonts/taamey-frank/TaameyFrankCLM-MediumOblique.ttf", weight: "400", style: "italic" },
    { path: "../public/fonts/taamey-frank/TaameyFrankCLM-BoldOblique.ttf", weight: "700", style: "italic" },
  ],
  variable: "--font-hebrew-text",
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
  appleWebApp: {
    capable: true,
    title: "The Essentialist Torah",
    statusBarStyle: "black-translucent",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const nav = getNavStructure();

  return (
    <html
      lang="hu"
      className={`${fontHebrew.variable} ${fontHebrewText.variable} ${fontBody.variable} ${fontUi.variable}`}
    >
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
