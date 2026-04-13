import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/router";
import { useAuth } from "@/context/AuthContext";
import { connectionService, extractionService, storageService } from "@/services/api";
import EditableGrid from "@/components/EditableGrid";
import toast from "react-hot-toast";

interface Connection {
  id: number;
  name: string;
  db_type: string;
}

export default function ExtractPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const [connections, setConnections] = useState<Connection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<number | null>(null);
  const [tables, setTables] = useState<string[]>([]);
  const [selectedTable, setSelectedTable] = useState("");
  const [batchSize, setBatchSize] = useState(100);
  const [offset, setOffset] = useState(0);

  const [columns, setColumns] = useState<{ key: string; label: string }[]>([]);
  const [data, setData] = useState<Record<string, any>[]>([]);
  const [totalRows, setTotalRows] = useState(0);
  const [extracting, setExtracting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [exportFormat, setExportFormat] = useState("json");

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
      connectionService.list().then((res) => {
        const conns = res.data.results ?? res.data;
        setConnections(conns);
        const preselect = router.query.connection;
        if (preselect) {
          setSelectedConnection(Number(preselect));
        }
      });
    }
  }, [user, router.query.connection]);

  useEffect(() => {
    if (selectedConnection) {
      connectionService.getTables(selectedConnection).then((res) => {
        setTables(res.data.tables);
        setSelectedTable("");
        setData([]);
        setColumns([]);
      }).catch(() => toast.error("Failed to fetch tables"));
    }
  }, [selectedConnection]);

  const handleExtract = async () => {
    if (!selectedConnection || !selectedTable) return;
    setExtracting(true);
    try {
      const { data: result } = await extractionService.extract({
        connection_id: selectedConnection,
        table_name: selectedTable,
        batch_size: batchSize,
        offset,
      });
      setData(result.data);
      setTotalRows(result.total_rows);
      setColumns(
        result.columns.map((c: string) => ({ key: c, label: c }))
      );
      toast.success(`Extracted ${result.data.length} rows`);
    } catch (err: any) {
      toast.error(err.response?.data?.error || "Extraction failed");
    } finally {
      setExtracting(false);
    }
  };

  const handleDataChange = useCallback((newData: Record<string, any>[]) => {
    setData(newData);
  }, []);

  const handleSubmit = async () => {
    if (!selectedConnection || !selectedTable || data.length === 0) return;
    setSubmitting(true);
    try {
      const { data: result } = await storageService.submit({
        connection_id: selectedConnection,
        table_name: selectedTable,
        data,
        export_format: exportFormat,
      });
      toast.success(
        `Saved ${result.row_count} rows. File: ${result.file_name}`
      );
    } catch (err: any) {
      toast.error(err.response?.data?.error || "Submit failed");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading || !user) return null;

  const hasMore = offset + batchSize < totalRows;
  const hasPrev = offset > 0;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Extract & Edit Data</h1>

      {/* Controls */}
      <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Connection</label>
            <select
              value={selectedConnection ?? ""}
              onChange={(e) => setSelectedConnection(Number(e.target.value) || null)}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            >
              <option value="">Select connection...</option>
              {connections.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.db_type})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Table</label>
            <select
              value={selectedTable}
              onChange={(e) => setSelectedTable(e.target.value)}
              disabled={tables.length === 0}
              className="w-full border rounded-lg px-3 py-2 text-sm disabled:opacity-50"
            >
              <option value="">Select table...</option>
              {tables.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Batch Size</label>
            <input
              type="number"
              value={batchSize}
              onChange={(e) => setBatchSize(Math.max(1, parseInt(e.target.value) || 100))}
              min={1}
              max={10000}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleExtract}
              disabled={!selectedConnection || !selectedTable || extracting}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm"
            >
              {extracting ? "Extracting..." : "Extract Data"}
            </button>
          </div>
        </div>
      </div>

      {/* Data Grid */}
      {data.length > 0 && (
        <>
          <div className="flex justify-between items-center mb-4">
            <p className="text-sm text-gray-500">
              Showing rows {offset + 1}–{Math.min(offset + data.length, totalRows)} of {totalRows}
              <span className="ml-2 text-blue-600 font-medium">
                (Double-click cells to edit)
              </span>
            </p>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => { setOffset(Math.max(0, offset - batchSize)); }}
                disabled={!hasPrev}
                className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-30"
              >
                ← Prev
              </button>
              <button
                onClick={() => { setOffset(offset + batchSize); }}
                disabled={!hasMore}
                className="px-3 py-1 text-sm border rounded hover:bg-gray-50 disabled:opacity-30"
              >
                Next →
              </button>
            </div>
          </div>

          <EditableGrid columns={columns} data={data} onDataChange={handleDataChange} />

          {/* Submit Controls */}
          <div className="mt-6 flex items-center justify-between bg-white rounded-xl shadow-sm border p-4">
            <div className="flex items-center space-x-4">
              <label className="text-sm font-medium text-gray-700">Export Format:</label>
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value)}
                className="border rounded-lg px-3 py-1.5 text-sm"
              >
                <option value="json">JSON</option>
                <option value="csv">CSV</option>
              </select>
            </div>
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm font-medium"
            >
              {submitting ? "Submitting..." : "Submit & Export Data"}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
