import { useState } from "react";
import { useRouter } from "next/router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { DB_TYPE_COLORS } from "@/constants";
import { storageService } from "@/services/api";
import toast from "react-hot-toast";

interface ExportedFile {
  id: number;
  username: string;
  file_format: string;
  file_name: string;
  source_db_type: string;
  source_table: string;
  is_shared: boolean;
  created_at: string;
}

interface ProcessedRecord {
  id: number;
  username: string;
  connection_name: string;
  source_db_type: string;
  source_table: string;
  row_count: number;
  created_at: string;
}

export default function FilesPage() {
  const { user, ready, isAdmin } = useRequireAuth();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"files" | "records">("files");

  const { data: files = [] } = useQuery<ExportedFile[]>({
    queryKey: ["files"],
    queryFn: async () => {
      const res = await storageService.getFiles();
      return res.data.results ?? res.data;
    },
    enabled: !!user,
  });

  const { data: records = [] } = useQuery<ProcessedRecord[]>({
    queryKey: ["records"],
    queryFn: async () => {
      const res = await storageService.getRecords();
      return res.data.results ?? res.data;
    },
    enabled: !!user,
  });

  const shareMutation = useMutation({
    mutationFn: (fileId: number) => storageService.shareFile(fileId),
    onSuccess: (res) => {
      toast.success(res.data.is_shared ? "File shared" : "File unshared");
      queryClient.invalidateQueries({ queryKey: ["files"] });
    },
    onError: () => {
      toast.error("Failed to update sharing");
    },
  });

  const handleDownload = async (file: ExportedFile) => {
    try {
      const response = await storageService.downloadFile(file.id);
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = file.file_name;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error("Download failed");
    }
  };

  const handleShare = async (fileId: number) => {
    shareMutation.mutate(fileId);
  };

  const formatDate = (isoStr: string) =>
    new Date(isoStr).toLocaleString();

  if (!ready) return null;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Processed Data & Files</h1>

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-100 rounded-lg p-1 w-fit mb-6">
        <button
          onClick={() => setTab("files")}
          className={`px-4 py-2 rounded-md text-sm font-medium transition ${
            tab === "files" ? "bg-white shadow text-gray-900" : "text-gray-500"
          }`}
        >
          Exported Files ({files.length})
        </button>
        <button
          onClick={() => setTab("records")}
          className={`px-4 py-2 rounded-md text-sm font-medium transition ${
            tab === "records" ? "bg-white shadow text-gray-900" : "text-gray-500"
          }`}
        >
          DB Records ({records.length})
        </button>
      </div>

      {tab === "files" && (
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">File Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Format</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Owner</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {files.map((f) => (
                <tr key={f.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium">{f.file_name}</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100">
                      {f.file_format.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${DB_TYPE_COLORS[f.source_db_type] || "bg-gray-100"}`}>
                      {f.source_db_type}
                    </span>
                    <span className="ml-2 text-sm text-gray-500">{f.source_table}</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {f.username}
                    {f.is_shared && (
                      <span className="ml-1 text-xs text-green-600">(shared)</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{formatDate(f.created_at)}</td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <button
                      onClick={() => handleDownload(f)}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      Download
                    </button>
                    {(f.username === user?.username || isAdmin) && (
                      <button
                        onClick={() => handleShare(f.id)}
                        className="text-sm text-purple-600 hover:text-purple-800"
                      >
                        {f.is_shared ? "Unshare" : "Share"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {files.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-400">
                    No exported files yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {tab === "records" && (
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Table</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rows</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Owner</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {records.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-mono">{r.id}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${DB_TYPE_COLORS[r.source_db_type] || "bg-gray-100"}`}>
                      {r.source_db_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm">{r.source_table}</td>
                  <td className="px-6 py-4 text-sm font-medium">{r.row_count}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{r.username}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{formatDate(r.created_at)}</td>
                </tr>
              ))}
              {records.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-400">
                    No processed records yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
