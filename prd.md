# PRD — Telegram OLT Monitoring

## 1. Informasi Proyek

**Nama aplikasi:** OLT Telegram Monitor

**Versi:** 1.0.0

**Platform:** Ubuntu Linux / STB Linux

**Bahasa pemrograman:** Python 3

**Interface pengguna:** Telegram Bot

**Protokol monitoring:** SNMP

**Database:** Tidak diperlukan untuk versi 1.0

**Deployment:** Server Ubuntu/STB sebagai service `systemd`

**Tujuan utama:**

Membuat aplikasi Telegram Bot sederhana untuk melakukan pengecekan kondisi ONT/ONU pada OLT melalui SNMP.

Bot hanya memiliki dua fungsi utama:

```text
/cek_putus
```

Untuk menampilkan ONT yang sedang **offline/putus**.

```text
/cek_redaman
```

Untuk menampilkan ONT yang mempunyai **redaman/optical power tinggi atau buruk** berdasarkan batas yang ditentukan pada `.env`.

---

# 2. Tujuan Aplikasi

Aplikasi dibuat untuk membantu teknisi mengetahui kondisi pelanggan/ONT tanpa harus login langsung ke OLT.

Alur penggunaan:

```text
Admin/Operator
      │
      ▼
Telegram Bot
      │
      ▼
Python Application
      │
      ▼
SNMP
      │
      ▼
OLT
      │
      ├── Status ONT
      ├── Optical RX Power
      ├── Optical TX Power
      ├── PON/Slot/Port
      └── ONT ID
```

Operator cukup mengirim:

```text
/cek_putus
```

atau:

```text
/cek_redaman
```

Bot kemudian mengambil data langsung dari OLT melalui SNMP dan mengirimkan hasilnya ke Telegram.

---

# 3. Scope Versi 1.0

## Fitur wajib

### 3.1 `/start`

Menampilkan informasi penggunaan bot.

Contoh:

```text
📡 OLT MONITOR

Bot monitoring OLT melalui SNMP.

Perintah:

/cek_putus
Menampilkan ONT yang sedang offline.

/cek_redaman
Menampilkan ONT dengan redaman tinggi.

/status
Menampilkan status koneksi aplikasi ke OLT.

/help
Menampilkan bantuan.
```

---

# 4. Command `/cek_putus`

Ketika operator mengirim:

```text
/cek_putus
```

aplikasi harus:

1. Membaca konfigurasi OLT dari `.env`.
2. Membuat koneksi SNMP.
3. Melakukan SNMP WALK/GET terhadap OID status ONT.
4. Mengidentifikasi ONT yang berstatus offline.
5. Mengelompokkan hasil berdasarkan OLT dan PON.
6. Mengirim hasil ke Telegram.

Contoh hasil:

```text
🔴 ONT PUTUS

Total: 4 ONT

PON 1/1/1
• ONT 03
  Status: OFFLINE
  SN: ZTEG12345678

• ONT 08
  Status: OFFLINE
  SN: ZTEG87654321


PON 1/1/2
• ONT 05
  Status: OFFLINE
  SN: ZTEG11223344

• ONT 1/1/3
  Status: OFFLINE
  SN: ZTEG99887766

Waktu pengecekan:
03-10-2026 00:30:15
```

Jika tidak ada ONT putus:

```text
🟢 TIDAK ADA ONT PUTUS

Semua ONT yang terdeteksi saat pengecekan
berstatus ONLINE.

Waktu:
03-10-2026 00:30:15
```

---

# 5. Command `/cek_redaman`

Ketika operator mengirim:

```text
/cek_redaman
```

aplikasi melakukan:

1. SNMP WALK terhadap tabel ONT.
2. Mengambil optical power yang relevan.
3. Membaca nilai redaman/power.
4. Membandingkan nilai dengan threshold dari `.env`.
5. Menampilkan ONT yang melewati threshold.

Contoh:

