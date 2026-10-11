## Tushuncha

Siz ilovani `python3 app.py &` bilan ishga tushirdingiz va u ishlayapti. Keyin savollar boshlanadi: server qayta yuklansa, ilovani kim ishga tushiradi? Ilova yiqilsa, kim qayta ko'taradi? Uning loglari qayerda? U qaysi user nomidan ishlayapti? Bularning barchasiga Ubuntu'da bitta javob bor — **systemd**.

systemd — tizimdagi birinchi process (PID 1) va **servis menejeri**. U boot paytida servislarni to'g'ri tartibda ishga tushiradi, ularning holatini kuzatadi, yiqilganini qayta ishga tushiradi, chiqishini jurnalga yozadi va har birini o'z user'i hamda cheklovlari bilan ishlatadi. Siz unga nima kerakligini **unit fayl**da tasvirlaysiz — qolganini u o'zi qiladi.

Bu deklarativ yondashuv: "qanday ishga tushirish" skriptini emas, "nima bo'lishi kerak"ni yozasiz — qaysi buyruq, qaysi user, qachon, yiqilsa nima qilish. Bu g'oya keyinchalik Docker Compose, Kubernetes va Ansible'da ham uchraydi.

## Qanday ishlaydi

Unit fayl — INI ko'rinishidagi matn. Servislar uchun uning uchta bo'limi bor:

```text
[Unit]                         — tavsif va bog'liqliklar
Description=Tick demo
Wants=network-online.target    — "tarmoq tayyor bo'lishini xohlayman"
After=network-online.target    — "va undan KEYIN ishga tush"

[Service]                      — qanday ishga tushirish
User=worker                    — root emas!
ExecStart=/usr/local/bin/tick.sh
Restart=on-failure
RestartSec=2

[Install]                      — enable qilinganda qayerga ulanadi
WantedBy=multi-user.target     — oddiy (grafik bo'lmagan) boot holati
```

Fayllar ikki joyda turadi: paketlar o'rnatganlari — `/usr/lib/systemd/system/`, siz yozganlar va o'zgartirishlar — `/etc/systemd/system/`. Bir xil nomli fayl bo'lsa, `/etc` ustun turadi. Paket fayliga to'g'ridan-to'g'ri tegmang: `systemctl edit nginx` qo'shimcha "drop-in" fayl yaratadi va paket yangilanganda o'zgarishingiz yo'qolmaydi.

`start` va `enable` farqi: `start` servisni **hozir** ishga tushiradi; `enable` esa `multi-user.target.wants/` papkasida symlink yaratadi, shunda servis **har boot'da** ishga tushadi. `enable --now` ikkalasini birga qiladi.

systemd unit fayllarni xotirada saqlaydi. Faylni o'zgartirgach `systemctl daemon-reload` qilmasangiz, eski versiya ishlayveradi — `status` buni ogohlantirish bilan aytadi.

`After=` faqat **tartib**ni belgilaydi, `network-online.target` ni ishga tushirishni talab qilmaydi. Shuning uchun u `Wants=` bilan juft yoziladi.

`Restart=on-failure` servisni "nosog'lom" tugaganda qayta ishga tushiradi: noldan farqli exit code, SIGKILL kabi signal, timeout. SIGTERM bilan toza to'xtatish esa xato hisoblanmaydi — tekshiruvda `kill -9` dan keyin servis qayta ko'tarildi, oddiy `kill` dan keyin esa `inactive` bo'lib qoldi. Cheksiz qayta urinishga qarshi limit ham bor: standart holatda 10 soniyada 5 ta start (`StartLimitBurst=5`, `StartLimitIntervalSec=10s`), undan keyin systemd servisni `failed` holatida qoldiradi.

## Buyruqlar

Natijalar Ubuntu 24.04 + systemd 255 konteynerida, yuqoridagi `tick.service` bilan olingan.

```bash
systemctl daemon-reload && systemctl enable --now tick
```
```text
Created symlink /etc/systemd/system/multi-user.target.wants/tick.service → /etc/systemd/system/tick.service.
```
`enable` aslida shu symlinkni yaratadi.

```bash
systemctl status tick --no-pager
```
```text
● tick.service - Tick demo
     Loaded: loaded (/etc/systemd/system/tick.service; enabled; preset: enabled)
     Active: active (running) since Sun 2026-10-11 10:38:27 UTC; 3s ago
   Main PID: 123 (tick.sh)
      Tasks: 2 (limit: 2700)
     Memory: 712.0K (peak: 1.1M)
...
Oct 11 10:38:27 7de0d1773d52 systemd[1]: Started tick.service - Tick demo.
```
`Loaded` — fayl qayerda va enabled'mi, `Active` — holati va qachondan beri, pastda — oxirgi log qatorlari.

