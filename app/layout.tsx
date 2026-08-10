import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import NavBar from "@/components/NavBar";
import Script from "next/script";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "What Your ERP Cannot Tell You | C-Suite Intelligence Platform",
  description: "Forward-looking executive intelligence built on top of your ERP data.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <Script
          src="https://cdn.jsdelivr.net/npm/powerbi-client@2.23.1/dist/powerbi.min.js"
          strategy="beforeInteractive"
        />
      </head>
      <body className={inter.className}>
        <NavBar />
        <main className="min-h-screen bg-slate-50">{children}</main>
      </body>
    </html>
  );
}
