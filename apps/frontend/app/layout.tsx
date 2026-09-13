import type { Metadata } from "next";
import "./globals.css";
import "./advanced.css";
import "./enterprise.css";
import "./desktop-compat.css";

export const metadata: Metadata = {
  title: "Tjekatjeka Holdings",
  description: "Enterprise operations, production, inventory, finance, people, governance and fleet management for Tjekatjeka Holdings.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
