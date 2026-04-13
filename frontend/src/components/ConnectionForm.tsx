"use client";

import React from "react";

interface ConnectionFormData {
  name: string;
  db_type: string;
  host: string;
  port: string;
  username: string;
  password: string;
  database: string;
}

interface ConnectionFormProps {
  initialData?: Partial<ConnectionFormData>;
  onSubmit: (data: ConnectionFormData) => void;
  onCancel: () => void;
  loading?: boolean;
}

const DB_TYPES = [
  { value: "postgres", label: "PostgreSQL", defaultPort: "5432" },
  { value: "mysql", label: "MySQL", defaultPort: "3306" },
  { value: "mongodb", label: "MongoDB", defaultPort: "27017" },
  { value: "clickhouse", label: "ClickHouse", defaultPort: "8123" },
];

export default function ConnectionForm({
  initialData,
  onSubmit,
  onCancel,
  loading,
}: ConnectionFormProps) {
  const [form, setForm] = React.useState<ConnectionFormData>({
    name: initialData?.name || "",
    db_type: initialData?.db_type || "postgres",
    host: initialData?.host || "",
    port: initialData?.port || "5432",
    username: initialData?.username || "",
    password: initialData?.password || "",
    database: initialData?.database || "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setForm((prev) => {
      const updated = { ...prev, [name]: value };
      if (name === "db_type") {
        const dbType = DB_TYPES.find((d) => d.value === value);
        if (dbType) updated.port = dbType.defaultPort;
      }
      return updated;
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Connection Name
          </label>
          <input
            name="name"
            value={form.name}
            onChange={handleChange}
            required
            className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
            placeholder="My Database"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Database Type
          </label>
          <select
            name="db_type"
            value={form.db_type}
            onChange={handleChange}
            className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
          >
            {DB_TYPES.map((db) => (
              <option key={db.value} value={db.value}>
                {db.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Host</label>
          <input
            name="host"
            value={form.host}
            onChange={handleChange}
            required
            className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
            placeholder="localhost"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Port</label>
          <input
            name="port"
            value={form.port}
            onChange={handleChange}
            required
            type="number"
            className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
          <input
            name="username"
            value={form.username}
            onChange={handleChange}
            required
            className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input
            name="password"
            value={form.password}
            onChange={handleChange}
            required
            type="password"
            className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Database Name
          </label>
          <input
            name="database"
            value={form.database}
            onChange={handleChange}
            required
            className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>
      <div className="flex justify-end space-x-3 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm border rounded-lg text-gray-700 hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Saving..." : "Save Connection"}
        </button>
      </div>
    </form>
  );
}
