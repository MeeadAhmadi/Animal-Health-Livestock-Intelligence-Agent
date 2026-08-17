import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Livestock Intelligence",
  description: "Animal Health, Livestock Intelligence & Early-Warning System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
