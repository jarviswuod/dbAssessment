"use client";

import React, { useState, useCallback } from "react";

interface Column {
  key: string;
  label: string;
}

interface EditableGridProps {
  columns: Column[];
  data: Record<string, any>[];
  onDataChange: (data: Record<string, any>[]) => void;
}

export default function EditableGrid({ columns, data, onDataChange }: EditableGridProps) {
  const [editingCell, setEditingCell] = useState<{ row: number; col: string } | null>(null);
  const [editValue, setEditValue] = useState("");

  const startEdit = (rowIdx: number, colKey: string, value: any) => {
    setEditingCell({ row: rowIdx, col: colKey });
    setEditValue(value == null ? "" : String(value));
  };

  const commitEdit = useCallback(() => {
    if (!editingCell) return;
    const updated = [...data];
    updated[editingCell.row] = {
      ...updated[editingCell.row],
      [editingCell.col]: editValue,
    };
    onDataChange(updated);
    setEditingCell(null);
  }, [editingCell, editValue, data, onDataChange]);

  const cancelEdit = () => {
    setEditingCell(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") commitEdit();
    if (e.key === "Escape") cancelEdit();
  };

  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">No data to display</div>
    );
  }

  return (
    <div className="overflow-x-auto border rounded-lg">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              #
            </th>
            {columns.map((col) => (
              <th
                key={col.key}
                className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((row, rowIdx) => (
            <tr key={rowIdx} className="hover:bg-gray-50">
              <td className="px-4 py-2 text-sm text-gray-400">{rowIdx + 1}</td>
              {columns.map((col) => (
                <td
                  key={col.key}
                  className="px-4 py-2 text-sm cursor-pointer"
                  onDoubleClick={() => startEdit(rowIdx, col.key, row[col.key])}
                >
                  {editingCell?.row === rowIdx && editingCell?.col === col.key ? (
                    <input
                      type="text"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onBlur={commitEdit}
                      onKeyDown={handleKeyDown}
                      autoFocus
                      className="w-full px-2 py-1 border border-blue-400 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  ) : (
                    <span className="block truncate max-w-xs">
                      {row[col.key] == null ? (
                        <span className="text-gray-300 italic">null</span>
                      ) : (
                        String(row[col.key])
                      )}
                    </span>
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
