# OLT Telegram Monitor

Aplikasi Telegram Bot sederhana, stabil, dan *production-ready* untuk melakukan pengawasan (monitoring) kondisi ONT/ONU pada OLT melalui protokol **SNMP (Simple Network Management Protocol)**.

---

## 1. Deskripsi Aplikasi

**OLT Telegram Monitor** dibuat untuk membantu teknisi dan administrator jaringan memantau kondisi pelanggan/ONT tanpa harus melakukan login langsung ke CLI atau Web Management OLT. 

Aplikasi ini berjalan secara *asynchronous* menggunakan bahasa pemrograman Python 3 dan pustaka `python-telegram-bot` serta `pysnmp`. Seluruh konfigurasi (seperti token Telegram, IP OLT, SNMP community string, threshold redaman, dan MIB OID) dikelola secara fleksibel melalui file `.env`.

---

## 2. Fitur Utama

- 🔴 **` /cek_putus`**: Memeriksa dan menampilkan daftar ONT yang sedang berstatus **OFFLINE** (putus), dikelompokkan berdasarkan PON & Slot.
- ⚠️ **` /cek_redaman`**: Memeriksa dan menampilkan ONT yang memiliki nilai **RX Optical Power** melampaui batas (*threshold*) yang ditentukan pada `.env`.
- 📡 **` /status`**: Memeriksa status konektivitas SNMP dari server monitoring ke OLT beserta waktu respons (*latency*).
- 🔒 **Sistem Keamanan Akses (Access Control)**: Membatasi pengunaan bot hanya untuk Telegram Chat ID yang terdaftar pada `TELEGRAM_ALLOWED_CHAT_IDS`.
- 📄 **Auto Pagination**: Memecah pesan Telegram secara otomatis jika jumlah data ONT yang dikembalikan sangat banyak, mencegah terjadinya *error* karena *message length limit* Telegram (4096 karakter).
- 🐧 **Systemd Integration**: Siap dijalankan sebagai *service Linux systemd* dengan fitur *auto-restart* jika proses terhenti.

---

## 3. Arsitektur Aplikasi

```text
Operator / Administrator (Telegram App)
                │
                ▼
      [ Telegram Bot Server ]
                │
        (python-telegram-bot)
                │
                ▼
       [ App Core Engine ]
    ├── Config Manager (.env)
    ├── Security / Chat ID Filter
    ├── OLT Monitor Logic
    └── OID & Signal Parser
                │
            (pysnmp)
                │
                ▼
        [ SNMP Protocol ]
                │
                ▼
         [ OLT Hardware ]
   (ZTE / Huawei / Fiberhome / VSOL / dll)
```

---

## 4. Requirements System

- **OS**: Ubuntu Linux 20.04 / 22.04 / 24.04 LTS (atau STB Linux Armbian)
- **Python**: Python 3.9+
- **Network**: Akses koneksi UDP Port 161 dari server monitor ke IP OLT

---

## 5. Persiapan Telegram Bot

1. Buka aplikasi Telegram dan cari **@BotFather**.
2. Kirim perintah `/newbot` dan ikuti petunjuk hingga selesai.
3. Simpan **HTTP API Token** yang diberikan (contoh: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).
4. Cari **@userinfobot** atau **@raw_data_bot** di Telegram untuk mendapatkan **Chat ID** akun Telegram Anda.

---

## 6. Persiapan SNMP OLT

1. Login ke OLT Anda (via Telnet/SSH/Web).
2. Pastikan fitur **SNMP Server / Agent** telah diaktifkan.
3. Konfigurasikan **Read-Only (RO) Community String** (contoh: `public` atau `mysecretro`).
4. Pastikan firewall OLT mengizinkan query SNMP (UDP 161) dari IP server monitoring Anda.

---

## 7. Cara Mendapatkan OID MIB OLT

Setiap vendor OLT (ZTE, Huawei, Fiberhome, VSOL, HSAN, Cdata, dll.) memiliki struktur OID MIB yang berbeda. Untuk mendapatkan OID yang sesuai:

1. Unduh file MIB resmi dari vendor OLT Anda.
2. Gunakan aplikasi MIB Browser (seperti Paessler MIB Viewer atau iReasoning MIB Browser).
3. Atau lakukan *snmpwalk* terhadap MIB tree umum untuk mencari OID ONT Status dan Optical Power:
   ```bash
   snmpwalk -v2c -c public 192.168.88.2 1.3.6.1.4.1
   ```

---

## 8. Instalasi di Ubuntu

### 8.1 Update Package Manager
```bash
sudo apt update && sudo apt upgrade -y
```

### 8.2 Install Dependencies Python & SNMP Tools
```bash
sudo apt install -y python3 python3-venv python3-pip snmp
```

