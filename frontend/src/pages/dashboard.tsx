import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { useAuth } from "@/context/AuthContext";
import { connectionService, extractionService, storageService } from "@/services/api";

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState({
    connections: 0,
    jobs: 0,
    records: 0,
    files: 0,
  });

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
      Promise.all([
        connectionService.list(),
        extractionService.getJobs(),
        storageService.getRecords(),
        storageService.getFiles(),
      ]).then(([conn, jobs, records, files]) => {
        setStats({
          connections: conn.data.results?.length ?? conn.data.length ?? 0,
          jobs: jobs.data.length ?? 0,
          records: records.data.length ?? 0,
          files: files.data.length ?? 0,
        });
      });
    }
  }, [user]);

  if (loading || !user) return null;

  const cards = [
    { label: "Connections", value: stats.connections, href: "/connections", color: "bg-blue-500" },
    { label: "Extraction Jobs", value: stats.jobs, href: "/extract", color: "bg-green-500" },
    { label: "Processed Records", value: stats.records, href: "/files", color: "bg-purple-500" },
    { label: "Exported Files", value: stats.files, href: "/files", color: "bg-orange-500" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">
        Welcome, {user.first_name || user.username}
      </h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((card) => (
          <div
            key={card.label}
            onClick={() => router.push(card.href)}
            className="cursor-pointer bg-white rounded-xl shadow-sm border p-6 hover:shadow-md transition"
          >
            <div className={`w-10 h-10 rounded-lg ${card.color} mb-3`} />
            <p className="text-3xl font-bold">{card.value}</p>
            <p className="text-sm text-gray-500 mt-1">{card.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