```text
⚠️ REDAMAN TINGGI

Batas: -25 dBm

Total: 5 ONT

PON 1/1/1

ONT 03
SN: ZTEG12345678
RX Power: -27.41 dBm
Status: ONLINE

ONT 07
SN: ZTEG22334455
RX Power: -26.18 dBm
Status: ONLINE


PON 1/1/2

ONT 11
SN: ZTEG66778899
RX Power: -28.02 dBm
Status: ONLINE

Waktu pengecekan:
03-10-2026 00:31:02
```

---

# 6. Definisi Redaman Tinggi

Aplikasi harus mendukung threshold yang dapat diubah melalui `.env`.

Contoh:

```env
OLT_RX_POWER_THRESHOLD=-25
```

Karena optical RX power biasanya direpresentasikan dalam dBm dengan nilai negatif, aplikasi **tidak boleh menggunakan perbandingan angka secara sembarangan**.

Contoh:

```text
ONT A = -21 dBm
ONT B = -26 dBm
ONT C = -29 dBm
```

Jika:

```env
OLT_RX_POWER_THRESHOLD=-25
```

maka:

```text
-21 dBm → normal
-26 dBm → tinggi/buruk
-29 dBm → tinggi/buruk
```

Logic:

```python
if rx_power <= threshold:
    high_attenuation = True
```

Tetapi logic ini harus dibuat configurable apabila vendor OLT menggunakan definisi nilai optical power yang berbeda.

---

# 7. Konfigurasi `.env`

Semua konfigurasi penting harus berada di `.env`.

Contoh:

```env
# ==========================================
# TELEGRAM
# ==========================================

TELEGRAM_BOT_TOKEN=123456789:xxxxxxxxxxxxxxxx

# Telegram user/chat ID yang diperbolehkan
TELEGRAM_ALLOWED_CHAT_IDS=123456789,987654321


# ==========================================
# OLT
# ==========================================

OLT_NAME=OLT-UTAMA
OLT_HOST=192.168.88.2
OLT_PORT=161

# v2c / v3
OLT_SNMP_VERSION=2c

# Untuk SNMP v2c
OLT_SNMP_COMMUNITY=public


# ==========================================
# SNMP
# ==========================================

SNMP_TIMEOUT=5
SNMP_RETRIES=2


# ==========================================
# REDAMAN
# ==========================================

OLT_RX_POWER_THRESHOLD=-25


# ==========================================
# OID
# ==========================================

OID_ONT_STATUS=1.3.6.x.x.x
OID_ONT_RX_POWER=1.3.6.x.x.x
OID_ONT_TX_POWER=1.3.6.x.x.x
OID_ONT_SERIAL=1.3.6.x.x.x
OID_ONT_NAME=1.3.6.x.x.x


# ==========================================
# APPLICATION
# ==========================================

LOG_LEVEL=INFO
LOG_FILE=/opt/olt-monitor/logs/app.log
```

**Catatan penting:**

Jangan mengasumsikan OID di atas benar untuk semua OLT.

Antigravity harus membuat OID sebagai konfigurasi sehingga pengguna dapat menggantinya sesuai MIB/OID OLT.

---

# 8. Dukungan SNMP

Versi pertama minimal mendukung:

```text
SNMP v2c
```

Struktur kode harus dibuat sedemikian rupa sehingga nantinya mudah menambahkan:

```text
SNMP v1
SNMP v3
```

Untuk produksi, konfigurasi SNMP harus dibatasi berdasarkan IP server monitoring dan tidak menggunakan community `public` secara sembarangan. Dokumentasi MikroTik juga mencatat bahwa SNMP v1/v2c menggunakan community string dan kurang aman dibanding SNMPv3. ([Mikrotik Manual][1])

Walaupun OLT Anda bukan MikroTik, prinsip keamanan tersebut tetap berlaku.

---

# 9. Arsitektur Aplikasi

Gunakan arsitektur modular.

