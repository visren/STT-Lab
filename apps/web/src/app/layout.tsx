import type { Metadata } from "next";
import { Figtree, Fraunces } from "next/font/google";
import { Nav } from "@/components/Nav";
import "./globals.css";

const display = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
});

const sans = Figtree({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "STT Lab",
  description: "Compare and adapt speech-to-text models on your own voice.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${display.variable} ${sans.variable} antialiased`}>
        <Nav />
        <main>{children}</main>
      </body>
    </html>
  );
}
