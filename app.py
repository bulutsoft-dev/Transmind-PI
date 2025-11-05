import logging
from flask import Flask, render_template, redirect
from config import get_active_device_config, get_all_devices, ACTIVE_DEVICE

# === Uygulama ve Loglama Kurulumu ===
app = Flask(__name__)

# Basit loglama
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Aktif cihaz konfigürasyonunu al
active_device = get_active_device_config()
stream_url = active_device['STREAM_URL']

logger.info(f"Aktif cihaz: {ACTIVE_DEVICE}")
logger.info(f"Stream URL: {stream_url}")


@app.route('/')
def index():
    """Ana sayfayı gösterir."""
    all_devices = get_all_devices()
    return render_template('index.html', devices=all_devices, active_device=ACTIVE_DEVICE)


@app.route('/streams')
def streams():
    """Canlı yayın arayüzünü gösterir."""
    all_devices = get_all_devices()
    return render_template('index.html', devices=all_devices, active_device=ACTIVE_DEVICE)


@app.route('/cams')
def cams():
    """Canlı yayın arayüzünü gösterir."""
    all_devices = get_all_devices()
    return render_template('index.html', devices=all_devices, active_device=ACTIVE_DEVICE)


@app.route('/stream')
def stream():
    """Aktif cihazın stream URL'sine yönlendir."""
    logger.info(f"Stream yönlendirmesi: {stream_url}")
    return redirect(stream_url, code=307)


@app.route('/cam')
def cam():
    """Aktif cihazın WebRTC yayınına yönlendir."""
    logger.info(f"Cam yönlendirmesi: {stream_url}")
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
    logger.info("Mevcut cihazlar:")
    for device_id, device_config in get_all_devices().items():
        logger.info(f"  - {device_id}: {device_config['STREAM_URL']}")
    app.run(host='0.0.0.0', port=5000, debug=False)