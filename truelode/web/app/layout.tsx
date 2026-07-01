import type { Metadata } from "next";

import { AuthProvider } from "@/lib/auth";

import "./globals.css";

export const metadata: Metadata = {
  title: "Truelode — chain of custody",
  description: "Proving Zimbabwean lithium is clean, from mine to passport.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
