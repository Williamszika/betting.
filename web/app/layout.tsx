import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'SportPredix — Suivi',
  description: 'Coupons, résultats 🟢/🔴 et ROI — estimations, pas des garanties.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
