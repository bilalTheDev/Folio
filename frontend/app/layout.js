import { Inter, Newsreader } from "next/font/google";
import Script from "next/script";
import { THEME_SCRIPT } from "@/lib/theme";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

// Licensed Waldenburg Light substitute: Newsreader at 300, same editorial display weight.
const display = Newsreader({
  variable: "--font-display-serif",
  subsets: ["latin"],
  weight: "300",
});

export const metadata = {
  title: "Folio",
  description: "Chat with your documents using your own inference key, with citations you can check.",
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${display.variable} h-full scroll-smooth antialiased`}
      data-scroll-behavior="smooth"
      suppressHydrationWarning
    >
      <body className="flex min-h-full flex-col" suppressHydrationWarning>
        <Script id="folio-theme" strategy="beforeInteractive">
          {THEME_SCRIPT}
        </Script>
        {children}
      </body>
    </html>
  );
}
