#!/usr/bin/env python3
"""
Heartbeat sistemini test etmek için örnek script.
"""

import time
import logging
from heartbeat import init_heartbeat, get_heartbeat_manager, stop_heartbeat

# Loglama ayarı
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_heartbeat():
    """Heartbeat sistemini test et."""

    logger.info("=" * 60)
    logger.info("RPi Heartbeat Sistemi Test Başlıyor")
    logger.info("=" * 60)

    # Heartbeat sistemini başlat
    logger.info("\n1. Heartbeat sistemi başlatılıyor...")
    manager = init_heartbeat(
        device_id='lab_rpi_1_zerotier',
        interval=10,  # Test için 10 saniye
        offline_threshold=2
    )

    # Durumu kontrol et
    logger.info("\n2. Heartbeat durumu kontrol ediliyor...")
    time.sleep(2)

    manager = get_heartbeat_manager()
    if manager:
        logger.info(f"   ✓ Cihaz ID: {manager.device_id}")
        logger.info(f"   ✓ Hostname: {manager.hostname}")
        logger.info(f"   ✓ IP Adresi: {manager.ip_address}")
        logger.info(f"   ✓ Interval: {manager.interval}s")
        logger.info(f"   ✓ Offline Threshold: {manager.offline_threshold}")
        logger.info(f"   ✓ Durumu: {'✓ ÇALIŞIYOR' if manager.is_running() else '✗ DURMUŞ'}")

    # Test süresi - ping'lerin gönderilmesini izle
    logger.info("\n3. 30 saniye boyunca sistem izleniyor...")
    for i in range(3):
        time.sleep(10)
        if manager:
            logger.info(f"   [{i+1}/3] Missed Pings: {manager.missed_pings}")

    # Sistemi durdur
    logger.info("\n4. Heartbeat sistemi durdurluyor...")
    stop_heartbeat()

    logger.info("\n" + "=" * 60)
    logger.info("Test tamamlandı!")
    logger.info("=" * 60)


if __name__ == '__main__':
    try:
        test_heartbeat()
    except KeyboardInterrupt:
        logger.info("\n\nTest kullanıcı tarafından durduruldu")
        stop_heartbeat()
    except Exception as e:
        logger.error(f"Test hatası: {e}", exc_info=True)
        stop_heartbeat()