```text
olt-monitor/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── handlers.py
│   │   └── messages.py
│   │
│   ├── snmp/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── parser.py
│   │
│   ├── olt/
│   │   ├── __init__.py
│   │   ├── monitor.py
│   │   └── models.py
│   │
│   ├── config.py
│   ├── logger.py
│   └── utils.py
│
├── tests/
│   ├── test_config.py
│   ├── test_parser.py
│   └── test_monitor.py
│
├── logs/
│
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── olt-monitor.service
```

---

# 10. Komponen Aplikasi

## 10.1 Config Manager

Bertugas membaca:

```text
.env
```

Gunakan:

```text
python-dotenv
```

Konfigurasi harus divalidasi ketika aplikasi dijalankan.

Jika misalnya:

```env
TELEGRAM_BOT_TOKEN=
```

kosong, aplikasi harus menampilkan error yang jelas:

```text
ERROR: TELEGRAM_BOT_TOKEN belum dikonfigurasi.
```

---

# 11. SNMP Client

Buat class:

```python
SNMPClient
```

Minimal menyediakan:

```python
get(oid)
walk(oid)
```

Contoh konsep:

```python
client = SNMPClient(config)

value = client.get(oid)

rows = client.walk(oid)
```

Library SNMP yang direkomendasikan:

```text
pysnmp
```

SNMP client harus mempunyai:

* timeout
* retry
* error handling
* logging
* connection failure detection

---

# 12. OLT Monitor

Buat class:

```python
OLTMonitor
```

Minimal:

```python
get_ont_status()
get_offline_onts()
get_ont_optical_power()
get_high_attenuation_onts()
```

Contoh:

```python
offline_onts = monitor.get_offline_onts()
```

dan:

```python
bad_signal = monitor.get_high_attenuation_onts()
```

---

# 13. Data Model ONT

Buat model data seperti:

```python
ONT(
    pon="1/1/1",
    ont_id="3",
    serial_number="ZTEG12345678",
    name="Pelanggan 01",
    status="online",
    rx_power=-23.5,
    tx_power=2.1
)
```

Field minimal:

```text
olt
slot
pon
ont_id
serial_number
name
status
rx_power
tx_power
```

Tidak perlu database pada versi 1.0.

---

# 14. Mapping Index SNMP

Karena hasil `SNMP WALK` sering menggunakan index OID tertentu, buat parser khusus:

```text
SNMP response
      ↓
OID parser
      ↓
ONT object
      ↓
OLT Monitor
      ↓
Telegram formatter
```

Jangan mencampurkan logic parsing OID dengan Telegram handler.

---

# 15. Telegram Bot

Gunakan:

```text
python-telegram-bot
```

Library ini menyediakan `ApplicationBuilder` sebagai pola utama untuk membangun aplikasi bot. ([Python Telegram Bot][2])

Handler minimal:

```python
CommandHandler("start", start_command)
CommandHandler("help", help_command)
CommandHandler("cek_putus", cek_putus_command)
CommandHandler("cek_redaman", cek_redaman_command)
CommandHandler("status", status_command)
```

---

# 16. Security Telegram

Bot tidak boleh bisa digunakan sembarang orang.

Gunakan:

```env
TELEGRAM_ALLOWED_CHAT_IDS=123456789,987654321
```

Ketika user yang tidak terdaftar menjalankan:

```text
/cek_putus
```

bot membalas:

```text
⛔ Akses ditolak.

Chat ID Anda tidak terdaftar sebagai pengguna bot.
```

Jangan menjalankan proses SNMP untuk user yang tidak memiliki izin.

---

# 17. Command `/status`

Walaupun fitur utama hanya dua command, tambahkan:

```text
/status
```

untuk troubleshooting.

Contoh:

```text
📡 STATUS OLT MONITOR

OLT:
OLT-UTAMA

IP:
192.168.88.2

SNMP:
v2c

Status:
🟢 CONNECTED

Response:
12 ms

Last check:
03-10-2026 00:35:21
```

Jika gagal:

```text
🔴 SNMP ERROR

OLT:
OLT-UTAMA

IP:
192.168.88.2

Error:
Timeout

Pastikan:
• IP OLT benar
• SNMP aktif
• Community benar
• UDP 161 tidak diblokir
```

