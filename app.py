import time
import logging
import subprocess
from flask import Flask, Response, render_template, stream_with_context

# === Uygulama ve Loglama Kurulumu ===
app = Flask(__name__)

# Basit loglama
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === RTSP Stream Ayarları ===
RTSP_URL = "rtsp://172.28.117.8:8554/cam"
RTSP_TIMEOUT = 10

# === Kamera Kurulumu Kaldırıldı ===
# Artık uzak RTSP stream'ini kullanıyoruz


@app.route('/')
def index():
    """Ana sayfayı (video oynatıcı) gösterir."""
    return render_template('index.html')


@app.route('/stream')
def video_feed():
    """RTSP stream'ini MJPEG formatında proxy yapar."""
    logger.info(f"Stream isteği alındı. RTSP URL: {RTSP_URL}")

    return Response(stream_with_context(generate_frames()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def generate_frames():
    """
    RTSP stream'ini yakalayıp MJPEG formatında yayınlar.
    ffmpeg kullanarak RTSP'den kare çıkarır.
    """
    logger.info("RTSP akış oluşturucu başlatıldı.")

    try:
        # ffmpeg ile RTSP stream'ini açıyoruz
        process = subprocess.Popen(
            [
                'ffmpeg',
                '-rtsp_transport', 'tcp',
                '-i', RTSP_URL,
                '-f', 'image2pipe',
                '-pix_fmt', 'yuvj420p',
                '-vcodec', 'mjpeg',
                '-'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=10
        )

        logger.info("FFmpeg process başlatıldı")

        while True:
            try:
                # JPEG frame'i oku
                in_bytes = process.stdout.read(4)
                if not in_bytes:
                    logger.warning("FFmpeg process sonlandı")
                    break

                # JPEG başlangıç marker'ını bul (0xFFD8)
                if in_bytes[:2] != b'\xff\xd8':
                    # Başlangıcı bulana kadar oku
                    bytes_read = in_bytes
                    while True:
                        byte = process.stdout.read(1)
                        if not byte:
                            break
                        bytes_read += byte
                        if bytes_read[-2:] == b'\xff\xd8':
                            in_bytes = bytes_read[-2:]
                            break

                # JPEG sonu marker'ını (0xFFD9) bulana kadar oku
                if in_bytes[:2] == b'\xff\xd8':
                    frame_data = in_bytes
                    while True:
                        byte = process.stdout.read(1)
                        if not byte:
                            logger.warning("FFmpeg sonlandırıldı")
                            process.terminate()
                            raise GeneratorExit

                        frame_data += byte

                        # JPEG sonu bulundu
                        if frame_data[-2:] == b'\xff\xd9':
                            break

                    # Frame'i yayınla
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')

            except GeneratorExit:
                logger.info("İstemci bağlantıyı kesti, akış durduruluyor.")
                process.terminate()
                process.wait(timeout=5)
                break

            except Exception as e:
                logger.exception("Frame okuma hatası: %s", e)
                time.sleep(1)
                continue

    except Exception as e:
        logger.exception("FFmpeg başlatılamadı: %s", e)
        yield (b'--frame\r\n'
               b'Content-Type: text/plain\r\n\r\n'
               b'HATA: FFmpeg baslatilami\r\n')
        time.sleep(5)


@app.route('/health')
def health():
    """
    Sistemin ve RTSP stream'inin çalışıp çalışmadığını kontrol eden sağlık rotası.
    """
    try:
        logger.info(f"Sağlık kontrolü yapılıyor: {RTSP_URL}")

        # ffprobe ile RTSP stream'ini kontrol et
        result = subprocess.run(
            [
                'ffprobe',
                '-rtsp_transport', 'tcp',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1:nofile=1',
                RTSP_URL
            ],
            capture_output=True,
            timeout=5
        )

        if result.returncode == 0:
            return ('OK - RTSP Stream Aktif', 200)
        else:
            return ('HATA: RTSP Stream Ulaşılamıyor', 503)

    except subprocess.TimeoutExpired:
        logger.error("Sağlık kontrolü zaman aşımına uğradı")
        return ('HATA: Zaman aşımı', 503)
    except Exception as e:
        logger.exception("Sağlık kontrolü başarısız: %s", e)
        return (f'HATA: {e}', 503)


@app.errorhandler(404)
def page_not_found(error):
    """404 hata sayfası."""
    return render_template('error.html'), 404


# Uygulamayı doğrudan çalıştırmak için (gunicorn yerine test için)
if __name__ == '__main__':
    logger.info("Flask sunucusu test modunda başlatıldı...")
    logger.info(f"RTSP Stream URL: {RTSP_URL}")
    app.run(host='0.0.0.0', port=5000, debug=False)