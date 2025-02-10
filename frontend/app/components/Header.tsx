import Image from 'next/image';

export default function Header() {
  return (
    <header className="fixed top-0 left-0 w-full bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-50">
      <div className="container flex h-20 items-center px-8 py-4">
        <div className="flex items-center">
          <Image
            src="/ক.png"
            alt="Nivesha Logo"
            width={32}
            height={32}
            className="object-contain"
          />
        </div>
      </div>
    </header>
  );
}