---

# 18. Loading Message

Karena SNMP WALK bisa membutuhkan waktu, ketika user menjalankan:

```text
/cek_putus
```

bot terlebih dahulu mengirim:

```text
🔎 Sedang mengecek ONT putus...

Mohon tunggu.
```

Kemudian pesan tersebut dapat diedit menjadi hasil akhir.

Hal yang sama untuk:

```text
/cek_redaman
```

---

# 19. Error Handling

Aplikasi wajib menangani:

### SNMP timeout

```text
❌ Gagal menghubungi OLT.

Penyebab:
SNMP timeout.

OLT: OLT-UTAMA
IP: 192.168.88.2
```

### Community salah

```text
❌ SNMP tidak dapat mengambil data.

Periksa SNMP community atau konfigurasi SNMP OLT.
```

### OID tidak ditemukan

```text
❌ OID tidak ditemukan.

Periksa konfigurasi OID pada .env.
```

### Data kosong

```text
ℹ️ Tidak ada data ONT yang ditemukan.
```

### Exception internal

User tidak boleh menerima traceback Python.

Telegram cukup menerima:

```text
❌ Terjadi kesalahan pada aplikasi.

Silakan periksa log server.
```

Detail error masuk ke log.

---

# 20. Logging

Gunakan Python `logging`.

Format:

```text
2026-10-03 00:30:21 INFO Starting OLT Monitor
2026-10-03 00:30:22 INFO Connecting to OLT 192.168.88.2
2026-10-03 00:30:22 INFO SNMP connection successful
2026-10-03 00:30:25 INFO /cek_putus requested by 123456789
2026-10-03 00:30:27 INFO Found 4 offline ONTs
```

Log error:

```text
2026-10-03 00:35:10 ERROR SNMP timeout: 192.168.88.2
```

Jangan pernah mencatat:

```text
TELEGRAM_BOT_TOKEN
SNMP password
SNMPv3 authentication password
SNMPv3 encryption password
```

ke log.

---

# 21. Format Output Telegram

Gunakan Markdown atau HTML Telegram.

Hasil harus dibuat ringkas.

Contoh:

```text
🔴 <b>ONT PUTUS</b>

OLT: OLT-UTAMA
Total: 3

<b>PON 1/1/1</b>

1. ONT 03
   SN: ZTEG12345678

2. ONT 08
   SN: ZTEG87654321

<b>PON 1/1/2</b>

3. ONT 05
   SN: ZTEG99887766

⏱ 03-10-2026 00:40:12
```

---

# 22. Jika Data Sangat Banyak

Telegram mempunyai batas ukuran pesan.

Jika jumlah ONT sangat banyak, jangan mengirim satu pesan yang terlalu panjang.

Implementasikan:

```python
split_message()
```

Misalnya hasil 300 ONT otomatis dibagi:

```text
📄 Bagian 1/4
...
```

```text
📄 Bagian 2/4
...
```

dan seterusnya.

---

# 23. Sorting

Hasil `/cek_putus` dan `/cek_redaman` harus diurutkan:

```text
OLT
↓
Slot
↓
PON
↓
ONT ID
```

Contoh:

```text
1/1/1 ONT 1
1/1/1 ONT 2
1/1/1 ONT 3
1/1/2 ONT 1
1/1/2 ONT 2
```

---

# 24. Status ONT

Status ONT harus dibuat configurable.

Contoh konfigurasi:

```env
ONT_STATUS_ONLINE=1
ONT_STATUS_OFFLINE=2
```

Tetapi jangan mengasumsikan bahwa semua OLT menggunakan:

```text
1 = online
2 = offline
```

Mapping tersebut harus dapat diubah melalui `.env`.

Contoh:

```env
ONT_STATUS_ONLINE_VALUES=1
ONT_STATUS_OFFLINE_VALUES=2,3,4
```

Dengan demikian aplikasi dapat menyesuaikan OLT/vendor yang berbeda.