### 8.3 Buat Direktori Aplikasi
```bash
sudo mkdir -p /opt/olt-monitor
sudo chown -R $USER:$USER /opt/olt-monitor
cd /opt/olt-monitor
```

---

## 9. Virtual Environment Setup

```bash
cd /opt/olt-monitor
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 10. Konfigurasi `.env`

Salin file `.env.example` menjadi `.env`:

```bash
cp .env.example .env
nano .env
```

Isi konfigurasi sesuai lingkungan jaringan Anda:

```env
TELEGRAM_BOT_TOKEN=123456789:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_ALLOWED_CHAT_IDS=123456789,987654321

OLT_NAME=OLT-UTAMA
OLT_HOST=192.168.88.2
OLT_PORT=161

OLT_SNMP_VERSION=2c
OLT_SNMP_COMMUNITY=public

SNMP_TIMEOUT=5
SNMP_RETRIES=2

OLT_RX_POWER_THRESHOLD=-25
OLT_RX_POWER_SCALE=100

# Konfigurasi OID HSGQ Private MIB (50224)
OID_ONT_STATUS=1.3.6.1.4.1.50224.3.3.2.1.8
OID_ONT_RX_POWER=1.3.6.1.4.1.50224.3.3.3.1.4
OID_ONT_TX_POWER=1.3.6.1.4.1.50224.3.3.3.1.5
OID_ONT_VENDOR=1.3.6.1.4.1.50224.3.3.2.1.25
OID_ONT_MODEL=1.3.6.1.4.1.50224.3.3.2.1.26
OID_ONT_NAME=1.3.6.1.4.1.50224.3.3.2.1.2

ONT_STATUS_ONLINE_VALUES=1
ONT_STATUS_OFFLINE_VALUES=2

LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

---

## 11. Testing SNMP dari Server

Sebelum menjalankan bot, lakukan pengujian koneksi SNMP menggunakan perintah bawaan Ubuntu:

```bash
snmpwalk -v2c -c public 192.168.88.2 1.3.6.1.4.1.3902.1012.3.28.1.1.3
```

Jika perintah tersebut menampilkan daftar OID dan nilai status ONT, maka jaringan dan konfigurasi SNMP OLT sudah siap.

---

## 12. Menjalankan Aplikasi secara Manual

```bash
cd /opt/olt-monitor
source venv/bin/activate
python -m app.main
```

Output log ketika berhasil:
```text
2026-10-03 00:50:00 INFO Starting OLT Telegram Monitor v1.0.0...
2026-10-03 00:50:00 INFO Target OLT: OLT-UTAMA (192.168.88.2:161)
2026-10-03 00:50:00 INFO Bot Telegram siap & polling dimulai...
```

---

## 13. Instalasi sebagai Service `systemd`

1. Salin file service `olt-monitor.service` ke direktori systemd:
   ```bash
   sudo cp olt-monitor.service /etc/systemd/system/
   ```

2. Reload daemon systemd:
   ```bash
   sudo systemctl daemon-reload
   ```

3. Aktifkan service agar otomatis berjalan saat booting:
   ```bash
   sudo systemctl enable olt-monitor
   ```

4. Jalankan service:
   ```bash
   sudo systemctl start olt-monitor
   ```

5. Cek status service:
   ```bash
   sudo systemctl status olt-monitor
   ```

6. Melihat log real-time:
   ```bash
   journalctl -u olt-monitor -f
   ```

---

## 14. Daftar Perintah Telegram

| Perintah | Fungsi |
|---|---|
| `/start` | Menampilkan pesan selamat datang dan ringkasan menu |
| `/help` | Menampilkan penjelasan bantuan penggunaan perintah bot |
| `/cek_putus` | Menampilkan seluruh ONT yang berstatus offline |
| `/cek_redaman` | Menampilkan ONT dengan RX power melampaui threshold |
| `/status` | Menampilkan status koneksi SNMP ke OLT & latency |

---

## 15. Troubleshooting

| Masalah | Kemungkinan Penyebab | Solusi |
|---|---|---|
| Bot tidak merespons | Token Telegram salah atau bot mati | Periksa `TELEGRAM_BOT_TOKEN` pada `.env` & cek `systemctl status olt-monitor` |
| `⛔ Akses ditolak` | Chat ID Telegram belum terdaftar | Tambahkan Chat ID Anda ke `TELEGRAM_ALLOWED_CHAT_IDS` di `.env` |
| SNMP timeout | IP OLT tidak dapat dijangkau / firewall | Lakukan `ping` ke IP OLT & pastikan UDP port 161 tidak diblokir |
| SNMP error community | Community string salah | Sesuaikan `OLT_SNMP_COMMUNITY` pada `.env` |
| Hasil OID kosong | OID tidak sesuai dengan vendor OLT | Cek OID MIB OLT dengan perintah `snmpwalk` |
| RX power tidak muncul | OID optical power tidak terkonfigurasi | Isi `OID_ONT_RX_POWER` pada `.env` |
| Status ONT tertukar | Mapping status integer OLT berbeda | Sesuaikan `ONT_STATUS_ONLINE_VALUES` & `ONT_STATUS_OFFLINE_VALUES` |
| Angka redaman aneh | Scale pembagi berbeda | Sesuaikan `OLT_RX_POWER_SCALE` (misal 10 atau 100) |

