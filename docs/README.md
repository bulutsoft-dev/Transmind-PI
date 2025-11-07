# Transmind-PI — MediaMTX Canlı Yayın Sunucusu

Bu proje, Raspberry Pi üzerinde çalışan **MediaMTX** sunucusundan gelen RTSP yayınını web tarayıcılarında görüntülemek için Flask tabanlı bir arayüz sağlar.

MediaMTX, RTSP yayınlarını otomatik olarak tarayıcı dostu formatlara (WebRTC ve HLS) dönüştürür.

---

## 🚀 Hızlı Başlangıç

### Gereksinimler

- Raspberry Pi (veya Debian tabanlı Linux)
- Python 3.8+
- MediaMTX sunucusu çalışıyor ve 8888/8889 portlarında aktif
- Flask + Gunicorn + Gevent

### Kurulum (1 dakika)

```bash
# Sistem paketleri
sudo apt update && sudo apt install -y python3-pip python3-venv

# Proje klasörü
mkdir -p ~/transmind-pi && cd ~/transmind-pi

# Sanal ortam
python3 -m venv venv
source venv/bin/activate

# Python paketleri
pip install --upgrade pip
pip install Flask gunicorn gevent
```

### Çalıştırma

```bash
# Development
python app.py

# Production (Gunicorn)
gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:5000 app:app
```

Tarayıcıdan erişin: **http://localhost:5000** (veya Pi'nin IP adresi)

---

## 📡 MediaMTX Kurulumu

MediaMTX henüz kurulu değilse:

```bash
# İndir ve kur
sudo mkdir -p /opt/mediamtx
cd /opt/mediamtx
sudo wget https://github.com/bluenviron/mediamtx/releases/download/v1.1.0/mediamtx_v1.1.0_linux_armv7.tar.gz
sudo tar -xzf mediamtx_v1.1.0_linux_armv7.tar.gz

# IPv4 dinlemesi açmak için yapılandırma
sudo nano /opt/mediamtx/mediamtx.yml
```

**Dosyada şu satırları bulup düzenle:**

```yaml
# HLS Sunucusu (Port 8888)
hlsAddress: 0.0.0.0:8888

# WebRTC Sunucusu (Port 8889)
webrtcAddress: 0.0.0.0:8889

# Stream yollarını yapılandır (paths bölümüne ekle)
paths:
  cam:
    # RTSP kaynağı (kendi kameranızın RTSP URL'si)
    source: rtsp://your-camera-ip:554/stream
  
  stream:
    # Stream, cam ile aynı kaynağı kullanır
    source: rtsp://your-camera-ip:554/stream
```

**Servisi başlat:**

```bash
sudo systemctl start mediamtx
sudo systemctl enable mediamtx
```

---

## ⚠️ Önemli: MediaMTX Yapılandırması

Eğer şu hatayı alıyorsanız:
```
path 'stream' is not configured
```

Bu, MediaMTX'in `/stream` yolunu tanımadığı anlamına gelir. Çözmek için:

1. **MediaMTX config dosyasını düzenle:**
   ```bash
   sudo nano /opt/mediamtx/mediamtx.yml
   ```

2. **`paths:` bölümünü bulup şu eklemeyi yap:**
   ```yaml
   paths:
     cam:
       # Kameranızın RTSP adresi
       source: rtsp://192.168.1.100:554/stream
     
     stream:
       # Stream yolu (cam ile aynı kaynağı kullanır)
       source: rtsp://192.168.1.100:554/stream
   ```

3. **Servisi yeniden başlat:**
   ```bash
   sudo systemctl restart mediamtx
   ```

**Not:** `rtsp://192.168.1.100:554/stream` kısmını kendi kameranızın RTSP adresine göre değiştirin!

---

## 🌐 Yayın Adresleri

MediaMTX sunucusu iki farklı yayın yöntemi sağlar:

### 1️⃣ WebRTC (Ultra Düşük Gecikme - 1 saniye)
- **URL:** `http://172.28.117.8:8889/cam`
- **Avantajları:** En düşük gecikme, en yüksek kalite
- **Dezavantajları:** Özel tarayıcı desteği gerekebilir

### 2️⃣ HLS (Geniş Uyumluluk - 10-20 saniye gecikme)
- **URL:** `http://172.28.117.8:8888/cam/index.m3u8`
- **Avantajları:** Tüm cihazlarda çalışır (iPhone, iPad, eski tarayıcılar)
- **Dezavantajları:** Biraz daha yüksek gecikme

---

## 📋 Proje Yapısı