---

# 25. Optical Power

Buat konfigurasi:

```env
OLT_RX_POWER_THRESHOLD=-25
```

Selain itu, siapkan:

```env
OLT_RX_POWER_SCALE=10
```

atau:

```env
OLT_RX_POWER_SCALE=100
```

Karena SNMP dapat mengembalikan nilai integer yang harus dikonversi menjadi dBm.

Contoh:

```text
SNMP:
-253

Scale:
10

Hasil:
-25.3 dBm
```

Parser harus menggunakan konfigurasi scale.

---

# 26. Konfigurasi OID

`.env.example` harus menyediakan bagian:

```env
# ONT STATUS
OID_ONT_STATUS=

# ONT SERIAL
OID_ONT_SERIAL=

# ONT NAME
OID_ONT_NAME=

# RX POWER
OID_ONT_RX_POWER=

# TX POWER
OID_ONT_TX_POWER=
```

Jika suatu OID tidak digunakan, aplikasi tidak boleh crash.

Misalnya:

```env
OID_ONT_TX_POWER=
```

maka fitur tetap dapat menjalankan:

```text
/cek_putus
/cek_redaman
```

---

# 27. Multi OLT — Struktur Siapkan Sejak Awal

Walaupun versi 1.0 cukup satu OLT, struktur program sebaiknya tidak dibuat terlalu sulit untuk dikembangkan.

Contoh `.env`:

```env
OLT_NAME=OLT-UTAMA
OLT_HOST=192.168.88.2
```

Nantinya bisa dikembangkan menjadi:

```text
OLT-01
OLT-02
OLT-03
```

Tetapi **jangan implementasikan multi-OLT pada versi 1.0 kecuali diperlukan**.

Fokus versi awal adalah aplikasi sederhana dan stabil.

---

# 28. Requirements

Minimal:

```text
python-telegram-bot
pysnmp
python-dotenv
```

Tambahkan library lain hanya jika benar-benar diperlukan.

Contoh:

```text
python-telegram-bot>=22
pysnmp
python-dotenv
```

Jangan memasukkan framework web seperti:

```text
FastAPI
Flask
Django
```

karena aplikasi ini tidak membutuhkan web interface.

---

# 29. Deployment Ubuntu

Aplikasi harus dapat dijalankan sebagai:

```text
systemd service
```

Contoh:

```text
/etc/systemd/system/olt-monitor.service
```

Service:

```text
[Unit]
Description=OLT Telegram Monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=oltmonitor
WorkingDirectory=/opt/olt-monitor
EnvironmentFile=/opt/olt-monitor/.env
ExecStart=/opt/olt-monitor/venv/bin/python -m app.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Sesuaikan jika implementasi environment variable dilakukan langsung oleh Python.

---

# 30. Instalasi

README.md harus menjelaskan secara lengkap:

### 30.1 Update Ubuntu

```bash
sudo apt update
sudo apt upgrade -y
```

### 30.2 Install Python

```bash
sudo apt install -y python3 python3-venv python3-pip
```

### 30.3 Buat directory

```bash
sudo mkdir -p /opt/olt-monitor
```

### 30.4 Buat virtual environment

```bash
cd /opt/olt-monitor
python3 -m venv venv
source venv/bin/activate
```

### 30.5 Install dependency

```bash
pip install -r requirements.txt
```

---

# 31. Konfigurasi `.env`

README harus menjelaskan:

```bash
cp .env.example .env
nano .env
```

Kemudian pengguna mengisi:

```env
TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_ALLOWED_CHAT_IDS=123456789

OLT_NAME=OLT-UTAMA
OLT_HOST=192.168.88.2
OLT_PORT=161

OLT_SNMP_VERSION=2c
OLT_SNMP_COMMUNITY=private

OLT_RX_POWER_THRESHOLD=-25

