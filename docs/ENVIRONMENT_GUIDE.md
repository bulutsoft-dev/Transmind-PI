# Ortam (Environment) Rehberi

Bu rehber, proje için sanal ortamı sistem kütüphanelerini (ör. python3-libcamera) görebilecek şekilde yeniden oluşturma adımlarını açıklar. Aşağıdaki adımlar, mevcut `TM` sanal ortamını silip, `--system-site-packages` ile yeni bir sanal ortam oluşturmayı ve bağımlılıkları kurmayı kapsar.

Not: Aşağıdaki komutları proje dizininizde (`/home/furkanblt/Documents/Transmind/Transmind-PI`) çalıştırın.

---

## 1) Mevcut ortamı devre dışı bırakın ve klasörü silin
Eğer hâlihazırda sanal ortam etkinse, çıkın:

```bash
deactivate
```

Ardından proje içindeki `TM` klasörünü silin:

```bash
rm -rf TM
```

Bu adım, önceki izole ortamı tamamen kaldırır.

## 2) Yeni sanal ortamı `--system-site-packages` ile oluşturun
Bu adım kritik: `--system-site-packages` bayrağı, ortamın sistem genelindeki paketleri de görmesine izin verir (ör. `python3-libcamera` gibi apt ile kurulmuş paketler).

```bash
python3 -m venv TM --system-site-packages
```

## 3) Yeni ortamı etkinleştirin ve proje bağımlılıklarını kurun
Ortamı etkinleştirin:

```bash
source TM/bin/activate
```

Ardından ihtiyaç duyulan pip paketlerini kurun (sanal ortam içinde):

```bash
pip install --upgrade pip
pip install flask picamera2 gunicorn
```

Notlar:
- `libcamera` veya `python3-libcamera` sistem (apt) ile yüklendiyse, pip ile tekrar kurmanıza gerek yok. `--system-site-packages` sayesinde erişilebilir olacaktır.
- `picamera2` pip paketidir ve burada ayrıca kurulur; `libcamera` ise sistem kütüphanesidir.

## 4) Doğrulama
Aşağıdaki adımlarla doğrulayın:

1) Python içinde `libcamera` modülünü içe aktarılabiliyor mu kontrol edin:

```bash
python -c "import libcamera; print('libcamera bulundu')"
```

Eğer hata alırsanız (`ModuleNotFoundError: No module named 'libcamera'`), büyük olasılıkla `python3-libcamera` sistem paketiniz yüklü değil ya da sistem Python sürümünüz ile uyumsuzdur. Bu durumda:

- `sudo apt install python3-libcamera` ile yükleyin (Raspberry Pi OS veya ilgili dağıtıma uygun paketler).
- Paket yüklüyse ve hâlâ görünmüyorsa, ortamın gerçekten `--system-site-packages` ile oluşturulduğundan ve etkin olduğundan emin olun.

2) Uygulamayı başlatın ve `/health` endpoint'ini kontrol edin:

```bash
python app.py
# veya üretim için gunicorn kullanımı (tek worker önerilir çünkü kamera tek bir process tarafından kullanılmalı):
# gunicorn --chdir /home/furkanblt/Documents/Transmind/Transmind-PI --workers 1 --bind unix:/run/transmind.sock app:app
```

Tarayıcıdan veya curl ile kontrol:

```bash
curl -i http://127.0.0.1:5000/health
```

Başarılıysa `OK` ve 200 dönecektir.

## Systemd servis (`transmind-pi.service`) — Gunicorn yolu ve servis hatası düzeltmesi

Bu bölüm, sık karşılaşılan bir problem olan systemd servisinin `ExecStart` içinde yanlış Gunicorn yolu gösterilmesi ve sonucunda `status=203/EXEC (No such file or directory)` hatası almayı nasıl düzelteceğinizi açıklar.

Sorun özeti:
- Sistem üzerindeki `gunicorn` paketiniz sistem Python'una (`/usr/bin/gunicorn`) kurulmuş olabilir.
- Ancak `transmind-pi.service` dosyanız `ExecStart` içinde proje sanal ortamınızın içindeki yolu (`/home/transmind/Desktop/Transmind-PI/TM/bin/gunicorn`) gösteriyorsa ve o dosya orada yoksa, systemd servisi başlamaz.

