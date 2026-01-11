import { Nunito } from 'next/font/google';
import 'reactflow/dist/style.css';
import './globals.css';

const nunito = Nunito({ subsets: ['latin'] });

export const metadata = {
  title: 'Flow Builder',
  description: 'A visual programming interface',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={nunito.className}>{children}</body>
    </html>
  );
}