OID_ONT_STATUS=...
OID_ONT_RX_POWER=...
OID_ONT_SERIAL=...
```

---

# 32. Testing SNMP

Sebelum menjalankan bot, README harus menjelaskan cara melakukan testing SNMP dari Ubuntu.

Install:

```bash
sudo apt install -y snmp
```

Contoh:

```bash
snmpwalk -v2c -c COMMUNITY 192.168.88.2 1.3.6.1
```

Pengguna kemudian bisa memastikan OLT merespons sebelum menjalankan aplikasi.

Ini penting agar troubleshooting dapat dibedakan antara:

```text
masalah SNMP
```

dan:

```text
masalah Python/Bot.
```

---

# 33. Menjalankan Manual

README:

```bash
cd /opt/olt-monitor
source venv/bin/activate

python -m app.main
```

Jika berhasil:

```text
2026-10-03 00:50:00 INFO OLT Telegram Monitor started
2026-10-03 00:50:00 INFO Telegram bot started
```

---

# 34. Menjalankan dengan systemd

```bash
sudo cp olt-monitor.service /etc/systemd/system/
```

Kemudian:

```bash
sudo systemctl daemon-reload
sudo systemctl enable olt-monitor
sudo systemctl start olt-monitor
```

Cek:

```bash
sudo systemctl status olt-monitor
```

Log:

```bash
journalctl -u olt-monitor -f
```

---

# 35. README.md

Antigravity **wajib membuat README.md lengkap** yang berisi:

```text
1. Deskripsi aplikasi
2. Fitur
3. Arsitektur
4. Requirement
5. Persiapan Telegram Bot
6. Persiapan SNMP OLT
7. Cara mendapatkan OID
8. Instalasi Ubuntu
9. Virtual environment
10. Konfigurasi .env
11. Testing SNMP
12. Menjalankan aplikasi
13. Instalasi systemd
14. Perintah Telegram
15. Troubleshooting
16. Logging
17. Security
18. Cara mengubah threshold redaman
19. Cara mengubah OID
20. Struktur project
```

---

# 36. Troubleshooting README

Harus ada tabel seperti:

| Masalah                  | Kemungkinan penyebab     | Solusi                       |
| ------------------------ | ------------------------ | ---------------------------- |
| Bot tidak merespons      | Token salah              | Periksa `.env`               |
| Access denied            | Chat ID belum terdaftar  | Tambahkan Chat ID            |
| SNMP timeout             | OLT tidak bisa dijangkau | Test ping/SNMP               |
| SNMP timeout             | UDP 161 diblokir         | Periksa firewall             |
| OID kosong               | OID salah                | Test `snmpwalk`              |
| RX power kosong          | OID optical power salah  | Periksa MIB OLT              |
| Semua ONT dianggap putus | Mapping status salah     | Periksa `ONT_STATUS_*`       |
| Redaman salah            | Scale salah              | Periksa `OLT_RX_POWER_SCALE` |

---

# 37. Security Requirement

`.env` **tidak boleh masuk Git**.

`.gitignore`:

```gitignore
.env
venv/
__pycache__/
*.pyc
logs/
```

Permission:

```bash
chmod 600 .env
```

Bot hanya boleh menerima command dari:

```env
TELEGRAM_ALLOWED_CHAT_IDS
```

SNMP hanya menggunakan:

```text
READ ONLY
```

Tidak menggunakan SNMP SET.

---

# 38. Prinsip Penting Implementasi

Antigravity **jangan membuat asumsi vendor OLT**.

Aplikasi harus dibuat generic.

Contoh:

```text
Vendor OLT
     │
     ▼
MIB / OID
     │
     ▼
.env
     │
     ▼
SNMP Client
     │
     ▼
Parser
     │
     ▼
ONT Model
     │
     ▼
