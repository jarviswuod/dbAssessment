import { useState } from "react";
import { useRouter } from "next/router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { connectionService, ConnectionInput } from "@/services/api";
import { DB_TYPE_COLORS } from "@/constants";
import ConnectionForm from "@/components/ConnectionForm";
import Spinner from "@/components/Spinner";
import EmptyState from "@/components/EmptyState";
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
  const { user, ready } = useRequireAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [testingId, setTestingId] = useState<number | null>(null);

  const { data: connections = [] } = useQuery<Connection[]>({
    queryKey: ["connections"],
    queryFn: async () => {
      const res = await connectionService.list();
      return res.data.results ?? res.data;
    },
    enabled: !!user,
  });

  const createMutation = useMutation({
    mutationFn: (formData: { name: string; db_type: string; host: string; port: string; username: string; password: string; database: string }) => {
      const input: ConnectionInput = { ...formData, port: parseInt(formData.port) };
      return connectionService.create(input);
    },
    onSuccess: () => {
      toast.success("Connection created");
      setShowForm(false);
      queryClient.invalidateQueries({ queryKey: ["connections"] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.error?.message || "Failed to create connection");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => connectionService.delete(id),
    onSuccess: () => {
      toast.success("Connection deleted");
      queryClient.invalidateQueries({ queryKey: ["connections"] });
    },
    onError: () => {
      toast.error("Failed to delete");
    },
  });

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
    deleteMutation.mutate(id);
  };

  if (!ready) return <Spinner text="Loading connections..." />;

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
            onSubmit={(data) => createMutation.mutate(data)}
            onCancel={() => setShowForm(false)}
            loading={createMutation.isPending}
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
                  <span className={`px-2 py-1 rounded text-xs font-medium ${DB_TYPE_COLORS[conn.db_type] || "bg-gray-100"}`}>
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
                <td colSpan={5}>
                  <EmptyState
                    icon="🔌"
                    title="No connections yet"
                    description="Add a database connection to start extracting and processing data."
                    action={{ label: "+ New Connection", onClick: () => setShowForm(true) }}
                  />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
