import "./globals.css";

export const metadata = {
  title: "Folio",
  description: "Ask the page. Document question answering.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
