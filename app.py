import logging
from flask import Flask, render_template

# === Uygulama ve Loglama Kurulumu ===
app = Flask(__name__)

# Basit loglama
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    """Ana sayfayı gösterir."""
    return render_template('index.html')


@app.route('/stream')
def stream():
    """Ana sayfa (/cam ile aynı içeriği gösterir)."""
    return render_template('index.html')


@app.route('/cam')
def cam():
    """Ana sayfa (/stream ile aynı içeriği gösterir)."""
    return render_template('index.html')


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