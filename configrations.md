transmind@transmind:~ $ sudo cat /etc/nginx/sites-enabled/transmind-pi 
server {
    listen 80;
    server_name 10.209.60.146 172.28.248.105 cam1.transmind.com.tr;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/transmind/Desktop/Transmind-PI/app.sock;

        # --- Akış için kritik ayarlar ---
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
        proxy_read_timeout 600s;  # Uzun süreli bağlantılar
        proxy_send_timeout 600s;
        send_timeout 600s;
    }
}
transmind@transmind:~ $ sudo cat /etc/systemd/system/gunicorn.service
[Unit]
Description=Gunicorn instance for Camera Stream (Transmind-PI)
After=network.target

[Service]
User=transmind
Group=www-data
WorkingDirectory=/home/transmind/Desktop/Transmind-PI
ExecStart=/usr/bin/gunicorn \
    --workers 1 \
    --worker-class gevent \
    --timeout 0 \
    --bind unix:/home/transmind/Desktop/Transmind-PI/app.sock \
    app:app
Restart=always
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target