import "./globals.css";

export const metadata = {
  title: "Block Flow",
  description: "Visual API Block Builder",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}