Aşağıdaki adımlarla problemi tespit edip düzeltebilirsiniz.

1) Gunicorn'un hangi yolda olduğunu kontrol edin

```bash
# Sistemdeki gunicorn'un yolunu öğrenin
which gunicorn || command -v gunicorn
# Örnek çıktı: /usr/bin/gunicorn
```

2) `transmind-pi.service` dosyasını açın ve `ExecStart` satırını düzeltin

- Eğer tercih edeceğiniz Gunicorn sistemdekiyse (`/usr/bin/gunicorn`), `ExecStart` satırını şu şekilde güncelleyin:

```ini
# /etc/systemd/system/transmind-pi.service içindeki ExecStart örneği
ExecStart=/usr/bin/gunicorn --workers 1 --bind unix:/home/transmind/Desktop/Transmind-PI/app.sock app:app
```

- Alternatif olarak sanal ortam içindeki gunicorn'u kullanmak isterseniz (önerilen yol: tüm runtime bağımlılıklarını venv içinde tutmak), önce venv'yi etkinleştirip `pip install gunicorn` çalıştırın:

```bash
source /home/transmind/Desktop/Transmind-PI/TM/bin/activate
pip install gunicorn
# ardından ExecStart'ı venv içindeki gunicorn'a işaret edecek şekilde ayarlayın:
ExecStart=/home/transmind/Desktop/Transmind-PI/TM/bin/gunicorn --workers 1 --bind unix:/home/transmind/Desktop/Transmind-PI/app.sock app:app
```

Not: Kamera donanımı tek bir process tarafından kullanılmalıdır; bu yüzden `--workers 1` kullanmanız şiddetle tavsiye edilir. Eğer önceki servis dosyanız `--workers 3` gibi bir değer içeriyorsa bunu 1'e çekin.

3) Systemd'yi yeniden yükleyin ve servisi yeniden başlatın

```bash
# systemd değişiklikleri yükle
sudo systemctl daemon-reload
# servisi yeniden başlat
sudo systemctl restart transmind-pi.service
# servisin durumunu kontrol edin
sudo systemctl status transmind-pi.service
```

4) Hala hata alırsanız loglara bakın

```bash
# Servis günlüklerini takip edin
sudo journalctl -u transmind-pi.service -f
```

5) Ek notlar ve olası çözümler
- Eğer `status=203/EXEC` hatası devam ediyorsa, `ExecStart` yolunun gerçekten var olduğundan ve dosyanın çalıştırılabilir olduğundan emin olun (`ls -l /usr/bin/gunicorn`).
- Socket izinleri veya ownership sorunları `502`/`permission denied` sorunlarına yol açabilir. Nginx ile unix socket üzerinden konuşuyorsanız, systemd unit'ında `Group=www-data` veya uygun izinleri ayarlamayı düşünün.
- Sistem genelindeki pip paketleri görüldüğü için `pip install` komutunun "Requirement already satisfied" demesi normaldir; ancak bu durumda systemd servisi aynı pip ortamını kullanmıyor olabilir.

## Hızlı Komut Özeti

```bash
# 1. Mevcut ortamı kapat & sil
deactivate
rm -rf TM

# 2. Yeni ortam oluştur
python3 -m venv TM --system-site-packages

# 3. Etkinleştir ve bağımlılıkları kur
source TM/bin/activate
pip install --upgrade pip
pip install flask picamera2 gunicorn

# 4. Doğrula
python -c "import libcamera; print('libcamera bulundu')"
python app.py
# veya
# gunicorn --chdir /home/furkanblt/Documents/Transmind/Transmind-PI --workers 1 --bind unix:/run/transmind.sock app:app
```

---

Eğer rehberde değiştirmemi istediğiniz başka bir şey veya eklemek istediğiniz ayrıntı varsa söyleyin; hemen güncellerim.
