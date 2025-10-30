import io
import time
import logging
from flask import Flask, Response, render_template, stream_with_context
from picamera2 import Picamera2

# === Uygulama ve Loglama Kurulumu ===
app = Flask(__name__)

# Basit loglama
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Kamera Kurulumu ===
# Bu bölüm sağlam ve iyi, olduğu gibi kalıyor.
camera = None
try:
    camera = Picamera2()
    config = camera.create_video_configuration(main={"size": (1480, 980)})
    config["controls"]["FrameDurationLimits"] = (33333, 33333)  # 30 FPS
    camera.configure(config)
    camera.start()
    logger.info("Kamera başarıyla başlatıldı")
except Exception as e:
    logger.exception("Kamera başlatılamadı: %s", e)
    camera = None


# === Kamera Kurulumu Bitişi ===


@app.route('/')
def index():
    """Ana sayfayı (video oynatıcı) gösterir."""
    return render_template('index.html')


@app.route('/stream')
def video_feed():
    """Video akış rotası."""
    if camera is None:
        logger.error("/stream çağrıldı ancak kamera mevcut değil")
        return ("Kamera mevcut değil", 503)

    return Response(stream_with_context(generate_frames()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def generate_frames():
    """
    Kameradan MJPEG formatında akış üretir.

    İYİLEŞTİRME: Bu fonksiyon artık io.BytesIO() objesini
    döngü dışında BİR KEZ oluşturur ve her kare için yeniden kullanır.
    Bu, bellek verimliliği için en önemli iyileştirmedir.
    """
    logger.info("Akış oluşturucu başlatıldı.")

    # Verimlilik: Stream objesini döngü dışında SADECE BİR KEZ oluştur
    with io.BytesIO() as stream:
        while True:
            try:
                # 1. Görüntüyü 'jpeg' formatında doğrudan stream'e yakala
                camera.capture_file(stream, format='jpeg')

                # 2. Stream'in içeriğini (frame baytlarını) al
                frame_bytes = stream.getvalue()

                # 3. Frame'i yayınla
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

                # 4. Verimlilik: Bir sonraki frame için stream'i temizle
                # (seek(0) imleci başa alır, truncate() içeriği siler)
                stream.seek(0)
                stream.truncate()

            except GeneratorExit:
                # Sağlamlık: İstemci bağlantıyı kopardı (tarayıcı kapatıldı)
                logger.info("İstemci bağlantıyı kesti, akış durduruluyor.")
                break  # Döngüden güvenle çık (with bloğu stream'i kapatacak)

            except Exception as e:
                # Sağlamlık: Kamera veya yakalama hatası
                logger.exception("Frame yakalama/yayınlama hatası: %s", e)

                # Orijinal kodunuzdaki mükemmel kamera yeniden başlatma mantığı
                try:
                    logger.warning("Hata sonrası kamera yeniden başlatılıyor...")
                    camera.stop()
                    time.sleep(0.5)
                    camera.start()
                    logger.info("Kamera başarıyla yeniden başlatıldı")
                except Exception as e2:
                    logger.exception("Kamera yeniden başlatılamadı: %s", e2)
                    time.sleep(1.0)  # Yeniden denemeden önce bekle

                # Hata ne olursa olsun, bir sonraki deneme için stream'i temizle
                stream.seek(0)
                stream.truncate()


@app.route('/health')
def health():
    """
    Sistemin ve kameranın çalışıp çalışmadığını kontrol eden sağlık rotası.
    Bu, hata ayıklama için harika bir araçtır.
    """
    try:
        if camera is None:
            return ("HATA: kamera başlatılmamış", 503)

        # Hızlı bir fotoğraf çekmeyi deneyerek kamerayı test et
        with io.BytesIO() as s:
            camera.capture_file(s, format='jpeg')

        return ('OK', 200)
    except Exception as e:
        logger.exception("Sağlık kontrolü başarısız: %s", e)
        return (f'HATA: {e}', 503)


@app.errorhandler(404)
def page_not_found(error):
    """404 hata sayfası."""
    return render_template('error.html'), 404


# Uygulamayı doğrudan çalıştırmak için (gunicorn yerine test için)
if __name__ == '__main__':
    logger.info("Flask sunucusu test modunda başlatılıyor...")
    app.run(host='0.0.0.0', port=5000, debug=False)