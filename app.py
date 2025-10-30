import io
from flask import Flask, Response, render_template

app = Flask(__name__)



def generate_frames():
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
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('index.html')

# Gunicorn kullanırken bu bloğa gerek yok, ama test için kalabilir
if __name__ == '__main__':
    # Run a simple server for testing
    app.run(host='0.0.0.0', port=5000, debug=True)
