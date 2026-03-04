import './globals.css';
import Sidebar from '@/components/Sidebar';

export const metadata = {
  title: 'Zentivra — Frontier AI Radar',
  description: 'Multi-agent intelligence system tracking AI industry developments with daily executive digests.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="layout">
          <Sidebar />
          <main className="main-content">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
