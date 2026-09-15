import "./globals.css";

export const metadata = {
  title: "AquaSense OS",
  description: "Commercial Facility Intelligence",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#0b0f19] text-white antialiased">
        {children}
      </body>
    </html>
  );
}