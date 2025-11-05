import os

# Cihaz konfigürasyonları
DEVICES = {
    'lab_rpi_1_zerotier': {
        'HOST': '172.28.117.8',
        'USER': 'transmind_3b',
        'PASSWORD': '12345678',
        'NAME': 'Raspberry Pi 3B+ Zerotier',
        'DESCRIPTION': 'Raspberry Pi 3B+ cihazı proje danışmanı tarafından temin edildi.',
        'VNC_ENABLED': True,
        'VNC_PORT': 5901,
        'NOVNC_URL': '/novnc/lab_rpi_1_zerotier/vnc.html',
        'STREAM_URL': 'http://172.28.117.8:8889/cam/',
    },
    'lab_rpi_2_zerotier': {
        'HOST': '172.28.248.105',
        'USER': 'transmind',
        'PASSWORD': '12345678',
        'NAME': 'Raspberry Pi 4 Zerotier',
        'DESCRIPTION': 'Raspberry Pi 4 2 GB RAM proje bütçesi kullanılarak satın alındı',
        'VNC_ENABLED': True,
        'VNC_PORT': 5902,
        'NOVNC_URL': '/novnc/lab_rpi_2_zerotier/vnc.html',
        'STREAM_URL': 'http://172.28.248.105:8889/cam/',
    },
}

# Aktif cihaz (environment variable'dan okunur, varsayılan: lab_rpi_1_zerotier)
ACTIVE_DEVICE = os.getenv('ACTIVE_DEVICE', 'lab_rpi_1_zerotier')

# Aktif cihazın konfigürasyonunu al
def get_active_device_config():
    """Aktif cihazın konfigürasyonunu döndür."""
    return DEVICES.get(ACTIVE_DEVICE)

# Tüm cihazları döndür
def get_all_devices():
    """Tüm cihazları döndür."""
    return DEVICES