```bash
kill -9 $(systemctl show -p MainPID --value tick)
journalctl -u tick -n 30 --no-pager | grep -E "Main process|Scheduled restart|Started"
```
```text
systemd[1]: tick.service: Main process exited, code=killed, status=9/KILL
systemd[1]: tick.service: Scheduled restart job, restart counter is at 1.
systemd[1]: Started tick.service - Tick demo.
```
`Restart=on-failure` ishladi: SIGKILL → 2 soniyadan keyin qayta ishga tushdi.

```bash
kill $(systemctl show -p MainPID --value tick); systemctl is-active tick
```
```text
inactive
```
SIGTERM — toza chiqish, `on-failure` qayta ishga tushirmadi (`Restart=always` bo'lsa tushirardi).

```bash
systemctl show -p NRestarts,Restart,StartLimitBurst,StartLimitIntervalUSec tick
```
```text
Restart=on-failure
NRestarts=0
StartLimitIntervalUSec=10s
StartLimitBurst=5
```
Amaldagi qiymatlar, shu jumladan siz yozmagan standartlar.

```bash
systemctl status tick --no-pager | grep -i warning
```
```text
Warning: The unit file, source configuration file or drop-ins of tick.service changed on disk. Run 'systemctl daemon-reload' to reload units.
```
Faylni o'zgartirib `daemon-reload` qilmaganingizda shunday ogohlantirish chiqadi.

```bash
systemctl reload tick
```
```text
Failed to reload tick.service: Job type reload is not applicable for unit tick.service.
```
`reload` faqat unit'da `ExecReload=` bo'lsa ishlaydi; aks holda `restart`.

```bash
systemctl cat tick | head -3
systemctl list-units --failed
```
```text
# /etc/systemd/system/tick.service
[Unit]
Description=Tick demo
```
`cat` — amalda qaysi fayl(lar) ishlatilayotganini drop-in'lar bilan birga ko'rsatadi; `--failed` — yiqilgan unit'lar.

```bash
systemd-analyze verify /etc/systemd/system/tick.service
```
Sintaksis va ma'lum muammolarni tekshiradi; xato bo'lmasa hech narsa chiqarmaydi. Tekshiruvda nisbiy `ExecStart` li faylga ham xato bermadi — demak u har bir xatoni ushlamaydi, `status` va jurnal baribir kerak.

## Odatiy xatolar

- **`daemon-reload` ni unutish.** Belgi: unit o'zgartirildi, `restart` qilindi, lekin eski xatti-harakat. Sabab: systemd eski versiyani xotirada saqlaydi. To'g'ri usul: har o'zgarishdan keyin `systemctl daemon-reload`, keyin `restart`.
- **`start` qilib, `enable` ni unutish.** Belgi: reboot'dan keyin servis o'chiq. Sabab: boot'da ishga tushirish uchun symlink yo'q. To'g'ri usul: `systemctl enable --now`, `is-enabled` bilan tekshirish.
- **`After=network-online.target` ni `Wants=` siz yozish.** Belgi: boot'da servis tarmoq tayyor bo'lmasdan ishga tushib yiqiladi. Sabab: `After=` faqat tartib, target'ni tortib kelmaydi. To'g'ri usul: ikkalasini birga yozing.
- **Shell muhitiga tayanish.** Belgi: qo'lda ishlaydi, servis sifatida `command not found` yoki `KeyError`. Sabab: systemd `~/.bashrc` ni o'qimaydi, `PATH` va o'zgaruvchilar boshqacha. To'g'ri usul: `ExecStart` da to'liq yo'l, o'zgaruvchilar `Environment=` yoki `EnvironmentFile=` orqali.
- **`Start request repeated too quickly.`** Belgi: jurnalda shu qator, servis `failed`, qayta urinmaydi. Sabab: 10 soniyada 5 martadan ko'p yiqildi. To'g'ri usul: `journalctl -u servis` dan asl xatoni toping, tuzating, keyin `systemctl reset-failed servis`.

## Intervyuda

**Savol:** `systemctl enable` va `systemctl start` farqi nima, servis yiqilganda qayta ishga tushishini qanday ta'minlaysiz?

**Namunaviy javob:** `start` servisni hozir ishga tushiradi, `enable` esa uni target'ga (odatda `multi-user.target`) symlink orqali bog'laydi, shunda u har boot'da ishga tushadi; ko'pincha `enable --now` bilan ikkalasini birga qilaman. Yiqilganda tiklanish uchun `[Service]` da `Restart=on-failure` va `RestartSec=` qo'yaman — bu xato kodi yoki signal bilan tugashda qayta ishga tushiradi, lekin oddiy `systemctl stop` ni hurmat qiladi. Start limitini ham hisobga olaman: servis tez-tez yiqilsa systemd to'xtaydi, shunda sababni jurnaldan qidiraman.
