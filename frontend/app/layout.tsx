// frontend/app/layout.tsx

import type { Metadata } from 'next';
import Header from './components/Header';
import './globals.css';

export const metadata: Metadata = {
  title: 'Nivesha',
  description: 'Grounded in Insights, Driven by Growth',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans antialiased">
        <Header />
        {/*
          Add a container that wraps all pages:
          - max-w-4xl: Limits width to a comfortable reading size
          - mx-auto: Centers horizontally
          - px-6, py-8: Adds uniform horizontal & vertical padding
          - space-y-8: Adds vertical spacing between any stacked elements inside
        */}
        <main className="max-w-8xl mx-auto px-8 py-8 space-y-8 pt-24">
          {children}
        </main>
      </body>
    </html>
  );
}
