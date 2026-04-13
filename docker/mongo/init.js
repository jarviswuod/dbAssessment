// Seed data for MongoDB test database
db = db.getSiblingDB('testdb');

db.createUser({
  user: 'testuser',
  pwd: 'testpass',
  roles: [{ role: 'readWrite', db: 'testdb' }]
});

db.sensors.insertMany([
  { sensor_id: "SENS-001", location: "Building A - Floor 1", type: "temperature", value: 22.5, unit: "°C", timestamp: new Date("2024-01-15T08:30:00Z") },
  { sensor_id: "SENS-002", location: "Building A - Floor 2", type: "humidity", value: 45.2, unit: "%", timestamp: new Date("2024-01-15T08:30:00Z") },
  { sensor_id: "SENS-003", location: "Building B - Floor 1", type: "temperature", value: 21.8, unit: "°C", timestamp: new Date("2024-01-15T08:31:00Z") },
  { sensor_id: "SENS-004", location: "Building B - Floor 3", type: "pressure", value: 1013.25, unit: "hPa", timestamp: new Date("2024-01-15T08:31:00Z") },
  { sensor_id: "SENS-005", location: "Warehouse", type: "temperature", value: 18.3, unit: "°C", timestamp: new Date("2024-01-15T08:32:00Z") },
  { sensor_id: "SENS-006", location: "Warehouse", type: "humidity", value: 38.7, unit: "%", timestamp: new Date("2024-01-15T08:32:00Z") },
  { sensor_id: "SENS-007", location: "Server Room", type: "temperature", value: 19.1, unit: "°C", timestamp: new Date("2024-01-15T08:33:00Z") },
  { sensor_id: "SENS-008", location: "Server Room", type: "humidity", value: 30.5, unit: "%", timestamp: new Date("2024-01-15T08:33:00Z") },
  { sensor_id: "SENS-009", location: "Office Wing C", type: "co2", value: 412, unit: "ppm", timestamp: new Date("2024-01-15T08:34:00Z") },
  { sensor_id: "SENS-010", location: "Lobby", type: "temperature", value: 23.0, unit: "°C", timestamp: new Date("2024-01-15T08:35:00Z") }
]);

db.events.insertMany([
  { event_type: "login", user: "admin", ip: "192.168.1.10", success: true, timestamp: new Date("2024-01-15T09:00:00Z") },
  { event_type: "login", user: "jdoe", ip: "192.168.1.25", success: true, timestamp: new Date("2024-01-15T09:05:00Z") },
  { event_type: "file_upload", user: "jdoe", filename: "report_q4.pdf", size_bytes: 2048576, timestamp: new Date("2024-01-15T09:10:00Z") },
  { event_type: "login", user: "unknown", ip: "10.0.0.55", success: false, timestamp: new Date("2024-01-15T09:15:00Z") },
  { event_type: "config_change", user: "admin", setting: "max_connections", old_value: 100, new_value: 200, timestamp: new Date("2024-01-15T09:20:00Z") },
  { event_type: "logout", user: "jdoe", timestamp: new Date("2024-01-15T17:00:00Z") },
  { event_type: "backup", user: "system", status: "completed", duration_seconds: 342, timestamp: new Date("2024-01-16T02:00:00Z") },
  { event_type: "login", user: "admin", ip: "192.168.1.10", success: true, timestamp: new Date("2024-01-16T08:00:00Z") },
  { event_type: "alert", user: "system", severity: "warning", message: "Disk usage above 80%", timestamp: new Date("2024-01-16T10:30:00Z") },
  { event_type: "login", user: "msmith", ip: "192.168.1.42", success: true, timestamp: new Date("2024-01-16T11:00:00Z") }
]);