Telegram
```

Dengan demikian ketika nanti OLT diganti, pengguna cukup mengubah OID/configuration tanpa perlu mengubah keseluruhan program.

---

# 39. Acceptance Criteria

Aplikasi dianggap berhasil apabila:

### AC-01

Bot dapat menerima:

```text
/start
```

dan menampilkan bantuan.

### AC-02

Bot dapat menerima:

```text
/cek_putus
```

dan melakukan SNMP query ke OLT.

### AC-03

Bot dapat menampilkan hanya ONT dengan status offline.

### AC-04

Bot tidak menampilkan ONT online pada `/cek_putus`.

### AC-05

Bot dapat menerima:

```text
/cek_redaman
```

### AC-06

Bot hanya menampilkan ONT yang nilai RX power-nya melewati threshold.

### AC-07

Threshold dapat diubah hanya melalui:

```text
.env
```

tanpa mengubah source code.

### AC-08

OID dapat diubah melalui:

```text
.env
```

tanpa mengubah source code.

### AC-09

SNMP timeout tidak menyebabkan aplikasi berhenti.

### AC-10

OLT tidak bisa diakses → bot memberikan pesan error yang mudah dipahami.

### AC-11

User Telegram yang tidak diizinkan tidak dapat menjalankan monitoring.

### AC-12

Aplikasi dapat berjalan sebagai:

```text
systemd service
```

dan otomatis restart jika proses mati.

### AC-13

Semua aktivitas penting masuk ke log.

### AC-14

README.md menyediakan dokumentasi instalasi dari Ubuntu kosong sampai aplikasi berjalan.

---

# 40. Struktur Output yang Diharapkan dari Antigravity

Antigravity harus menghasilkan **project lengkap**, bukan hanya potongan kode.

Output:

```text
olt-monitor/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── logger.py
│   │
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── handlers.py
│   │   └── messages.py
│   │
│   ├── snmp/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── parser.py
│   │
│   └── olt/
│       ├── __init__.py
│       ├── monitor.py
│       └── models.py
│
├── tests/
│   ├── test_config.py
│   ├── test_parser.py
│   └── test_monitor.py
│
├── logs/
│   └── .gitkeep
│
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── olt-monitor.service
```

---

# 41. Instruksi Khusus untuk Antigravity

Tambahkan instruksi berikut pada akhir prompt:

> Buat aplikasi ini sebagai aplikasi production-ready yang sederhana, stabil, dan mudah dipelihara.
>
> Jangan membuat web dashboard.
>
> Jangan membuat database pada versi 1.0.
>
> Jangan menambahkan fitur yang tidak diminta.
>
> Jangan hard-code IP OLT, community SNMP, Telegram token, threshold redaman, atau OID.
>
> Semua konfigurasi tersebut harus berasal dari `.env`.
>
> Jangan mengasumsikan OID tertentu berlaku untuk semua vendor OLT.
>
> Pisahkan SNMP client, parser OID, logic monitoring OLT, dan Telegram handler.
>
> Gunakan asynchronous Telegram bot sesuai API/library `python-telegram-bot` modern.
>
> Gunakan timeout dan retry pada SNMP.
>
> Semua error harus ditangani dengan baik.
>
> Jangan pernah menampilkan traceback Python kepada pengguna Telegram.
>
> Jangan menyimpan Telegram token atau password SNMP di source code.
>
> Implementasikan logging yang jelas.
>
> Pastikan `/cek_putus` hanya mengembalikan ONT yang offline.
>
> Pastikan `/cek_redaman` hanya mengembalikan ONT yang melewati threshold redaman.
>
> Buat `.env.example`.
>
> Buat `requirements.txt`.
>
> Buat `README.md` lengkap dalam Bahasa Indonesia.
>
> Buat `systemd service`.
>
> Buat unit test untuk parser, konfigurasi, dan logic threshold.
>
> Setelah selesai, lakukan pemeriksaan project untuk memastikan tidak ada import yang rusak, konfigurasi yang hard-coded, atau dependency yang hilang.

---

## Catatan yang sangat penting sebelum implementasi

Bagian yang paling perlu Anda siapkan sebenarnya adalah **OID OLT**. Python/SNMP-nya relatif standar, tetapi data seperti:

```text
ONT ID
PON
Serial Number
Status online/offline
RX optical power
TX optical power
```