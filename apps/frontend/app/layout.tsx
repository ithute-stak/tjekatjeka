import type { Metadata } from "next";
import "./globals.css";
import "./advanced.css";

export const metadata: Metadata = {
  title: "Tjekatjeka Holdings",
  description: "Operations, production, inventory, finance and fleet management for Tjekatjeka Holdings.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
