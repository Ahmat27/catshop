"""
CatShop – Flask Backend
Menggunakan SQLite (gratis, tanpa server database)
"""

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import sqlite3, os, datetime, time

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'catshop_secret_2025'
CORS(app, supports_credentials=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'catshop.db')

# ── DATABASE CONNECTION ──────────────────────────────────────
def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

# ── INISIALISASI DATABASE ────────────────────────────────────
def init_db():
    con = get_db()
    cur = con.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        nama     TEXT NOT NULL,
        role     TEXT NOT NULL DEFAULT 'Pengguna'
    );

    CREATE TABLE IF NOT EXISTS produk (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        nama     TEXT NOT NULL,
        kategori TEXT NOT NULL,
        harga    INTEGER NOT NULL DEFAULT 0,
        stok     INTEGER NOT NULL DEFAULT 0,
        terjual  INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS customer (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        nama    TEXT NOT NULL,
        hp      TEXT NOT NULL,
        email   TEXT NOT NULL,
        alamat  TEXT,
        tipe    TEXT NOT NULL DEFAULT 'Baru',
        joined  TEXT NOT NULL,
        pesanan INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS pesanan (
        id       TEXT PRIMARY KEY,
        customer TEXT NOT NULL,
        produk   TEXT NOT NULL,
        qty      INTEGER NOT NULL DEFAULT 1,
        total    INTEGER NOT NULL DEFAULT 0,
        status   TEXT NOT NULL DEFAULT 'Menunggu',
        tanggal  TEXT NOT NULL
    );
    """)

    # Insert default data jika belum ada
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.executescript("""
        INSERT INTO users (username,password,nama,role) VALUES
            ('admin','12345','Ahmat Hidayat','Admin'),
            ('user','12345','Pelanggan','Pengguna');

        INSERT INTO produk (nama,kategori,harga,stok,terjual) VALUES
            ('Makanan Premium','Makanan',120000,25,130),
            ('Pasir Kucing Gumpal','Pasir',50000,40,90),
            ('Mainan Bola','Mainan',25000,30,70),
            ('Kalung Kucing','Aksesoris',35000,8,45),
            ('Kandang Lipat','Kandang',250000,5,20),
            ('Vitamin Kucing','Kesehatan',80000,15,55);

        INSERT INTO customer (nama,hp,email,alamat,tipe,joined,pesanan) VALUES
            ('Nadia Rahayu','081234567890','nadia@email.com','Jl. Melati No.5, Jakarta','VIP','2024-11-10',8),
            ('Rian Pratama','082198765432','rian@email.com','Jl. Mawar No.3, Bandung','Reguler','2025-01-15',4),
            ('Putri Cantika','085678901234','putri@email.com','Jl. Anggrek No.12, Surabaya','Reguler','2025-02-20',3),
            ('Budi Santoso','087712345678','budi@email.com','Jl. Dahlia No.7, Yogyakarta','Baru','2025-05-01',1),
            ('Siti Aminah','089912348765','siti@email.com','Jl. Kenanga No.9, Malang','VIP','2024-09-05',12),
            ('Dodi Firmansyah','081387654321','dodi@email.com','Jl. Cempaka No.2, Semarang','Baru','2025-05-10',1);

        INSERT INTO pesanan (id,customer,produk,qty,total,status,tanggal) VALUES
            ('ORD001','Nadia','Makanan Kucing Premium',2,240000,'Selesai','2025-05-20'),
            ('ORD002','Rian','Pasir Kucing Gumpal',1,50000,'Dikirim','2025-05-22'),
            ('ORD003','Putri','Mainan Bola',3,75000,'Menunggu','2025-05-25'),
            ('ORD004','Budi','Vitamin Kucing',1,80000,'Diproses','2025-05-26'),
            ('ORD005','Siti','Kalung Kucing',2,70000,'Selesai','2025-05-18');
        """)

    con.commit()
    con.close()

init_db()

# ── HELPER ──────────────────────────────────────────────────
def resp(data=None, msg='OK', code=200):
    return jsonify({'status': 'ok' if code < 400 else 'error',
                    'message': msg, 'data': data}), code

def auth_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return resp(msg='Belum login', code=401)
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return resp(msg='Belum login', code=401)
        if session.get('role') != 'Admin':
            return resp(msg='Akses ditolak – hanya Admin', code=403)
        return fn(*args, **kwargs)
    return wrapper

# ════════════════════════════════════════════════════════════
#  SERVE HTML FILES
# ════════════════════════════════════════════════════════════
@app.route('/')
def index():
    return send_from_directory('templates', 'login.html')

@app.route('/<path:filename>')
def serve_html(filename):
    tpl_path = os.path.join(app.template_folder, filename)
    if os.path.exists(tpl_path):
        return send_from_directory('templates', filename)
    return send_from_directory('static', filename)

# ════════════════════════════════════════════════════════════
#  AUTH
# ════════════════════════════════════════════════════════════
@app.route('/api/login', methods=['POST'])
def login():
    data     = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    role_req = data.get('role', '').strip()

    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cur.fetchone()
    con.close()

    if not user:
        return resp(msg='Username atau password salah!', code=401)

    role_map = {'admin': 'Admin', 'pengguna': 'Pengguna'}
    if role_map.get(role_req) != user['role']:
        return resp(msg='Role tidak sesuai!', code=401)

    session['user_id'] = user['id']
    session['nama']    = user['nama']
    session['role']    = user['role']

    return resp({'namaUser': user['nama'], 'roleUser': user['role']})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return resp(msg='Logout berhasil')


@app.route('/api/me')
def me():
    if 'user_id' not in session:
        return resp(msg='Belum login', code=401)
    return resp({'namaUser': session['nama'], 'roleUser': session['role']})


# ════════════════════════════════════════════════════════════
#  DASHBOARD STATS
# ════════════════════════════════════════════════════════════
@app.route('/api/dashboard')
@auth_required
def dashboard():
    con = get_db()
    cur = con.cursor()
    jml_produk  = cur.execute("SELECT COUNT(*) FROM produk").fetchone()[0]
    jml_pesanan = cur.execute("SELECT COUNT(*) FROM pesanan").fetchone()[0]
    jml_cust    = cur.execute("SELECT COUNT(*) FROM customer").fetchone()[0]
    omzet       = cur.execute("SELECT IFNULL(SUM(total),0) FROM pesanan WHERE status='Selesai'").fetchone()[0]
    recent      = [dict(r) for r in cur.execute("SELECT customer,produk,total FROM pesanan ORDER BY tanggal DESC LIMIT 3").fetchall()]
    terlaris    = [dict(r) for r in cur.execute("SELECT nama,stok,terjual FROM produk ORDER BY terjual DESC LIMIT 3").fetchall()]
    con.close()
    return resp({
        'produk': jml_produk,
        'pesanan': jml_pesanan,
        'customer': jml_cust,
        'omzet': omzet,
        'pesananMasuk': recent,
        'produkTerlaris': terlaris
    })


# ════════════════════════════════════════════════════════════
#  PRODUK
# ════════════════════════════════════════════════════════════
@app.route('/api/produk', methods=['GET'])
@auth_required
def get_produk():
    q   = request.args.get('q', '')
    kat = request.args.get('kategori', '')
    con = get_db()
    cur = con.cursor()
    sql = "SELECT * FROM produk WHERE nama LIKE ?"
    params = [f'%{q}%']
    if kat:
        sql += " AND kategori=?"
        params.append(kat)
    rows = [dict(r) for r in cur.execute(sql, params).fetchall()]
    con.close()
    return resp(rows)


@app.route('/api/produk', methods=['POST'])
@admin_required
def add_produk():
    d = request.get_json()
    nama     = d.get('nama','').strip()
    kategori = d.get('kategori','')
    harga    = int(d.get('harga', 0))
    stok     = int(d.get('stok', 0))
    if not nama or harga < 0 or stok < 0:
        return resp(msg='Data tidak lengkap', code=400)
    con = get_db()
    cur = con.cursor()
    cur.execute("INSERT INTO produk (nama,kategori,harga,stok,terjual) VALUES (?,?,?,?,0)",
                (nama, kategori, harga, stok))
    con.commit()
    new_id = cur.lastrowid
    con.close()
    return resp({'id': new_id}, msg='Produk ditambahkan', code=201)


@app.route('/api/produk/<int:pid>', methods=['PUT'])
@admin_required
def update_produk(pid):
    d = request.get_json()
    con = get_db()
    con.execute("UPDATE produk SET nama=?,kategori=?,harga=?,stok=? WHERE id=?",
                (d['nama'], d['kategori'], int(d['harga']), int(d['stok']), pid))
    con.commit()
    con.close()
    return resp(msg='Produk diperbarui')


@app.route('/api/produk/<int:pid>', methods=['DELETE'])
@admin_required
def delete_produk(pid):
    con = get_db()
    con.execute("DELETE FROM produk WHERE id=?", (pid,))
    con.commit()
    con.close()
    return resp(msg='Produk dihapus')


# ════════════════════════════════════════════════════════════
#  PESANAN
# ════════════════════════════════════════════════════════════
@app.route('/api/pesanan', methods=['GET'])
@admin_required
def get_pesanan():
    q  = request.args.get('q', '')
    st = request.args.get('status', '')
    con = get_db()
    sql = "SELECT * FROM pesanan WHERE (customer LIKE ? OR produk LIKE ?)"
    params = [f'%{q}%', f'%{q}%']
    if st:
        sql += " AND status=?"
        params.append(st)
    sql += " ORDER BY tanggal DESC"
    rows = [dict(r) for r in con.execute(sql, params).fetchall()]
    con.close()
    return resp(rows)


@app.route('/api/pesanan', methods=['POST'])
@admin_required
def add_pesanan():
    d        = request.get_json()
    customer = d.get('customer','').strip()
    produk   = d.get('produk','').strip()
    qty      = int(d.get('qty', 1))
    total    = int(d.get('total', 0))
    status   = d.get('status','Menunggu')
    if not customer or not produk:
        return resp(msg='Data tidak lengkap', code=400)
    today  = datetime.date.today().isoformat()
    new_id = 'ORD' + str(int(time.time() * 1000))[-6:]
    con = get_db()
    con.execute("INSERT INTO pesanan (id,customer,produk,qty,total,status,tanggal) VALUES (?,?,?,?,?,?,?)",
                (new_id, customer, produk, qty, total, status, today))
    con.commit()
    con.close()
    return resp({'id': new_id}, msg='Pesanan ditambahkan', code=201)


@app.route('/api/pesanan/<string:pid>', methods=['PUT'])
@admin_required
def update_pesanan(pid):
    d = request.get_json()
    con = get_db()
    con.execute("UPDATE pesanan SET customer=?,produk=?,qty=?,total=?,status=? WHERE id=?",
                (d['customer'], d['produk'], int(d['qty']), int(d['total']), d['status'], pid))
    con.commit()
    con.close()
    return resp(msg='Pesanan diperbarui')


@app.route('/api/pesanan/<string:pid>', methods=['DELETE'])
@admin_required
def delete_pesanan(pid):
    con = get_db()
    con.execute("DELETE FROM pesanan WHERE id=?", (pid,))
    con.commit()
    con.close()
    return resp(msg='Pesanan dihapus')


# ════════════════════════════════════════════════════════════
#  CUSTOMER
# ════════════════════════════════════════════════════════════
@app.route('/api/customer', methods=['GET'])
@admin_required
def get_customer():
    q    = request.args.get('q', '')
    tipe = request.args.get('tipe', '')
    con  = get_db()
    sql  = "SELECT * FROM customer WHERE (nama LIKE ? OR email LIKE ?)"
    params = [f'%{q}%', f'%{q}%']
    if tipe:
        sql += " AND tipe=?"
        params.append(tipe)
    rows = [dict(r) for r in con.execute(sql, params).fetchall()]
    con.close()
    return resp(rows)


@app.route('/api/customer', methods=['POST'])
@admin_required
def add_customer():
    d      = request.get_json()
    nama   = d.get('nama','').strip()
    hp     = d.get('hp','').strip()
    email  = d.get('email','').strip()
    alamat = d.get('alamat','').strip()
    tipe   = d.get('tipe','Baru')
    if not nama or not hp or not email:
        return resp(msg='Nama, HP, dan email wajib diisi', code=400)
    today = datetime.date.today().isoformat()
    con = get_db()
    cur = con.cursor()
    cur.execute("INSERT INTO customer (nama,hp,email,alamat,tipe,joined,pesanan) VALUES (?,?,?,?,?,?,0)",
                (nama, hp, email, alamat, tipe, today))
    con.commit()
    new_id = cur.lastrowid
    con.close()
    return resp({'id': new_id}, msg='Customer ditambahkan', code=201)


@app.route('/api/customer/<int:cid>', methods=['PUT'])
@admin_required
def update_customer(cid):
    d = request.get_json()
    con = get_db()
    con.execute("UPDATE customer SET nama=?,hp=?,email=?,alamat=?,tipe=? WHERE id=?",
                (d['nama'], d['hp'], d['email'], d.get('alamat',''), d['tipe'], cid))
    con.commit()
    con.close()
    return resp(msg='Customer diperbarui')


@app.route('/api/customer/<int:cid>', methods=['DELETE'])
@admin_required
def delete_customer(cid):
    con = get_db()
    con.execute("DELETE FROM customer WHERE id=?", (cid,))
    con.commit()
    con.close()
    return resp(msg='Customer dihapus')


# ════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))