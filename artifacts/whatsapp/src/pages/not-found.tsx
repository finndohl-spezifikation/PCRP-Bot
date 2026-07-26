import { Link } from "wouter";

export default function NotFound() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-[#f0f2f5] w-full">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-[#111b21] mb-4">404</h1>
        <p className="text-[#667781] mb-6">Page not found</p>
        <Link href="/">
          <span className="bg-[#00a884] text-white px-6 py-2 rounded-full inline-block cursor-pointer">
            Go Home
          </span>
        </Link>
      </div>
    </div>
  );
}
