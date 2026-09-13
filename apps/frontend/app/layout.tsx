import type { Metadata } from "next";
import "./globals.css";
import "./advanced.css";
import "./enterprise.css";
import "./desktop-compat.css";
import "./login.css";
import "./branding.css";
import "./dialog.css";

export const metadata: Metadata = {
  title: "Tjekatjeka Holdings",
  description: "Enterprise operations, production, inventory, finance, people, governance and fleet management for Tjekatjeka Holdings.",
  icons: {
    icon: "/brand/tjekatjeka-brand.webp",
    shortcut: "/brand/tjekatjeka-brand.webp",
    apple: "/brand/tjekatjeka-brand.webp",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
