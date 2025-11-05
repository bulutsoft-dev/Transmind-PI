import logging
from flask import Flask, render_template, redirect, request
import requests
from config import get_active_device_config, get_all_devices, ACTIVE_DEVICE

# === Uygulama ve Loglama Kurulumu ===
app = Flask(__name__)

# Basit loglama
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Aktif cihaz konfigürasyonunu al
active_device = get_active_device_config()
stream_url = f"http://{active_device['STREAM_HOST']}:{active_device['STREAM_PORT']}/cam/"

logger.info(f"Aktif cihaz: {ACTIVE_DEVICE}")
logger.info(f"Stream URL: {stream_url}")


@app.route('/')
def index():
    """Ana sayfayı gösterir."""
    return render_template('index.html')


@app.route('/streams')
def streams():
    """Canlı yayın arayüzünü gösterir."""
    return render_template('index.html')


@app.route('/cams')
def cams():
    """Canlı yayın arayüzünü gösterir."""
    return render_template('index.html')


@app.route('/stream')
def stream():
    """MediaMTX WebRTC sayfasını proxy'le - URL tarayıcıda /stream olarak görünsün."""
    try:
        # Aktif cihazın stream URL'sinden içeriği al
        response = requests.get(stream_url, timeout=5)
        logger.info(f"Stream proxy'si: {stream_url} -> 200 OK")
        return response.text, response.status_code, response.headers
    except Exception as e:
        logger.error(f"Stream proxy hatası: {e}")
        return render_template('error.html'), 500


@app.route('/cam')
def cam():
    """Direkt MediaMTX WebRTC yayınına yönlendir."""
    return redirect(stream_url, code=307)


@app.route('/health')
def health():
    """Sistem sağlık kontrolü."""
    return ('OK', 200)


@app.errorhandler(404)
def page_not_found(error):
    """404 hata sayfası."""
    return render_template('error.html'), 404


# Uygulamayı doğrudan çalıştırmak için
if __name__ == '__main__':
    logger.info(f"Flask sunucusu başlatıldı... Aktif cihaz: {ACTIVE_DEVICE}")
    logger.info(f"Stream URL: {stream_url}")
    app.run(host='0.0.0.0', port=5000, debug=False)