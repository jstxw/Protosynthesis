import 'reactflow/dist/style.css';
import './globals.css';
import { Providers } from '@/components/Providers';

export const metadata = {
  title: 'NodeLink - API Workflow Builder',
  description: 'Build API workflows visually with authentication',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}