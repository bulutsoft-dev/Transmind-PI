import io
from flask import Flask, Response, render_template
from picamera2 import Picamera2 # Kamera kütüphanesi eklendi

app = Flask(__name__)

# === Kamera Kurulumu ===
# Kamerayı başlat ve yapılandır
# Bu bloğun global alanda (if __name__ ... bloğunun DIŞINDA) olması önemlidir.
camera = Picamera2()
# Performans için çözünürlüğü 640x480 olarak ayarlayalım
config = camera.create_video_configuration(main={"size": (640, 480)})
camera.configure(config)
camera.start()
# === Kamera Kurulumu Bitişi ===


def generate_frames():
    """Kameradan görüntüleri yakalar ve MJPEG formatında yayınlar."""
    # io.BytesIO, yakalanan JPEG verilerini bellekte tutmak için kullanılır
    with io.BytesIO() as stream:
        while True:
            # Görüntüyü 'jpeg' formatında doğrudan stream'e yakala
            camera.capture_file(stream, format='jpeg')

            # Stream'in içeriğini (frame baytlarını) al
            frame_bytes = stream.getvalue()

            # Frame'i yayınla
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            # Bir sonraki frame için stream'i temizle
            stream.seek(0)
            stream.truncate()

@app.route('/stream')
def video_feed():
    """Video akış rotası."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    """Ana sayfa rotası."""
    return render_template('index.html')

# === Health endpoint - camera availability check ===
@app.route('/health')
def health():
    """Simple health check: returns 200 if a quick jpeg capture succeeds, otherwise 503 with error text.
    Note: this does a short capture using the same camera instance; it's intended for monitoring.
    """
    try:
        with io.BytesIO() as s:
            camera.capture_file(s, format='jpeg')
        return ('OK', 200)
    except Exception as e:
        # Return the exception message to help debugging (don't expose in public systems).
        return (f'ERROR: {e}', 503)
# === Health endpoint end ===

# === YENİ HATA YAKALAYICI ===
@app.errorhandler(404)
def page_not_found(error):
    """
    404 (Sayfa Bulunamadı) hatası oluştuğunda bu fonksiyon çalışır.
    Kullanıcıya özel 'error.html' sayfasını gösterir.
    """
    return render_template('error.html'), 404
# === HATA YAKALAYICI BİTİŞİ ===


# Gunicorn kullanırken bu bloğa gerek yok, ama test için kalabilir
if __name__ == '__main__':
    # Test için basit bir sunucu çalıştır
    app.run(host='0.0.0.0', port=5000, debug=True)