---

## 16. Logging

Log aplikasi disimpan secara otomatis pada file `logs/app.log` (atau sesuai konfigurasi `LOG_FILE`).

Format log:
```text
2026-10-03 00:30:21 INFO Starting OLT Monitor
2026-10-03 00:30:25 INFO /cek_putus requested by 123456789
2026-10-03 00:30:27 INFO Ditemukan 4 ONT offline dari total 48 ONT.
```

*Keamanan Log:* Pustaka logger diprogram untuk **TIDAK PERNAH** mencatat Token Bot Telegram atau kredensial SNMP ke dalam file log.

---

## 17. Keamanan (Security)

1. File `.env` berisi rahasia kredensial dan **TIDAK BOLEH** di-commit ke Git repo. File `.gitignore` telah dikonfigurasi untuk mengecualikan `.env`.
2. Atur izin akses file `.env` di Linux agar hanya dapat dibaca oleh owner:
   ```bash
   chmod 600 /opt/olt-monitor/.env
   ```
3. Batasi perintah bot hanya untuk user terpercaya menggunakan `TELEGRAM_ALLOWED_CHAT_IDS`.
4. Pastikan SNMP Community hanya menggunakan izin **Read-Only (RO)**.

---

## 18. Cara Mengubah Threshold Redaman

Untuk mengubah batas redaman buruk (misalnya dari `-25 dBm` menjadi `-27 dBm`):

1. Buka file `.env`:
   ```bash
   nano /opt/olt-monitor/.env
   ```
2. Ubah nilai baris berikut:
   ```env
   OLT_RX_POWER_THRESHOLD=-27
   ```
3. Simpan file (`Ctrl+O`, `Enter`, `Ctrl+X`).
4. Restart service:
   ```bash
   sudo systemctl restart olt-monitor
   ```

---

## 19. Cara Mengubah OID Vendor & Model OLT

Aplikasi mendukung pengembalian informasi **Model** (kombinasi `Vendor + Model`, contoh: `ZTE F6639127`) ataupun **Serial Number** pada pesan Telegram (`/cek_putus` & `/cek_redaman`).

Jika menggunakan OLT HSGQ (Private MIB `50224`):
```env
OID_ONT_VENDOR=1.3.6.1.4.1.50224.3.3.2.1.25
OID_ONT_MODEL=1.3.6.1.4.1.50224.3.3.2.1.26
```

Jika OLT Anda menggunakan OID MIB berbeda (ZTE, Huawei, Fiberhome, dll):
1. Buka file `.env`.
2. Ganti nilai OID sesuai MIB vendor baru:
   ```env
   OID_ONT_STATUS=1.3.6.1.4.1.2011.6.128.1.1.2.46.1.15
   OID_ONT_RX_POWER=1.3.6.1.4.1.2011.6.128.1.1.2.51.1.4
   OID_ONT_SERIAL=1.3.6.1.4.1.2011.6.128.1.1.2.43.1.3
   ```
3. Restart service:
   ```bash
   sudo systemctl restart olt-monitor
   ```

---

## 20. Struktur Project

```text
olt-monitor/
├── app/
│   ├── __init__.py         # Package initializer
│   ├── main.py             # Entry point aplikasi
│   ├── config.py           # Config loader & env validator
│   ├── logger.py           # Logger formatter & setup
│   │
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── handlers.py     # Telegram command handlers & access control
│   │   └── messages.py     # HTML message formatters & split pagination
│   │
│   ├── snmp/
│   │   ├── __init__.py
│   │   ├── client.py       # Asynchronous SNMP client (GET/WALK)
│   │   └── parser.py       # OID suffix & Optical power converter
│   │
│   └── olt/
│       ├── __init__.py
│       ├── monitor.py      # OLT Monitoring business logic
│       └── models.py       # ONT Domain Data Model & Natural Sorting
│
├── tests/
│   ├── __init__.py
│   ├── test_config.py      # Unit test konfigurasi
│   ├── test_parser.py      # Unit test SNMP parser & power conversion
│   └── test_monitor.py     # Unit test logic offline & redaman
│
├── logs/
│   └── .gitkeep            # Folder penampung log
│
├── .env.example            # Template file konfigurasi environment
├── .gitignore              # Git ignore rules
├── requirements.txt        # Daftar dependency Python
├── README.md               # Dokumentasi panduan lengkap (Bahasa Indonesia)
└── olt-monitor.service     # File konfigurasi systemd service
```
