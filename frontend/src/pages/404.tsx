import Link from "next/link";

export default function Custom404() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
      <span className="text-6xl mb-4">🔍</span>
      <h1 className="text-3xl font-bold text-gray-800 mb-2">Page not found</h1>
      <p className="text-gray-500 mb-6">The page you&apos;re looking for doesn&apos;t exist.</p>
      <Link
        href="/dashboard"
        className="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
      >
        Go to Dashboard
      </Link>
    </div>
  );
}