```
transmind-pi/
├── app.py              # Flask uygulaması
├── requirements.txt    # Python bağımlılıkları
├── templates/
│   ├── index.html      # Ana sayfa (WebRTC + HLS)
│   └── error.html      # 404 hata sayfası
└── README.md          # Bu dosya
```

---

## 🔧 app.py Detayları

Flask uygulaması sadece statik sayfa sunmaktadır:

- **GET /**: Ana sayfa (WebRTC ve HLS yayınları gösteren arayüz)
- **GET /health**: Sunucu sağlık kontrolü (basit "OK" döner)
- **404 Handler**: Bulunamayan sayfalar için hata sayfası

```python
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return ('OK', 200)
```

---

## 📺 Arayüz Özellikleri

index.html sayfası şunları sağlar:

✅ **WebRTC Oynatıcı** - MediaMTX'in yerleşik web arayüzünü iframe ile gösterir
✅ **HLS Video Oynatıcı** - HLS.js kütüphanesiyle video akışı oynatır
✅ **Canlı Durum Göstergesi** - Her iki yayının durumunu gösterir
✅ **Responsive Tasarım** - Mobil, tablet ve masaüstü cihazlarda uyumlu
✅ **Dinamik Saat** - Cihaz saatini gerçek zamanlı gösterir

---

## 🛠️ Production Deployment

### Systemd Servisi (Oto-başlatma)

`/etc/systemd/system/transmind-pi.service` dosyasını oluştur:

```ini
[Unit]
Description=TransMind Flask Web Server (MediaMTX Interface)
After=network.target mediamtx.service
Wants=mediamtx.service

[Service]
User=pi
Group=www-data
WorkingDirectory=/home/pi/transmind-pi
ExecStart=/home/pi/transmind-pi/venv/bin/gunicorn \
    --worker-class gevent \
    --workers 1 \
    --bind 0.0.0.0:5000 \
    app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Aktifleştir:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable transmind-pi.service
sudo systemctl start transmind-pi.service
sudo systemctl status transmind-pi.service

# Logları izle
sudo journalctl -u transmind-pi.service -f
```

### Nginx Reverse Proxy

`/etc/nginx/sites-available/transmind-pi`:

```nginx
server {
    listen 80;
    server_name transmind.local;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Aktifleştir:**

```bash
sudo ln -s /etc/nginx/sites-available/transmind-pi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🌍 İnternet'e Açma

### Seçenek 1: Tailscale VPN (Önerilen)
Güvenli ve kurulumu kolay:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Sonra `http://<tailscale-ip>:5000` ile erişin.

### Seçenek 2: ngrok (Geçici Test)
```bash
./ngrok http 5000
```

### Seçenek 3: Port Forwarding (İleri)
Router ayarlarında 5000 portunu forward et + DDNS (No-IP/DuckDNS) kullan.

---

## 🐛 Sorun Giderme

### "Connection refused" hatası

```bash
# Portun açık olup olmadığını kontrol et
sudo netstat -tlnp | grep 5000
sudo netstat -tlnp | grep 8888
sudo netstat -tlnp | grep 8889

# Firewall kontrolü
sudo ufw status
sudo ufw allow 5000/tcp
sudo ufw allow 8888/tcp
sudo ufw allow 8889/tcp
```

### MediaMTX yayını görünmüyor

```bash
# MediaMTX servisi kontrol et
sudo systemctl status mediamtx
sudo journalctl -u mediamtx -f

# IPv4 dinlemesi sağla
sudo nano /opt/mediamtx/mediamtx.yml
# hlsAddress: 0.0.0.0:8888
# webrtcAddress: 0.0.0.0:8889
sudo systemctl restart mediamtx
```

### CORS (Cross-Origin) hataları

Eğer harici kaynaktan erişiyorsan ve CORS hataları alıyorsan, Nginx'te header ekle:

```nginx
add_header 'Access-Control-Allow-Origin' '*';
add_header 'Access-Control-Allow-Methods' 'GET, OPTIONS';
```

---

## 📊 Başarı Kontrol Listesi

- [ ] Python 3 + Flask kurulu
- [ ] MediaMTX çalışıyor (8888 ve 8889 portlarda dinleme)
- [ ] `http://localhost:5000` tarayıcıda açılıyor
- [ ] WebRTC yayını görünüyor
- [ ] HLS yayını görünüyor
- [ ] Systemd servisi otomatik başlıyor

---

## 📝 Telif & Lisans

TransMind - Akıllı Ulaştırma Yönetim Sistemi

---

## 💬 Destek

Sorun varsa loglara bak:

```bash
# Flask uygulaması
sudo journalctl -u transmind-pi.service -f

# MediaMTX
sudo journalctl -u mediamtx.service -f

# Nginx
sudo tail -f /var/log/nginx/error.log
```
