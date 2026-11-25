# Xiaomi AX9000 (RA70) Global to China ROM (China Developer 1.0.140) — One-Click Migration Tool
### The First Open-Source (MIT) Standalone Utility for Global → China Developer 1.0.140 Conversion • Qualcomm Secure Boot Bypass (`atf=1`) • Dual-Boot Safe • Hardware NAND Verification

[English](#english) | [Türkçe](#türkçe)

---

<a name="english"></a>
## English (EN)

> **Convert Xiaomi Router AX9000 Global / International (EU) to Official China Developer Firmware (1.0.140) in One Click.**
>
> For years, Global **Xiaomi AX9000 (Model: RA70)** owners who tried flashing China ROMs ran into Qualcomm Secure Boot (RSA-2048 MBN signature verification in U-Boot), causing the router to halt on a solid orange LED. This project is the **first open-source, MIT-licensed, standalone Windows tool** that automates the complete **Global → China Developer 1.0.140** migration safely — without modifying a single bootloader partition.

---

### Global Firmware vs. China Developer 1.0.140 Comparison

| Feature | Global / EU Firmware (`3.0.40_INT`) | China Developer (`1.0.140 Dev`) |
| :--- | :--- | :--- |
| **Wi-Fi TX Power** | Capped by EU / ETSI limits (~20–23 dBm) | Full Qualcomm hardware power up to **30 dBm (1000 mW)** (`CountryCode=CN`) |
| **5.2 GHz (5G Game, Ch 36–64)** | Restricted channels / power | Full **160 MHz** channel width (**4804 Mbps**) |
| **5.8 GHz (UNII-3, Ch 149–165)** | Restricted power | Full **80 MHz** channel width (**2402 Mbps**) at 30 dBm |
| **Native Docker Engine** | ❌ Not available | ✅ Official built-in Docker support (AdGuard Home, Portainer, Tailscale, FileBrowser, etc.) |
| **Permanent Root SSH** | ❌ Locked | ✅ One-click Dropbear SSH (Port 22) persistence |
| **China Xiaomi Mesh** | ❌ Incompatible | ✅ Full Xiaomi Mesh compatibility with CN routers |

---

### How It Works & Why Global AX9000 Normally Refuses China ROM

Global AX9000 units enforce **Qualcomm Secure Boot** inside U-Boot (`0:APPSBL`), rejecting China-signed kernels and leaving the router stuck on an orange LED. Rather than risking a brick by flashing a modified bootloader, this tool:

1. **Never Touches Bootloaders:** Primary bootloader partitions (`0:SBL1`, `0:APPSBL` / U-Boot, `0:CDT`, `0:MIBIB`) remain 100% untouched.
2. **Applies Official U-Boot Bypass (`atf=1`):** Sets `nvram set atf=1` and `boot_wait=on`, instructing Qualcomm's stock U-Boot to bypass RSA signature checks and boot the official China Developer 1.0.140 kernel cleanly.
3. **Dual-Boot Partition Isolation:** AX9000 has two independent rootfs slots (`mtd21` / `rootfs` and `mtd22` / `rootfs_1`). The tool parses `/proc/cmdline` and `/proc/mtd`, leaves the active working slot untouched, and flashes exclusively to the idle slot.
4. **Strict Hardware Model Check:** Validates `/proc/xiaoqiang/model` against exact regex `^RA70$` so incompatible routers are rejected immediately.
5. **Automated Host PC Backups:** Downloads and verifies full `NVRAM` and `BData` configuration backups to timestamped files in the local `Yedekler/` directory before any NAND write.
6. **Post-Flash Hardware Read-Back Verification:** Checks `ubiformat` exit status (`$? == 0`), attaches the newly written MTD via `ubiattach -m <mtd> -d 2`, verifies UBI volume count and `kernel` + `ubi_rootfs` presence with `ubinfo`, and detaches cleanly. If verification fails, the boot slot flag is **never switched**.
7. **Live Post-Reboot Verification:** Monitors the router reboot and confirms that the active running firmware version is `1.0.140`.

---

### Prerequisites
- Windows 10 / 11 (64-bit).
- PC connected to the Xiaomi AX9000 via **Ethernet LAN cable** (recommended) or Wi-Fi.
- Router reachable at `192.168.31.1` with an admin password already set.

### Quick Start (Usage)
1. Download **`AX9000_Cin_Dev_Gecis_Araci.exe`** from [Releases](https://github.com/Leekin2/AX9000-China-Dev/releases) (contains the official 44 MB `root_1.0.140.ubi` payload embedded — MD5 `dabb7639c015e4e93457e9e193315a27`).
2. Run the `.exe` and select **`[1]`** to migrate to China Developer 1.0.140.
3. Confirm the factory settings reset prompt (`E` / `Y`), enter your router IP (`192.168.31.1`) and Web Admin password.
4. Wait 2–3 minutes while the router flashes, verifies NAND, and reboots until the LEDs turn steady blue.
5. Open `http://192.168.31.1` (use Chrome/Edge Translate for English/Turkish), complete the 1-minute Wi-Fi setup, and optionally run **`[2]`** in the tool to enable permanent Root SSH.

---

### FAQ (Frequently Asked Questions)
- **Can I run it from Python source instead of the `.exe`?**
  Yes! Install `pip install -r requirements.txt`, place `root_1.0.140.ubi` next to `ax9000_flash_tool.py`, and run `python ax9000_flash_tool.py`.
- **Will my existing Wi-Fi settings be kept?**
  No. Because Global and China firmware configurations conflict, `flag_format_overlay=1` resets user settings cleanly to prevent bootloops. Your original NVRAM/BData is backed up to `Yedekler/` on your PC.
- **How do I translate the Chinese web interface?**
  Right-click anywhere on `http://192.168.31.1` in Chrome or Edge and choose **Translate**.

---

<a name="türkçe"></a>
## Türkçe (TR)

> **Xiaomi Router AX9000 (Model: RA70) Global'den Çin Geliştirici ROM'una (1.0.140 Develop) Tek Tıkla Geçiş Aracı.**
>
> Yıllardır Global **Xiaomi AX9000 (RA70)** cihazını Çin yazılımına geçirmek isteyen kullanıcılar, U-Boot içindeki **Qualcomm Secure Boot (RSA-2048)** imzasına takılıp sabit turuncu ışık sorunu yaşıyordu. Bu proje, ön yükleyiciye (bootloader) hiç dokunmadan Global → Çin Geliştirici 1.0.140 geçişini tek tıkla ve donanımsal doğrulamayla yapan **dünyadaki ilk açık kaynaklı (MIT lisanslı) bağımsız Windows aracıdır.**

---

### Global Sürüm vs. Çin Geliştirici 1.0.140 Karşılaştırması

| Özellik | Global / Avrupa ROM (`3.0.40_INT`) | Çin Geliştirici ROM (`1.0.140 Dev`) |
| :--- | :--- | :--- |
| **Wi-Fi Sinyal Gücü (TX)** | Avrupa CE / ETSI kısıtlamalı (~20–23 dBm) | Tam donanım gücü **30 dBm (1000 mW)** (`CountryCode=CN`) |
| **5.2 GHz (5G Game, Kanal 36–64)** | Kısıtlı güç / kanal | Tam **160 MHz** kanal genişliği (**4804 Mbps**) |
| **5.8 GHz (UNII-3, Kanal 149–165)** | Kısıtlı güç | Tam **80 MHz** kanal genişliği (**2402 Mbps**, 30 dBm) |
| **Resmi Dahili Docker** | ❌ Yok | ✅ Resmi Docker motoru (AdGuard Home, Portainer, Tailscale, FileBrowser vb.) |
| **Kalıcı Root SSH** | ❌ Kilitli | ✅ Tek tıkla kalıcı Dropbear SSH (Port 22) |
| **Çin Xiaomi Mesh** | ❌ Uyumsuz | ✅ Çin Xiaomi yönlendiricileriyle tam Mesh uyumu |

---

### Donanım Güvenliği ve Anti-Brick Mimarisi

Bu araç, standart tek satırlık scriptlerin aksine çok katmanlı savunma ve doğrulama kontrolleriyle çalışır:

* **Ön Yükleyicilere (Bootloader) Asla Dokunulmaz:** `0:SBL1`, `0:APPSBL` (U-Boot), `0:CDT` ve `0:MIBIB` bölümlerine hiçbir yazma işlemi yapılmaz.
* **Qualcomm Secure Boot Baypası (`atf=1`):** Global AX9000'in U-Boot ön yükleyicisindeki resmi `atf=1` parametresini NVRAM'e işleyerek imzasız Çin çekirdeğinin bootloader değiştirilmeden güvenle açılmasını sağlar.
* **Çift Yuva (Dual-Boot) Yalıtımı:** AX9000'deki iki sistem yuvasından (`mtd21` / `rootfs` ve `mtd22` / `rootfs_1`) aktif çalışan yuvaya dokunmaz; yalnızca boşta duran 2. yuvaya yazar.
* **Sıkı Donanım Model Doğrulaması:** `/proc/xiaoqiang/model` çıktısını tam `^RA70$` regex'iyle doğrular; farklı bir cihazda çalışmayı anında reddeder.
* **Bilgisayara Otomatik Zaman Damgalı Yedek:** Yazma öncesinde modemin tüm `NVRAM` ve `BData` ayarlarını bilgisayarınızdaki `Yedekler/` klasörüne indirir ve dosya boyutlarını doğrular.
* **NAND Geri Okuma ve UBI Doğrulaması:** `ubiformat` çıkış kodunu (`$? == 0`) denetler, ardından yazılan bölümü `ubiattach -m <mtd> -d 2` ile bağlayıp `ubinfo` üzerinden `kernel` ve `ubi_rootfs` birimlerinin sağlamlığını teyit eder. Doğrulama geçilmezse açılış yuvası bayrağı **asla değiştirilmez**.
* **Canlı Yeniden Başlatma ve Sürüm Teyidi:** Modem yeniden başladıktan sonra `192.168.31.1` üzerinden aktif açılan sürümün `1.0.140` olduğunu canlı olarak doğrular.

---

### Gereksinimler ve Adım Adım Kullanım
1. Bilgisayarı AX9000 modeme **Ethernet kablosu** (önerilen) veya Wi-Fi ile bağlayın (`192.168.31.1` erişilebilir olsun).
2. [Releases](https://github.com/Leekin2/AX9000-China-Dev/releases) bölümünden **`AX9000_Cin_Dev_Gecis_Araci.exe`** dosyasını indirin (resmi 44 MB'lık `root_1.0.140.ubi` dosyası içine gömülüdür, ekstra indirme gerekmez).
3. Programı çalıştırıp menüden **`[1]`** seçeneğini seçin, ayarların sıfırlanacağını onaylayın (`E`), modem IP (`192.168.31.1`) ve Web Yönetici Şifrenizi girin.
4. Program tüm adımları otomatik tamamlayıp modemi yeniden başlatacaktır. Ön LED'ler 2–3 dakika turuncu yanıp **sabit maviye** dönene kadar cihazın fişini çekmeyin.
5. Işıklar maviye döndüğünde `http://192.168.31.1` adresine girip yeni Wi-Fi adınızı belirleyin (Chrome/Edge ile sağ tıklayıp *Türkçe diline çevir* diyebilirsiniz).
6. İsterseniz araçtan **`[2]`** seçeneğiyle kalıcı Root SSH erişimini aktif edebilirsiniz (ilk kurulumdan sonra `passwd` ile kendi güçlü şifrenizi belirlemeniz önerilir).

---

### Sorumluluk Reddi & Lisans (Disclaimer & License)
Bu yazılım araştırma ve topluluk paylaşımı amacıyla **MIT Lisansı** altında açık kaynak olarak sunulmuştur. Çok katmanlı güvenlik denetimleri barındırmasına rağmen, yazılımın kullanımından doğabilecek her türlü sorumluluk kullanıcıya aittir.

---
**Anahtar Kelimeler / Keywords:** `Xiaomi AX9000 Global to China ROM`, `Xiaomi AX9000 Globalden Çin ROMuna Geçiş`, `RA70 China Developer 1.0.140`, `AX9000 Qualcomm Secure Boot atf=1`, `AX9000 Docker`, `AX9000 1000mW 30dBm`, `AX9000 SSH Unlock`
