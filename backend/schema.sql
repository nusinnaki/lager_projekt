PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sites (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1))
);

CREATE TABLE IF NOT EXISTS locations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  site_id INTEGER NOT NULL,
  shelf INTEGER NOT NULL,
  row INTEGER NOT NULL,
  active INTEGER NOT NULL DEF-AULT 1 CHECK (active IN (0,1)),
  UNIQUE (site_id, shelf, row),
  FOREIGN KEY (site_id) REFERENCES sites(id)
);

CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_category_name_ci
ON categories(lower(trim(name)));

CREATE TABLE IF NOT EXISTS brands (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_brand_name_ci
ON brands(lower(trim(name)));

CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category_id INTEGER NOT NULL,
  brand_id INTEGER NOT NULL,
  product_name TEXT NOT NULL,
  nc_nummer TEXT UNIQUE,
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
  FOREIGN KEY (category_id) REFERENCES categories(id),
  FOREIGN KEY (brand_id) REFERENCES brands(id)
);

CREATE TABLE IF NOT EXISTS product_site_locations (
  site_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  location_id INTEGER NOT NULL,
  PRIMARY KEY (site_id, product_id),
  FOREIGN KEY (site_id) REFERENCES sites(id),
  FOREIGN KEY (product_id) REFERENCES products(id),
  FOREIGN KEY (location_id) REFERENCES locations(id)
);

CREATE TABLE IF NOT EXISTS workers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT,
  auth_provider TEXT NOT NULL DEFAULT 'local',
  ldap_dn TEXT,
  is_admin INTEGER NOT NULL DEFAULT 0 CHECK (is_admin IN (0,1)),
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (first_name, last_name)
);

CREATE TABLE IF NOT EXISTS stock (
  location_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (location_id, product_id),
  FOREIGN KEY (location_id) REFERENCES locations(id),
  FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  action TEXT NOT NULL,
  location_id INTEGER NOT NULL,
  worker_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  timestamp TEXT NOT NULL,
  FOREIGN KEY (location_id) REFERENCES locations(id),
  FOREIGN KEY (worker_id) REFERENCES workers(id),
  FOREIGN KEY (product_id) REFERENCES products(id)
);