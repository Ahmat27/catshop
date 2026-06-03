"""
CatShop – Flask Backend
Menghubungkan HTML frontend ke MySQL (Railway)

Cara jalankan:
  pip install flask flask-mysqldb flask-cors
  python app.py
"""

from flask import Flask, request, jsonify, session, send_from_directory
from flask_mysqldb import MySQL
from flask_cors import CORS
import os, datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'catshop_secret_2025'
CORS(app, supports_credentials=True)

# ── KONFIGURASI MySQL (Railway) ────────────────────────────────
app.config['MYSQL_HOST']        = os.environ.get('MYSQLHOST', 'localhost')
app.config['MYSQL_USER']        = os.environ.get('MYSQLUSER', 'root')
app.config['MYSQL_PASSWORD']    = os.environ.get('MYSQLPASSWORD', '')
app.config['MYSQL_DB']          = os.environ.get('MYSQLDATABASE', 'catshop_db')
app.config['MYSQL_PORT']        = int(os.environ.get('MYSQLPORT', 3306))
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# ── HELPER ──────────────────────────────────────────────────
def resp(data=None, msg='OK', code=200):
    return jsonify({'status': 'ok' if code < 400 else 'error',
                    'message': msg, 'data': data}), code

def auth_required(fn):
    """Decorator: cek session login"""
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return resp(msg='Belum login', code=401)
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    """Decorator: cek role Admin"""
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
    # Coba templates dulu, lalu static
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
    role_req = data.get('role', '').strip()   # 'admin' atau 'pengguna'

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    user = cur.fetchone()
    cur.close()

    if not user:
        return resp(msg='Username atau password salah!', code=401)

    # Cocokkan role yang dipilih di form dengan role di DB
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
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) AS total FROM produk");  jml_produk = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) AS total FROM pesanan"); jml_pesanan = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) AS total FROM customer");jml_cust = cur.fetchone()['total']
    cur.execute("SELECT IFNULL(SUM(total),0) AS omzet FROM pesanan WHERE status='Selesai'")
    omzet = cur.fetchone()['omzet']
    cur.execute("SELECT customer,produk,total FROM pesanan ORDER BY tanggal DESC LIMIT 3")
    recent = cur.fetchall()
    cur.execute("SELECT nama,stok,terjual FROM produk ORDER BY terjual DESC LIMIT 3")
    terlaris = cur.fetchall()
    cur.close()
    return resp({
        'produk': jml_produk,
        'pesanan': jml_pesanan,
        'customer': jml_cust,
        'omzet': omzet,
        'pesananMasuk': list(recent),
        'produkTerlaris': list(terlaris)
    })


# ════════════════════════════════════════════════════════════
#  PRODUK  (Admin: CRUD | Pengguna: GET only)
# ════════════════════════════════════════════════════════════
@app.route('/api/produk', methods=['GET'])
@auth_required
def get_produk():
    q   = request.args.get('q', '')
    kat = request.args.get('kategori', '')
    cur = mysql.connection.cursor()
    sql = "SELECT * FROM produk WHERE nama LIKE %s"
    params = [f'%{q}%']
    if kat:
        sql += " AND kategori=%s"
        params.append(kat)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return resp(list(rows))


@app.route('/api/produk', methods=['POST'])
@admin_required
def add_produk():
    d = request.get_json()
    nama    = d.get('nama','').strip()
    kategori= d.get('kategori','')
    harga   = int(d.get('harga', 0))
    stok    = int(d.get('stok', 0))
    if not nama or harga < 0 or stok < 0:
        return resp(msg='Data tidak lengkap', code=400)
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO produk (nama,kategori,harga,stok,terjual) VALUES (%s,%s,%s,%s,0)",
                (nama, kategori, harga, stok))
    mysql.connection.commit()
    new_id = cur.lastrowid
    cur.close()
    return resp({'id': new_id}, msg='Produk ditambahkan', code=201)


@app.route('/api/produk/<int:pid>', methods=['PUT'])
@admin_required
def update_produk(pid):
    d = request.get_json()
    cur = mysql.connection.cursor()
    cur.execute("""UPDATE produk SET nama=%s,kategori=%s,harga=%s,stok=%s
                   WHERE id=%s""",
                (d['nama'], d['kategori'], int(d['harga']), int(d['stok']), pid))
    mysql.connection.commit()
    cur.close()
    return resp(msg='Produk diperbarui')


@app.route('/api/produk/<int:pid>', methods=['DELETE'])
@admin_required
def delete_produk(pid):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM produk WHERE id=%s", (pid,))
    mysql.connection.commit()
    cur.close()
    return resp(msg='Produk dihapus')


