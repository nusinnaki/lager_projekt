PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS workers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_source TEXT NOT NULL,
  product_name TEXT NOT NULL,
  internal_id TEXT NOT NULL UNIQUE,
  qr_code TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS stock (
  product_id INTEGER PRIMARY KEY,
  quantity INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  action TEXT NOT NULL CHECK(action IN ('TAKE','LOAD')),
  worker_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL CHECK(quantity > 0),
  delta INTEGER NOT NULL,
  FOREIGN KEY(worker_id) REFERENCES workers(id),
  FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE INDEX IF NOT EXISTS idx_logs_ts ON logs(ts);
CREATE INDEX IF NOT EXISTS idx_logs_worker ON logs(worker_id);
CREATE INDEX IF NOT EXISTS idx_logs_product ON logs(product_id);
