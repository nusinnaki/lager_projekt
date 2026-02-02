PRAGMA foreign_keys = ON;

-- 1 = Konstanz, 2 = Sindelfingen
CREATE TABLE IF NOT EXISTS lagers (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS workers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,     -- later: QR is just this integer
  nc_nummer TEXT NOT NULL UNIQUE,           -- NC_Nummer
  materialkurztext TEXT NOT NULL,           -- Materialkurztext
  active INTEGER NOT NULL DEFAULT 1
);

-- stock is per lager + product
CREATE TABLE IF NOT EXISTS stock (
  lager_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (lager_id, product_id),
  FOREIGN KEY(lager_id) REFERENCES lagers(id),
  FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL DEFAULT (datetime('now')),
  action TEXT NOT NULL CHECK(action IN ('take','load')),
  lager_id INTEGER NOT NULL,
  worker_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL CHECK(quantity > 0),
  note TEXT,
  FOREIGN KEY(lager_id) REFERENCES lagers(id),
  FOREIGN KEY(worker_id) REFERENCES workers(id),
  FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE INDEX IF NOT EXISTS idx_logs_ts ON logs(ts);
CREATE INDEX IF NOT EXISTS idx_logs_worker ON logs(worker_id);
CREATE INDEX IF NOT EXISTS idx_logs_product ON logs(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_product ON stock(product_id);
