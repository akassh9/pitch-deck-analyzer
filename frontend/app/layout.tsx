import type { Metadata } from 'next';
import { Roboto as FontSans } from 'next/font/google';
import { Young_Serif as FontSerif } from 'next/font/google';
import Header from './components/Header';
import './globals.css';

const fontSans = FontSans({
  weight: ['400', '500', '700'],
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
});

const fontSerif = FontSerif({
  weight: '400', // Added required weight - Young Serif only comes in 400 weight
  subsets: ['latin'],
  variable: '--font-serif',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Nivesha',
  description: 'Grounded in Insights, Driven by Growth',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${fontSans.variable} ${fontSerif.variable} font-sans antialiased`}>
        <Header />
        <main className="pt-20">
          {children}
        </main>
      </body>
    </html>
  );
}
