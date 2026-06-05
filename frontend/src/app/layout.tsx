import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FlowCompiler — AI Application Compiler",
  description:
    "Convert natural language software requirements into complete executable application configurations.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
