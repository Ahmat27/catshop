-- ============================================================
--  CatShop Database – jalankan di phpMyAdmin atau MySQL CLI
-- ============================================================

CREATE DATABASE IF NOT EXISTS catshop CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE catshop_db;

-- ── USERS (untuk login) ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id       INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50)  NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,        -- disimpan plain sesuai aslinya (12345)
  nama     VARCHAR(100) NOT NULL,
  role     ENUM('Admin','Pengguna') NOT NULL DEFAULT 'Pengguna'
) ENGINE=InnoDB;

INSERT INTO users (username, password, nama, role) VALUES
  ('admin', '12345', 'Ahmat Hidayat', 'Admin'),
  ('user',  '12345', 'Pelanggan',     'Pengguna')
ON DUPLICATE KEY UPDATE username=username;

-- ── PRODUK ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS produk (
  id        INT AUTO_INCREMENT PRIMARY KEY,
  nama      VARCHAR(150) NOT NULL,
  kategori  ENUM('Makanan','Pasir','Mainan','Aksesoris','Kandang','Kesehatan') NOT NULL,
  harga     INT          NOT NULL DEFAULT 0,
  stok      INT          NOT NULL DEFAULT 0,
  terjual   INT          NOT NULL DEFAULT 0
) ENGINE=InnoDB;

INSERT INTO produk (nama, kategori, harga, stok, terjual) VALUES
  ('Makanan Premium',      'Makanan',   120000, 25, 130),
  ('Pasir Kucing Gumpal',  'Pasir',      50000, 40,  90),
  ('Mainan Bola',          'Mainan',     25000, 30,  70),
  ('Kalung Kucing',        'Aksesoris',  35000,  8,  45),
  ('Kandang Lipat',        'Kandang',   250000,  5,  20),
  ('Vitamin Kucing',       'Kesehatan',  80000, 15,  55)
ON DUPLICATE KEY UPDATE nama=nama;

-- ── CUSTOMER ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customer (
  id      INT AUTO_INCREMENT PRIMARY KEY,
  nama    VARCHAR(100) NOT NULL,
  hp      VARCHAR(20)  NOT NULL,
  email   VARCHAR(100) NOT NULL,
  alamat  TEXT,
  tipe    ENUM('VIP','Reguler','Baru') NOT NULL DEFAULT 'Baru',
  joined  DATE         NOT NULL,
  pesanan INT          NOT NULL DEFAULT 0
) ENGINE=InnoDB;

INSERT INTO customer (nama, hp, email, alamat, tipe, joined, pesanan) VALUES
  ('Nadia Rahayu',    '081234567890', 'nadia@email.com', 'Jl. Melati No.5, Jakarta',    'VIP',     '2024-11-10', 8),
  ('Rian Pratama',    '082198765432', 'rian@email.com',  'Jl. Mawar No.3, Bandung',     'Reguler', '2025-01-15', 4),
  ('Putri Cantika',   '085678901234', 'putri@email.com', 'Jl. Anggrek No.12, Surabaya', 'Reguler', '2025-02-20', 3),
  ('Budi Santoso',    '087712345678', 'budi@email.com',  'Jl. Dahlia No.7, Yogyakarta', 'Baru',    '2025-05-01', 1),
  ('Siti Aminah',     '089912348765', 'siti@email.com',  'Jl. Kenanga No.9, Malang',    'VIP',     '2024-09-05', 12),
  ('Dodi Firmansyah', '081387654321', 'dodi@email.com',  'Jl. Cempaka No.2, Semarang',  'Baru',    '2025-05-10', 1)
ON DUPLICATE KEY UPDATE nama=nama;

-- ── PESANAN ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pesanan (
  id       VARCHAR(20)  PRIMARY KEY,
  customer VARCHAR(100) NOT NULL,
  produk   VARCHAR(150) NOT NULL,
  qty      INT          NOT NULL DEFAULT 1,
  total    INT          NOT NULL DEFAULT 0,
  status   ENUM('Menunggu','Diproses','Dikirim','Selesai','Dibatalkan') NOT NULL DEFAULT 'Menunggu',
  tanggal  DATE         NOT NULL
) ENGINE=InnoDB;

INSERT INTO pesanan (id, customer, produk, qty, total, status, tanggal) VALUES
  ('ORD001', 'Nadia',  'Makanan Kucing Premium', 2, 240000, 'Selesai',  '2025-05-20'),
  ('ORD002', 'Rian',   'Pasir Kucing Gumpal',    1,  50000, 'Dikirim',  '2025-05-22'),
  ('ORD003', 'Putri',  'Mainan Bola',             3,  75000, 'Menunggu', '2025-05-25'),
  ('ORD004', 'Budi',   'Vitamin Kucing',          1,  80000, 'Diproses', '2025-05-26'),
  ('ORD005', 'Siti',   'Kalung Kucing',           2,  70000, 'Selesai',  '2025-05-18')
ON DUPLICATE KEY UPDATE id=id;