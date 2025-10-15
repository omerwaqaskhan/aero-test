import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WindWays - Where every journey finds its way",
  description: "Discover amazing travel deals and plan your perfect trip with WindWays",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased" suppressHydrationWarning={true}>
        {children}
      </body>
    </html>
  );
}
