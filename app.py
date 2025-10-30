import io
import time
import logging
from flask import Flask, Response, render_template, stream_with_context
from picamera2 import Picamera2

app = Flask(__name__)

# Basit loglama
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Kamera Kurulumu ===
try:
    camera = Picamera2()
    config = camera.create_video_configuration(main={"size": (1480, 980)})  # Daha stabil
    config["controls"]["FrameDurationLimits"] = (33333, 33333)  # 30 FPS
    camera.configure(config)
    camera.start()
    logger.info("Camera started successfully")
except Exception as e:
    logger.exception("Failed to start camera: %s", e)
    camera = None
# === Kamera Kurulumu Bitişi ===


def generate_frames():
    """Kameradan MJPEG formatında akış üretir."""
    if camera is None:
        logger.error("generate_frames called but camera is not initialized")
        return

    while True:
        try:
            stream = io.BytesIO()
            camera.capture_file(stream, format='jpeg')
            frame_bytes = stream.getvalue()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        except GeneratorExit:
            logger.info("Client disconnected from stream")
            break
        except Exception as e:
            logger.exception("Frame capture failed: %s", e)
            # Kamera hata verirse yeniden başlatmayı dene
            try:
                camera.stop()
                time.sleep(0.5)
                camera.start()
                logger.info("Camera restarted after failure")
            except Exception as e2:
                logger.exception("Camera restart failed: %s", e2)
                time.sleep(1.0)


@app.route('/stream')
def video_feed():
    """Video akış rotası."""
    if camera is None:
        return ("Camera not available", 503)

    return Response(stream_with_context(generate_frames()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    try:
        if camera is None:
            return ("ERROR: camera not initialized", 503)
        with io.BytesIO() as s:
            camera.capture_file(s, format='jpeg')
        return ('OK', 200)
    except Exception as e:
        logger.exception("Health check failed: %s", e)
        return (f'ERROR: {e}', 503)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html'), 404
