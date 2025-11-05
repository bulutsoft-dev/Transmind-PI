import logging
from flask import Flask, render_template, redirect, request
import requests

# === Uygulama ve Loglama Kurulumu ===
app = Flask(__name__)

# Basit loglama
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        # MediaMTX WebRTC sayfasından içeriği al
        response = requests.get('http://172.28.117.8:8889/cam/', timeout=5)
        logger.info(f"Stream proxy'si: 172.28.117.8:8889/cam/ -> 200 OK")
        return response.text, response.status_code, response.headers
    except Exception as e:
        logger.error(f"Stream proxy hatası: {e}")
        return render_template('error.html'), 500


@app.route('/cam')
def cam():
    """Direkt MediaMTX WebRTC yayınına yönlendir."""
    return redirect('http://172.28.117.8:8889/cam/', code=307)


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
    logger.info("Flask sunucusu başlatıldı...")
    app.run(host='0.0.0.0', port=5000, debug=False)