# RPi Heartbeat Sistemi Dokümantasyonu

## Genel Bakış

Bu heartbeat sistemi, Raspberry Pi cihazlarının sunucu ile düzenli iletişim kurmasını sağlar. Sistem aşağıdaki işlemleri gerçekleştirir:

1. **Cihaz Kaydı**: RPi, başlangıçta sunucuya kendisini kaydeder
2. **Düzenli Ping**: Belirtilen aralıkla heartbeat sinyalleri gönderir
3. **Durum İzleme**: Başarısız ping'leri takip eder ve offline durumunu bildirir
4. **Ayar Yönetimi**: Sunucudan dinamik olarak ayarları güncelleyebilir

---

## Dosya Yapısı

```
Transmind-PI/
├── app.py                 # Flask uygulaması (heartbeat entegrasyonlu)
├── config.py              # Konfigürasyon (DEBUG mode, server URL'leri)
├── heartbeat.py           # Heartbeat yöneticisi (ana sistem)
├── test_heartbeat.py      # Test script'i
├── requirements.txt       # Python bağımlılıkları
└── README.md
```

---

## Kurulum

### 1. Bağımlılıkları Kur

```bash
pip install -r requirements.txt
```

Gerekli paketler:
- **Flask** - Web framework
- **requests** - HTTP istekleri için
- **gevent** - Async işlemler
- **gunicorn** - Production sunucusu

### 2. Ortam Değişkenlerini Ayarla

```bash
# Debug mode (localhost:8000 kullanır)
export DEBUG=True
export ACTIVE_DEVICE=lab_rpi_1_zerotier

# Production mode (transmind.com.tr kullanır)
export DEBUG=False
export ACTIVE_DEVICE=lab_rpi_1_zerotier
```

---

## Kullanım

### Flask Uygulamasını Çalıştır

```bash
python app.py
```

Uygulama başladığında otomatik olarak heartbeat sistemi açılır.

### Test Scriptini Çalıştır

```bash
python test_heartbeat.py
```

---

## API Endpoints

### 1. Heartbeat Durumunu Kontrol Et

```bash
GET /api/heartbeat/status
```

**Yanıt:**
```json
{
    "status": "running",
    "device_id": "lab_rpi_1_zerotier",
    "interval": 30,
    "missed_pings": 0,
    "offline_threshold": 3,
    "hostname": "rpi-hostname",
    "ip_address": "192.168.1.100"
}
```

### 2. Heartbeat'i Başlat

```bash
POST /api/heartbeat/start
```

**Yanıt:**
```json
{
    "message": "Heartbeat başlatıldı"
}
```

### 3. Heartbeat'i Durdur

```bash
POST /api/heartbeat/stop
```

**Yanıt:**
```json
{
    "message": "Heartbeat durduruldu"
}
```

### 4. Ayarları Görüntüle

```bash
GET /api/heartbeat/settings
```

**Yanıt:**
```json
{
    "interval": 30,
    "offline_threshold": 3
}
```

### 5. Ayarları Güncelle

```bash
POST /api/heartbeat/settings
Content-Type: application/json

{
    "interval": 60,
    "offline_threshold": 5
}
```

---

## Sunucu Tarafı API Endpoints

Sistem sunucuya aşağıdaki endpoint'lere istek gönderir:

### 1. Cihaz Kaydı (Başlangıçta)

```
POST /rpi/api/device/register/
```

**Gönderilen Veri:**
```json
{
    "device_id": "lab_rpi_1_zerotier",
    "hostname": "rpi-hostname",
    "ip_address": "192.168.1.100",
    "debug_mode": true
}
```

### 2. Heartbeat Ping (Düzenli)

```
POST /rpi/api/heartbeat/ping/
```

**Gönderilen Veri:**
```json
{
    "device_id": "lab_rpi_1_zerotier",
    "hostname": "rpi-hostname",
    "ip_address": "192.168.1.100",
    "timestamp": 1673456789
}
```

