import { useRouter } from "next/router";
import { useQuery } from "@tanstack/react-query";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { connectionService, extractionService, storageService } from "@/services/api";
import Spinner from "@/components/Spinner";

export default function DashboardPage() {
  const { user, ready } = useRequireAuth();
  const router = useRouter();

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: async () => {
      const [conn, jobs, records, files] = await Promise.all([
        connectionService.list(),
        extractionService.getJobs(),
        storageService.getRecords(),
        storageService.getFiles(),
      ]);
      return {
        connections: conn.data.count ?? conn.data.length ?? 0,
        jobs: jobs.data.count ?? jobs.data.length ?? 0,
        records: records.data.count ?? records.data.length ?? 0,
        files: files.data.count ?? files.data.length ?? 0,
      };
    },
    enabled: !!user,
  });

  if (!ready) return <Spinner text="Loading dashboard..." />;

  const cards = [
    { label: "Connections", value: stats?.connections ?? 0, href: "/connections", color: "bg-blue-500", icon: "🔌" },
    { label: "Extraction Jobs", value: stats?.jobs ?? 0, href: "/extract", color: "bg-green-500", icon: "📦" },
    { label: "Processed Records", value: stats?.records ?? 0, href: "/files", color: "bg-purple-500", icon: "💾" },
    { label: "Exported Files", value: stats?.files ?? 0, href: "/files", color: "bg-orange-500", icon: "📄" },
  ];

  const steps = [
    { num: 1, text: "Create or test a database connection", href: "/connections" },
    { num: 2, text: "Extract data from a table in batches", href: "/extract" },
    { num: 3, text: "Edit data in the interactive grid", href: "/extract" },
    { num: 4, text: "Submit & export as JSON or CSV", href: "/files" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">
        Welcome, {user?.first_name || user?.username}
      </h1>
      <p className="text-gray-500 mb-6">Multi-Database Data Integration Platform</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {cards.map((card) => (
          <div
            key={card.label}
            onClick={() => router.push(card.href)}
            className="cursor-pointer bg-white rounded-xl shadow-sm border p-6 hover:shadow-md transition"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-2xl">{card.icon}</span>
              <div className={`w-3 h-3 rounded-full ${card.color}`} />
            </div>
            <p className="text-3xl font-bold">{statsLoading ? "—" : card.value}</p>
            <p className="text-sm text-gray-500 mt-1">{card.label}</p>
          </div>
        ))}
      </div>

      {/* Quick Start Guide */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="text-lg font-semibold mb-4">Quick Start</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {steps.map((step) => (
            <div
              key={step.num}
              onClick={() => router.push(step.href)}
              className="flex items-start space-x-3 p-3 rounded-lg border border-dashed border-gray-200 hover:border-blue-300 hover:bg-blue-50 cursor-pointer transition"
            >
              <span className="flex-shrink-0 w-7 h-7 rounded-full bg-blue-100 text-blue-700 text-sm font-bold flex items-center justify-center">
                {step.num}
              </span>
              <p className="text-sm text-gray-600">{step.text}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
