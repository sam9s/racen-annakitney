import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'SOMERA - Your Empathetic Coaching Companion',
  description: 'SOMERA is your empathetic coaching companion, offering guidance on life challenges through Shweta\'s coaching wisdom.',
  icons: {
    icon: '/somera-favicon.png',
    apple: '/somera-favicon.png',
  },
};

export default function SomeraLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