### 3. Durum Kontrol (İsteğe Bağlı)

```
GET /rpi/api/status/{device_id}/
```

### 4. Ayarları Güncelle (İsteğe Bağlı)

```
POST /rpi/api/device/{device_id}/settings/
```

**Gönderilen Veri:**
```json
{
    "heartbeat_interval": 60,
    "offline_threshold": 5
}
```

---

## Konfigürasyon

### config.py

```python
# Debug Mode
DEBUG = True  # True: localhost:8000, False: https://transmind.com.tr

# Server URL'leri Otomatik Seçilir
if DEBUG:
    SERVER_BASE_URL = 'http://localhost:8000'
else:
    SERVER_BASE_URL = 'https://transmind.com.tr'

# Aktif Cihaz
ACTIVE_DEVICE = 'lab_rpi_1_zerotier'
```

### Heartbeat Parametreleri

```python
# app.py içinde
heartbeat_manager = init_heartbeat(
    device_id=ACTIVE_DEVICE,
    interval=30,              # 30 saniye aralıkla ping gönder
    offline_threshold=3       # 3 başarısız ping sonra offline say
)
```

---

## Hata Yönetimi

### Network Bağlantısı Kesilirse

- Sistem otomatik olarak retry'lar
- `missed_pings` sayacı artar
- `offline_threshold` aşılırsa offline durumu logger'a yazılır

### Log Örneği

```
INFO:heartbeat:✓ Cihaz başarıyla kaydedildi: lab_rpi_1_zerotier
INFO:heartbeat:Heartbeat döngüsü başlatıldı (interval: 30s)
DEBUG:heartbeat:✓ Heartbeat gönderildi: lab_rpi_1_zerotier
WARNING:heartbeat:✗ Heartbeat gönderme başarısız (1/3): Connection refused
WARNING:heartbeat:✗ Heartbeat gönderme başarısız (2/3): Connection refused
ERROR:heartbeat:⚠ OFFLINE: 3 ping başarısız oldu!
```

---

## Graceful Shutdown

Uygulama kapatılırken heartbeat sistemi otomatik olarak durdurulur:

```python
import atexit
atexit.register(shutdown_heartbeat)
```

---

## Örnek Senaryo

### Senaryo 1: Normal Operasyon

```bash
# 1. Flask uygulamasını başlat
python app.py

# 2. Diğer terminalde heartbeat durumunu kontrol et
curl http://localhost:5000/api/heartbeat/status

# 3. Heartbeat ayarlarını güncelle
curl -X POST http://localhost:5000/api/heartbeat/settings \
  -H "Content-Type: application/json" \
  -d '{"interval": 60}'
```

### Senaryo 2: Sunucu Yeniden Kaydı

```bash
# Ayarları güncellemek heartbeat'i yeniden başlatır
# (yeni ayarlar ile)
```

---

## Performans Özellikleri

- **Hafif**: Minimal CPU ve bellek kullanımı
- **Async**: Threading kullanarak ana uygulamayı bloklamaz
- **Robust**: Timeout ve hata yönetimi ile güvenli
- **Configurable**: Dinamik ayar güncellemeleri

---

## Troubleshooting

### Problem: Heartbeat gönderilmiyor

**Çözüm:**
1. Network bağlantısını kontrol et
2. Sunucu URL'sinin doğru olduğunu kontrol et (DEBUG mode)
3. Log'lara bak: `cat app.log | grep heartbeat`

### Problem: Offline durumu bildiriliyor

**Çözüm:**
1. Sunucu çalışıyor mu kontrol et
2. Firewall ayarlarını kontrol et
3. Interval değerini artır: `POST /api/heartbeat/settings`

### Problem: Ayarlar güncellenmiyor

**Çözüm:**
1. JSON format'ını kontrol et
2. Heartbeat manager'ın çalışıp çalışmadığını kontrol et
3. /api/heartbeat/status endpoint'ini kontrol et

---

## Lisans & İletişim

Transmind Projesi - 2024

