import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { useAuth } from "@/context/AuthContext";
import { connectionService } from "@/services/api";
import ConnectionForm from "@/components/ConnectionForm";
import toast from "react-hot-toast";

interface Connection {
  id: number;
  name: string;
  db_type: string;
  host: string;
  port: number;
  username: string;
  database: string;
  is_active: boolean;
  created_at: string;
}

export default function ConnectionsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [connections, setConnections] = useState<Connection[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [testingId, setTestingId] = useState<number | null>(null);

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [user, loading, router]);

  const fetchConnections = () => {
    connectionService.list().then((res) => {
      setConnections(res.data.results ?? res.data);
    });
  };

  useEffect(() => {
    if (user) fetchConnections();
  }, [user]);

  const handleCreate = async (data: any) => {
    setFormLoading(true);
    try {
      await connectionService.create({ ...data, port: parseInt(data.port) });
      toast.success("Connection created");
      setShowForm(false);
      fetchConnections();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to create connection");
    } finally {
      setFormLoading(false);
    }
  };

  const handleTest = async (id: number) => {
    setTestingId(id);
    try {
      const { data } = await connectionService.test(id);
      if (data.success) {
        toast.success("Connection successful!");
      } else {
        toast.error("Connection failed");
      }
    } catch {
      toast.error("Connection test failed");
    } finally {
      setTestingId(null);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this connection?")) return;
    try {
      await connectionService.delete(id);
      toast.success("Connection deleted");
      fetchConnections();
    } catch {
      toast.error("Failed to delete");
    }
  };

  const dbTypeColors: Record<string, string> = {
    postgres: "bg-blue-100 text-blue-800",
    mysql: "bg-orange-100 text-orange-800",
    mongodb: "bg-green-100 text-green-800",
    clickhouse: "bg-yellow-100 text-yellow-800",
  };

  if (loading || !user) return null;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Database Connections</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
        >
          {showForm ? "Cancel" : "+ New Connection"}
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">New Connection</h2>
          <ConnectionForm
            onSubmit={handleCreate}
            onCancel={() => setShowForm(false)}
            loading={formLoading}
          />
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Host</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Database</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {connections.map((conn) => (
              <tr key={conn.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 text-sm font-medium">{conn.name}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${dbTypeColors[conn.db_type] || "bg-gray-100"}`}>
                    {conn.db_type}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">{conn.host}:{conn.port}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{conn.database}</td>
                <td className="px-6 py-4 text-right space-x-2">
                  <button
                    onClick={() => handleTest(conn.id)}
                    disabled={testingId === conn.id}
                    className="text-sm text-green-600 hover:text-green-800 disabled:opacity-50"
                  >
                    {testingId === conn.id ? "Testing..." : "Test"}
                  </button>
                  <button
                    onClick={() => router.push(`/extract?connection=${conn.id}`)}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    Extract
                  </button>
                  <button
                    onClick={() => handleDelete(conn.id)}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {connections.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-gray-400">
                  No connections yet. Create one to get started.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
