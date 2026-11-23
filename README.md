# Xiaomi AX9000 (RA70) Global to China Developer 1.0.140 Migration Tool
### Qualcomm Secure Boot Verified • Dual-Boot Partition Isolation • Hardware Verification

[English](#english) | [Türkçe](#türkçe)

---

<a name="english"></a>
## English (EN)

A multi-layer verification migration and unlocking utility for the **Xiaomi Router AX9000 (Model: RA70)**. Engineered with defensive dual-boot partition isolation and hardware read-back checks to transition Global/International edition devices to official **China Developer Firmware (1.0.140 Develop)**, enabling full Wi-Fi transmission power, official Docker container engine support, and persistent root SSH access.

---

### Features & Advantages of China Developer 1.0.140
1. **Unrestricted Wi-Fi Transmission Power:**
   - Unlocks full Qualcomm hardware TX power up to **1000 mW (30 dBm)** (removes European CE / ETSI transmit caps).
   - Unlocks full **160 MHz** dynamic channel selection (DFS) on all 5GHz bands.
2. **Native Docker Engine Support:**
   - Run containers directly on the router (e.g., AdGuard Home, Home Assistant, Portainer, Speedtest-Tracker) utilizing USB 3.0 / external SSD storage.
3. **Cross-Region Mesh Compatibility:**
   - Seamlessly pairs in Xiaomi Mesh topology with China-exclusive routers.
4. **Permanent Root Shell Access:**
   - One-click Dropbear SSH (Port 22) and Telnet (Port 23) daemon setup with persistence across reboots.

---

### Anti-Brick & Hardware Safety Architecture

Unlike naive flashing scripts, this utility implements enterprise-grade defensive checks:

* **Zero Bootloader Exposure:**
  Never touches, writes, or modifies primary bootloader partitions (`0:SBL1`, `0:APPSBL` / U-Boot, `0:CDT`, `0:MIBIB`).
* **Qualcomm Secure Boot Bypass (`atf=1`):**
  Global AX9000 U-Boot checks Qualcomm RSA-2048 MBN signatures by default. The tool sets the official undocumented Qualcomm evaluation flag `nvram set atf=1` and `bdata set boot_wait=on`, allowing U-Boot to boot unsigned China developer kernels safely without modifying bootloader code.
* **Dual-Boot (Dual-Slot) Allocation:**
  Xiaomi AX9000 utilizes dual system partitions: `mtd21` (`rootfs` / Slot 0) and `mtd22` (`rootfs_1` / Slot 1). The tool dynamically queries `/proc/cmdline`. The active slot is **never overwritten**; the firmware payload is written exclusively to the idle secondary slot.
* **Strict Hardware Model Validation (Exact Regex):**
  Validates `/proc/xiaoqiang/model` using strict boundary regex (`^RA70$`). Prevents flashing onto incompatible hardware variants.
* **Automated Host PC Backups:**
  Prior to modifying any partition, full NVRAM and BData tables are downloaded and verified directly onto the operator's PC inside the `Yedekler/` directory.
* **Post-Flash Hardware Read-Back Verification (UBI Inspection):**
  After `ubiformat` completes, the tool inspects the exit code (`$? == 0`) and performs a hardware read-back check: it dynamically attaches the written partition using `ubiattach -m <mtd> -d 2`, verifies volume allocation (`ubinfo /dev/ubi2`), and cleanly detaches it (`ubidetach`). Boot flags are updated **only** if the written partition passes 100% NAND volume integrity checks.

---

### Prerequisites & Requirements
- Windows 10 / 11 (64-bit).
- Computer connected to the Xiaomi AX9000 via **Ethernet LAN cable** (recommended) or Wi-Fi.
- Default router gateway reachable at `192.168.31.1`.
- Router Web Admin password configured (if router is fresh out-of-box, complete the 1-minute initial setup in browser first).

---

### How to Use

1. Run `AX9000_Cin_Dev_Gecis_Araci.exe` as Administrator.
2. Select **[1] Flash China Developer Firmware (1.0.140 Dev)**:
   - Accept the configuration reset prompt by typing `E` or `Y`.
   - Enter your router Web Management password.
3. The tool executes automatically:
   - Validates embedded 44 MB payload MD5 (`dabb7639c015e4e93457e9e193315a27`).
   - Obtains STOK via LuCI web session and triggers port 19553 Mesh timezone exploit.
   - Spawns lightweight single-file HTTP server on port 8998 to transfer the UBI image.
   - Downloads NVRAM/BData configuration backup to local PC `Yedekler/` folder.
   - Formats idle slot and flashes `root_1.0.140.ubi`.
   - Validates NAND flash integrity with `ubiattach` / `ubinfo`.
   - Sets `atf=1`, `CountryCode=CN`, and points `flag_boot_rootfs` to the new slot.
   - Triggers reboot.
4. **Reboot Cycle:** The router's front LEDs will glow orange for 2–3 minutes while provisioning. **Do NOT unplug power until both system and internet LEDs turn steady blue.**
5. Once blue, open `http://192.168.31.1` in your web browser to access the China Developer interface.
6. Run the tool again and choose **[2] Setup Permanent Root SSH** to activate persistent SSH access (`root` / `root`).

---

<a name="türkçe"></a>
## Türkçe (TR)

**Xiaomi Router AX9000 (Model: RA70)** Global / Uluslararası sürüm cihazları, çift yuva yalıtımı ve donanımsal NAND geri okuma denetimleriyle donanımsal çökme ihtimalini minimize ederek resmi **Çin Geliştirici Yazılımına (1.0.140 Develop)** geçiren ve kalıcı root SSH yetkisi kazandıran geçiş aracı.

---

### Çin Geliştirici (1.0.140 Dev) Sürümünün Avantajları
1. **Avrupa Wi-Fi Sinyal Gücü Kısıtlamaları Kalkar:**
   - TX Çıkış Gücü tam donanım kapasitesi olan **1000 mW (30 dBm)** seviyesine ulaşır (Avrupa CE / ETSI kısıtlamaları kalkar).
   - Tüm 5GHz bantlarında **160 MHz** dinamik kanal desteği tam performansla açılır.
2. **Resmi Dahili Docker Desteği:**
   - Modemin USB 3.0 / harici SSD portu üzerinden AdGuard Home, Portainer, Home Assistant, Speedtest-Tracker gibi konteynerleri doğrudan modem üzerinde çalıştırabilirsiniz.
3. **Çin Xiaomi Modelleriyle Mesh Uyumluluğu:**
   - Çin iç pazarına özel Xiaomi modelleriyle sorunsuz kablosuz/kablolu Mesh ağı kurulabilir.
4. **Kalıcı Root Shell Erişimi:**
   - Yeniden başlatmalarda silinmeyen kalıcı Dropbear SSH (Port 22) ve Telnet (Port 23) erişimi tek tıkla açılır.

---

### Anti-Brick & Donanım Güvenlik Mimarisi

Bu araç, standart betiklerin aksine çok katmanlı savunma ve doğrulama denetimlerine sahiptir:

* **Ön Yükleyicilere (Bootloader) Asla Dokunulmaz:**
  Cihazın kritik ön yükleyici bölümlerine (`0:SBL1`, `0:APPSBL` / U-Boot, `0:CDT`, `0:MIBIB`) kesinlikle yazma yapılmaz.
* **Qualcomm Secure Boot Baypası (`atf=1`):**
  Global AX9000 U-Boot ön yükleyicisi normal şartlarda RSA-2048 MBN imza denetimi yapar. Araç, Qualcomm U-Boot'un resmi `atf=1` hata ayıklama parametresini NVRAM ve BData'ya otomatik işleyerek imzasız Çin çekirdeğinin U-Boot tarafından güvenle açılmasını sağlar.
* **Çift Yuva (Dual-Boot) Emniyeti:**
  AX9000 cihazı çift sistem yuvasına sahiptir (`mtd21`: Slot 0, `mtd22`: Slot 1). Araç `/proc/cmdline` üzerinden aktif çalışan yuvayı tespit eder. **Aktif yuvaya kesinlikle dokunulmaz**, yazma işlemi yalnızca boşta duran 2. yuvaya yapılır.
* **Sıkı Model Doğrulaması (Tam Eşleşme Regex):**
  `/proc/xiaoqiang/model` sorgusu yapılarak donanım modelinin tam `RA70` olduğu doğrulanır. Benzer veya uyumsuz modellerde işlem anında durdurulur.
* **Bilgisayara Otomatik Yapılandırma Yedeği:**
  NAND belleğe herhangi bir komut gönderilmeden önce, modemin tüm NVRAM ve BData tabloları operatörün bilgisayarında `Yedekler/` klasörüne dosya boyutu teyit edilerek kaydedilir.
* **Donanım Geri Okuma ve UBI Doğrulaması (NAND Verification):**
  `ubiformat` komutunun çıkış kodu (`$? == 0`) denetlenir. Ardından hedef yuvaya dinamik olarak UBI bağlanır (`ubiattach -m <mtd> -d 2`), dosya sistemi bölümleri (`ubinfo`) denetlenir ve temizce ayrılır (`ubidetach`). Yazma işlemi %100 kusursuz değilse açılış yuvası bayrağı **asla değiştirilmez**.

---

### Gereksinimler
- 64-bit Windows 10 veya Windows 11.
- Bilgisayarın modeme **Ethernet (Ağ Kablosu)** veya Wi-Fi ile bağlı olması.
- Varsayılan ağ geçidi: `192.168.31.1`.
- Modem Web Arayüz Şifresi (Modem yeni kutudan çıktıysa tarayıcıda 1 dakikalık ilk kurulumu tamamlayıp bir şifre belirleyin).

---

### Adım Adım Kullanım

1. `AX9000_Cin_Dev_Gecis_Araci.exe` dosyasını çalıştırın.
2. Menüden **[1] Modemi Çin Geliştirici (1.0.140 Develop) Sürümüne Yükselt** seçeneğini seçin:
   - Ayarların sıfırlanacağı bilgilendirmesini onaylamak için `E` yazıp Enter'a basın.
   - Modem IP adresini (Varsayılan: `192.168.31.1`) ve Web Yönetici Şifrenizi girin.
3. Araç tüm adımları otomatik olarak tamamlayacaktır:
   - Gömülü 44 MB'lık UBI dosyasının MD5 değerini doğrular.
   - Mesh güvenlik açığı (Port 19553) ile Telnet erişimini açar.
   - Yerel bilgisayarınızda `Yedekler/` klasörüne NVRAM ve BData yedeğini indirir.
   - Boşta duran yuvanın tespitini yapar ve `root_1.0.140.ubi` dosyasını yazar.
   - `ubiattach` ve `ubinfo` ile donanımsal dosya sistemi sağlamlığını teyit eder.
   - `atf=1` baypasını ve Çin NVRAM parametrelerini işler, modemi yeniden başlatır.
4. **Yeniden Başlama:** Modemin ön LED'leri 2-3 dakika turuncu yanacaktır. **Işıklar maviye dönene kadar cihazın fişini ASLA çekmeyin.**
5. Işıklar maviye döndüğünde tarayıcınızdan `192.168.31.1` adresine girerek yeni Wi-Fi adınızı belirleyin.
6. Ardından araç menüsünden **[2] Kalıcı Root SSH Kur** seçeneğini seçerek modeme `root` / `root` yetkisi kazandırabilirsiniz.

---

### Sorumluluk Reddi (Disclaimer)
Bu yazılım araştırma ve hobi amaçlı hazırlanmıştır. Bootloader koruma mekanizmaları ve çift yuva emniyeti barındırmasına rağmen, yazılımın kullanımından doğabilecek her türlü donanımsal veya yazılımsal sorumluluk kullanıcıya aittir.

---
### Lisans (License)
MIT License. Open-source for the Xiaomi AX9000 community.
