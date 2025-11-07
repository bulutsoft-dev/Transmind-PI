import logging
import threading
import time
import requests
import socket
from config import SERVER_BASE_URL, ACTIVE_DEVICE, DEBUG

logger = logging.getLogger(__name__)


class HeartbeatManager:
    """RPi cihazının heartbeat sinyallerini yönetir."""

    def __init__(self, device_id=None, interval=30, offline_threshold=3):
        """
        Heartbeat manager'ı başlat.

        Args:
            device_id: Cihaz ID'si (None ise ACTIVE_DEVICE kullanılır)
            interval: Heartbeat gönderme aralığı (saniye)
            offline_threshold: Offline sayılmadan önceki miss sayısı
        """
        self.device_id = device_id or ACTIVE_DEVICE
        self.interval = interval
        self.offline_threshold = offline_threshold
        self.running = False
        self.thread = None
        self.missed_pings = 0

        # Cihaz metadata
        self.hostname = socket.gethostname()
        self.ip_address = self._get_ip_address()

        logger.info(f"HeartbeatManager başlatıldı - Device ID: {self.device_id}, "
                   f"Interval: {self.interval}s, Offline Threshold: {offline_threshold}")

    def _get_ip_address(self):
        """Cihazın IP adresini al."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            logger.warning(f"IP adres alınamadı: {e}")
            return "unknown"

    def _register_device(self):
        """Cihazı sunucuya kaydet."""
        try:
            url = f"{SERVER_BASE_URL}/rpi/api/device/register/"

            payload = {
                "device_id": self.device_id,
                "hostname": self.hostname,
                "ip_address": self.ip_address,
                "debug_mode": DEBUG,
            }

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info(f"✓ Cihaz başarıyla kaydedildi: {self.device_id}")
            logger.debug(f"Kayıt yanıtı: {response.json()}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Cihaz kayıt hatası: {e}")
            return False

    def _send_heartbeat(self):
        """Sunucuya heartbeat ping gönder."""
        try:
            url = f"{SERVER_BASE_URL}/rpi/api/heartbeat/ping/"

            payload = {
                "device_id": self.device_id,
                "hostname": self.hostname,
                "ip_address": self.ip_address,
                "timestamp": int(time.time()),
            }

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            self.missed_pings = 0
            logger.debug(f"✓ Heartbeat gönderildi: {self.device_id}")

        except requests.exceptions.RequestException as e:
            self.missed_pings += 1
            logger.warning(f"✗ Heartbeat gönderme başarısız ({self.missed_pings}/{self.offline_threshold}): {e}")

            if self.missed_pings >= self.offline_threshold:
                logger.error(f"⚠ OFFLINE: {self.offline_threshold} ping başarısız oldu!")

    def _get_device_status(self):
        """Sunucudan cihaz durumunu al."""
        try:
            url = f"{SERVER_BASE_URL}/rpi/api/status/{self.device_id}/"

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            status = response.json()
            logger.debug(f"Cihaz durumu alındı: {status}")
            return status

        except requests.exceptions.RequestException as e:
            logger.warning(f"Cihaz durumu alınamadı: {e}")
            return None

    def _update_settings(self, heartbeat_interval=None, offline_threshold=None):
        """Cihaz heartbeat ayarlarını güncelle."""
        try:
            url = f"{SERVER_BASE_URL}/rpi/api/device/{self.device_id}/settings/"

            payload = {}
            if heartbeat_interval is not None:
                payload["heartbeat_interval"] = heartbeat_interval
            if offline_threshold is not None:
                payload["offline_threshold"] = offline_threshold

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info(f"✓ Ayarlar güncellendi: {payload}")

            if heartbeat_interval:
                self.interval = heartbeat_interval
            if offline_threshold:
                self.offline_threshold = offline_threshold

            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Ayarlar güncellenemedi: {e}")
            return False

    def _heartbeat_loop(self):
        """Ana heartbeat döngüsü."""
        logger.info(f"Heartbeat döngüsü başlatıldı (interval: {self.interval}s)")

        # İlk olarak cihazı kaydet
        self._register_device()

        # Döngü başla
        while self.running:
            try:
                self._send_heartbeat()
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Heartbeat döngüsü hatası: {e}")
                time.sleep(self.interval)

        logger.info("Heartbeat döngüsü durduruldu")

    def start(self):
        """Heartbeat yöneticisini başlat."""
        if self.running:
            logger.warning("Heartbeat zaten çalışıyor!")
            return

        self.running = True
        self.thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.thread.start()
        logger.info(f"✓ Heartbeat yöneticisi başlatıldı (Device: {self.device_id})")

    def stop(self):
        """Heartbeat yöneticisini durdur."""
        if not self.running:
            logger.warning("Heartbeat zaten durmuş!")
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info(f"✓ Heartbeat yöneticisi durduruldu (Device: {self.device_id})")

    def is_running(self):
        """Heartbeat çalışıyor mu kontrol et."""
        return self.running and self.thread and self.thread.is_alive()


# Global heartbeat manager örneği
_heartbeat_manager = None


def init_heartbeat(device_id=None, interval=30, offline_threshold=3):
    """Heartbeat sistemini başlat."""
    global _heartbeat_manager

    if _heartbeat_manager is None:
        _heartbeat_manager = HeartbeatManager(
            device_id=device_id,
            interval=interval,
            offline_threshold=offline_threshold
        )
        _heartbeat_manager.start()

    return _heartbeat_manager


def get_heartbeat_manager():
    """Global heartbeat manager'ı al."""
    return _heartbeat_manager


def stop_heartbeat():
    """Heartbeat sistemini durdur."""
    global _heartbeat_manager

    if _heartbeat_manager is not None:
        _heartbeat_manager.stop()
        _heartbeat_manager = None