# ════════════════════════════════════════════════════════════
#  PESANAN  (Admin only untuk CUD)
# ════════════════════════════════════════════════════════════
@app.route('/api/pesanan', methods=['GET'])
@admin_required
def get_pesanan():
    q  = request.args.get('q', '')
    st = request.args.get('status', '')
    cur = mysql.connection.cursor()
    sql = "SELECT * FROM pesanan WHERE (customer LIKE %s OR produk LIKE %s)"
    params = [f'%{q}%', f'%{q}%']
    if st:
        sql += " AND status=%s"
        params.append(st)
    sql += " ORDER BY tanggal DESC"
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    # Konversi date ke string agar JSON-serializable
    for r in rows:
        if isinstance(r.get('tanggal'), datetime.date):
            r['tanggal'] = r['tanggal'].isoformat()
    return resp(list(rows))


@app.route('/api/pesanan', methods=['POST'])
@admin_required
def add_pesanan():
    d = request.get_json()
    customer = d.get('customer','').strip()
    produk   = d.get('produk','').strip()
    qty      = int(d.get('qty', 1))
    total    = int(d.get('total', 0))
    status   = d.get('status','Menunggu')
    if not customer or not produk:
        return resp(msg='Data tidak lengkap', code=400)
    today = datetime.date.today().isoformat()
    import time
    new_id = 'ORD' + str(int(time.time() * 1000))[-6:]
    cur = mysql.connection.cursor()
    cur.execute("""INSERT INTO pesanan (id,customer,produk,qty,total,status,tanggal)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (new_id, customer, produk, qty, total, status, today))
    mysql.connection.commit()
    cur.close()
    return resp({'id': new_id}, msg='Pesanan ditambahkan', code=201)


@app.route('/api/pesanan/<string:pid>', methods=['PUT'])
@admin_required
def update_pesanan(pid):
    d = request.get_json()
    cur = mysql.connection.cursor()
    cur.execute("""UPDATE pesanan SET customer=%s,produk=%s,qty=%s,total=%s,status=%s
                   WHERE id=%s""",
                (d['customer'], d['produk'], int(d['qty']), int(d['total']), d['status'], pid))
    mysql.connection.commit()
    cur.close()
    return resp(msg='Pesanan diperbarui')


@app.route('/api/pesanan/<string:pid>', methods=['DELETE'])
@admin_required
def delete_pesanan(pid):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM pesanan WHERE id=%s", (pid,))
    mysql.connection.commit()
    cur.close()
    return resp(msg='Pesanan dihapus')


# ════════════════════════════════════════════════════════════
#  CUSTOMER  (Admin only untuk CUD)
# ════════════════════════════════════════════════════════════
@app.route('/api/customer', methods=['GET'])
@admin_required
def get_customer():
    q    = request.args.get('q', '')
    tipe = request.args.get('tipe', '')
    cur  = mysql.connection.cursor()
    sql  = "SELECT * FROM customer WHERE (nama LIKE %s OR email LIKE %s)"
    params = [f'%{q}%', f'%{q}%']
    if tipe:
        sql += " AND tipe=%s"
        params.append(tipe)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    for r in rows:
        if isinstance(r.get('joined'), datetime.date):
            r['joined'] = r['joined'].isoformat()
    return resp(list(rows))


@app.route('/api/customer', methods=['POST'])
@admin_required
def add_customer():
    d = request.get_json()
    nama   = d.get('nama','').strip()
    hp     = d.get('hp','').strip()
    email  = d.get('email','').strip()
    alamat = d.get('alamat','').strip()
    tipe   = d.get('tipe','Baru')
    if not nama or not hp or not email:
        return resp(msg='Nama, HP, dan email wajib diisi', code=400)
    today = datetime.date.today().isoformat()
    cur = mysql.connection.cursor()
    cur.execute("""INSERT INTO customer (nama,hp,email,alamat,tipe,joined,pesanan)
                   VALUES (%s,%s,%s,%s,%s,%s,0)""",
                (nama, hp, email, alamat, tipe, today))
    mysql.connection.commit()
    new_id = cur.lastrowid
    cur.close()
    return resp({'id': new_id}, msg='Customer ditambahkan', code=201)


@app.route('/api/customer/<int:cid>', methods=['PUT'])
@admin_required
def update_customer(cid):
    d = request.get_json()
    cur = mysql.connection.cursor()
    cur.execute("""UPDATE customer SET nama=%s,hp=%s,email=%s,alamat=%s,tipe=%s
                   WHERE id=%s""",
                (d['nama'], d['hp'], d['email'], d.get('alamat',''), d['tipe'], cid))
    mysql.connection.commit()
    cur.close()
    return resp(msg='Customer diperbarui')


@app.route('/api/customer/<int:cid>', methods=['DELETE'])
@admin_required
def delete_customer(cid):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM customer WHERE id=%s", (cid,))
    mysql.connection.commit()
    cur.close()
    return resp(msg='Customer dihapus')


# ════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))