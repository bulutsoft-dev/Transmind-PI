# Transmind-PI

Bu repo için hızlı kurulum ve çalıştırma rehberi (Raspberry Pi, Picamera2 ile JPEG stream ve Gunicorn + gevent kullanarak yayın).

Aşağıdaki adımlar Raspberry Pi OS (Lite/Full) üzerinde SSH ile bağlı olduğunuzu ve kamerayı CSI portuna doğru bağladığınızı varsayar.

---

## Özet
Bu rehberde aşağıyı yapıyoruz:
- Sistem güncelleme ve kamera arayüzünü etkinleştirme
- Gerekli sistem paketlerini kurma (libcamera, picamera2, geliştirme başlıkları)
- Proje klasörü oluşturma, `venv` oluşturma
- Örnek `app.py` (Picamera2 + Flask) dosyası
- Sanal ortamda gerekli Python paketlerini kurma (Flask, Gunicorn, gevent)
- Gunicorn ile çalıştırma (tek process, asenkron worker) — Kamera çakışmalarını önlemek için önemli
- Opsiyonel: systemd servis dosyası, internete açma seçenekleri (ngrok, Tailscale)

---

## 1. Sistem güncelleme ve kamera etkinleştirme
Önce sistemi güncelleyin:

```bash
sudo apt update && sudo apt upgrade -y
```

Kamera arayüzünü aktif edin (Legacy Camera seçeneği pi/raspios bazlı sistemlerde gerekebilir):

```bash
sudo raspi-config
# Interface Options -> Legacy Camera (I1) -> Enable
# Bitince reboot isteyecektir, reboot edin.
sudo reboot
```

---

## 2. Gerekli sistem paketlerini yükleyin
picamera2 ve libcamera'nın Python bağlamalarını ve derleme için gerekli başlıkları kurun:

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-picamera2 python3-libcamera libcap-dev
```

Açıklama:
- `python3-picamera2` ve `python3-libcamera`: sistem paketleri olarak libcamera/picamera2 bağlamalarını sağlar.
- `libcap-dev`: bazı Python paketlerinin (ör. python-prctl) derlenmesi için gerekli başlıklar.

Not: Eğer paket deposunda eksik bir paket varsa, önce Raspberry Pi OS sürümünüzün güncel olduğundan emin olun.

---

## 3. Proje klasörü ve örnek uygulama
Proje için klasör oluşturun ve örnek `app.py` dosyasını ekleyin (aşağıdaki örnek performans için 640x480 kullanır):

```bash
mkdir -p ~/stream_project
cd ~/stream_project
```

`app.py` içeriği (örnek):

```python
import io
from flask import Flask, Response
from picamera2 import Picamera2

app = Flask(__name__)

# Kamerayı başlat ve yapılandır (performans için 640x480 önerilir)
camera = Picamera2()
config = camera.create_video_configuration(main={"size": (640, 480)})
camera.configure(config)
camera.start()


def generate_frames():
    with io.BytesIO() as stream:
        while True:
            camera.capture_file(stream, format='jpeg')
            frame_bytes = stream.getvalue()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            stream.seek(0)
            stream.truncate()


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# geliştirirken test etmek isterseniz:
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)
```

Dosyayı kaydedin (ör. `nano app.py`) ve çıkın.

---

## 4. Sanal ortam ve Python paketleri
Proje klasöründe bir `venv` oluşturun, aktif edin ve gerekli paketleri kurun:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install Flask gunicorn gevent
# Eğer sistem paketleri yeterli değilse (nadiren): pip install picamera2
```

Not: `python3-picamera2` ve `python3-libcamera` genellikle apt ile kurulduğunda, `pip install picamera2` gerekmeyebilir. Eğer `ModuleNotFoundError: No module named 'picamera2'` veya `No module named 'libcamera'` hatası alırsanız önce apt ile kurduğunuzdan ve/veya sanal ortamda doğru paketleri yüklediğinizden emin olun.

---

## 5. Gunicorn ile çalıştırma (kamera erişim çakışmasını önlemek)
Kameraya tek bir process erişebildiği için Gunicorn'u "tek worker" ile ama asenkron worker class (gevent) ile çalıştırın:

```bash
# venv aktifken
gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:5000 app:app
```

Açıklama:
- `--workers 1`: Fiziksel kameraya yalnızca bir process erişecek. Çoklu process aynı anda kamerayı açmaya çalışırsa "Device or resource busy" hatası alırsınız.
- `--worker-class gevent`: Tek process içinde asenkron I/O ile birden fazla istemciyi (stream izleyicisini) idare edebilirsiniz.

Tarayıcıdan test:

http://<RASPBERRY_PI_IP>:5000/video_feed

---

## 6. systemd servisi (opsiyonel: cihaz açıldığında otomatik başlatma)
Aşağıdaki service dosyasını `/etc/systemd/system/stream.service` olarak oluşturun ve içindeki `User`, `WorkingDirectory` ve `ExecStart` yollarını kendi kullanıcı adınıza göre düzenleyin.

```ini
[Unit]
Description=Gunicorn Video Stream Server
After=network.target

[Service]
User=pi
Group=www-data
WorkingDirectory=/home/pi/stream_project
ExecStart=/home/pi/stream_project/venv/bin/gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Servisi etkinleştirme ve başlatma:

```bash
sudo systemctl daemon-reload
sudo systemctl enable stream.service
sudo systemctl start stream.service
sudo systemctl status stream.service
```

---

## 7. Hata / Sorun Giderme (Troubleshooting)
- Hata: `RuntimeError: Failed to acquire camera: Device or resource busy` → Neden: Birden fazla process aynı anda kameraya erişmeye çalışıyor. Çözüm: Gunicorn'u `--workers 1` ile çalıştırın.
- Hata: `ModuleNotFoundError: No module named 'picamera2'` → Çözüm: `sudo apt install python3-picamera2 python3-libcamera` veya venv içindeyken `pip install picamera2` (önce `libcap-dev` gibi sistem başlıklarını kurun).
- Hata: `You need to install libcap development headers to build this module` → Çözüm: `sudo apt install libcap-dev` ve sonra `pip install ...` tekrar deneyin.
- Eğer `libcamera` eksikse: `sudo apt install python3-libcamera` ile kurun.

---

## 8. İnternete açma seçenekleri (kısa)
- Hızlı test: ngrok kullanın (`./ngrok http 5000`) — ücretsiz plan sınırlı olabilir.
- Güvenli ve kalıcı: Tailscale veya ZeroTier ile bir mesh VPN kullanın.
- Doğrudan port açma: Router'da port forwarding + DDNS (No-IP / DuckDNS) — güvenlik riskleri ve NAT/ISP kısıtlamaları olabilir.

---

## 9. Ek notlar
- Donanımsal JPEG sıkıştırma kullanıldığı sürece (camera.capture_file(stream, format='jpeg')) CPU yükünüz düşük kalır; gerçek FPS sınırını büyük ölçüde kamera/VPU belirler.
- Eğer yüksek performans, düşük gecikme ve çoklu kaynak kullanımı gerekiyorsa C/C++ ile libcamera tabanlı bir sunucu yazmak mümkün fakat geliştirme maliyeti ve karmaşıklığı artar.

---

Herhangi bir adımda hata alırsanız, aldığınız hata mesajını buraya yapıştırın; adım adım yardımcı olurum.
