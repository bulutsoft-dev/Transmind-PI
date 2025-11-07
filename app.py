import logging
from flask import Flask, render_template, redirect, jsonify, request
from config import get_active_device_config, get_all_devices, ACTIVE_DEVICE
from heartbeat import init_heartbeat, get_heartbeat_manager, stop_heartbeat

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

# Heartbeat sistemini başlat
heartbeat_manager = init_heartbeat(
    device_id=ACTIVE_DEVICE,
    interval=30,  # 30 saniye
    offline_threshold=3
)


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


# === Heartbeat API Endpoints ===

@app.route('/api/heartbeat/status', methods=['GET'])
def heartbeat_status():
    """Heartbeat durumunu döndür."""
    manager = get_heartbeat_manager()
    if manager:
        return jsonify({
            'status': 'running' if manager.is_running() else 'stopped',
            'device_id': manager.device_id,
            'interval': manager.interval,
            'missed_pings': manager.missed_pings,
            'offline_threshold': manager.offline_threshold,
            'hostname': manager.hostname,
            'ip_address': manager.ip_address,
        }), 200
    else:
        return jsonify({'status': 'not_initialized'}), 200


@app.route('/api/heartbeat/start', methods=['POST'])
def heartbeat_start():
    """Heartbeat sistemini başlat."""
    try:
        manager = get_heartbeat_manager()
        if manager and not manager.is_running():
            manager.start()
            return jsonify({'message': 'Heartbeat başlatıldı'}), 200
        elif manager and manager.is_running():
            return jsonify({'message': 'Heartbeat zaten çalışıyor'}), 200
        else:
            return jsonify({'error': 'Heartbeat manager başlatılamadı'}), 500
    except Exception as e:
        logger.error(f"Heartbeat başlatma hatası: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/heartbeat/stop', methods=['POST'])
def heartbeat_stop():
    """Heartbeat sistemini durdur."""
    try:
        manager = get_heartbeat_manager()
        if manager and manager.is_running():
            manager.stop()
            return jsonify({'message': 'Heartbeat durduruldu'}), 200
        else:
            return jsonify({'message': 'Heartbeat zaten durmuş'}), 200
    except Exception as e:
        logger.error(f"Heartbeat durdurma hatası: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/heartbeat/settings', methods=['GET', 'POST'])
def heartbeat_settings():
    """Heartbeat ayarlarını görüntüle veya güncelle."""
    manager = get_heartbeat_manager()

    if not manager:
        return jsonify({'error': 'Heartbeat manager başlatılmamış'}), 500

    if request.method == 'GET':
        return jsonify({
            'interval': manager.interval,
            'offline_threshold': manager.offline_threshold,
        }), 200

    else:  # POST
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Geçersiz JSON'}), 400

            interval = data.get('interval')
            offline_threshold = data.get('offline_threshold')

            if interval:
                manager.interval = int(interval)
            if offline_threshold:
                manager.offline_threshold = int(offline_threshold)

            return jsonify({
                'message': 'Ayarlar güncellendi',
                'interval': manager.interval,
                'offline_threshold': manager.offline_threshold,
            }), 200
        except Exception as e:
            logger.error(f"Ayarlar güncelleme hatası: {e}")
            return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def page_not_found(error):
    """404 hata sayfası."""
    return render_template('error.html'), 404


def shutdown_heartbeat():
    """Uygulama kapatılırken heartbeat'i durdur."""
    logger.info("Uygulama kapatılıyor, heartbeat durdurluyor...")
    stop_heartbeat()


# Uygulama kapatılırken heartbeat'i durdur
import atexit
atexit.register(shutdown_heartbeat)


# Uygulamayı doğrudan çalıştırmak için
if __name__ == '__main__':
    logger.info(f"Flask sunucusu başlatıldı... Aktif cihaz: {ACTIVE_DEVICE}")
    logger.info(f"Stream URL: {stream_url}")
    logger.info("Mevcut cihazlar:")
    for device_id, device_config in get_all_devices().items():
        logger.info(f"  - {device_id}: {device_config['STREAM_URL']}")
    logger.info("Heartbeat sistemi aktif!")
    app.run(host='0.0.0.0', port=5000, debug=False)