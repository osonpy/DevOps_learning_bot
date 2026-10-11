## Tushuncha

Incident paytidagi birinchi savol deyarli doim bir xil: **"Loglarda nima bor?"** Servis nima uchun yiqildi, kim SSH orqali kirishga urindi, disk qachon to'la boshladi — bularning hammasi loglarda yozilgan. Logni tez topa olish va o'qiy olish juniorni foydali qiladigan eng muhim ko'nikmalardan biri.

Ubuntu serverda loglar ikki joyda yashaydi. Birinchisi — **journald**, systemd'ning jurnali: barcha servislar chiqishi, kernel xabarlari, boot jarayoni bitta indekslangan bazada saqlanadi va `journalctl` bilan o'qiladi. Ikkinchisi — an'anaviy **matnli loglar** `/var/log` ichida: `syslog`, `auth.log`, `kern.log` va ilovalarning o'z fayllari (`/var/log/nginx/access.log`). Ubuntu'da rsyslog journald'dan xabarlarni olib, shu fayllarga ham yozadi, shuning uchun ko'p narsani ikki joyda topasiz.

Loglarning qorong'i tomoni ham bor: ular o'sadi. Nazoratsiz log bir necha hafta yoki oyda diskni to'ldiradi va servisni yiqitadi. Buning oldini **logrotate** oladi: loglarni vaqti-vaqti bilan "aylantiradi" — eskisini qayta nomlaydi, siqadi va belgilangan sondan eskilarini o'chiradi.

## Qanday ishlaydi

```text
 servis stdout/stderr ─┐
 kernel xabarlari ─────┼──► journald ──► /var/log/journal/  (binary, indeksli)   ← journalctl
 syslog() / logger ────┘        │
                                └──► rsyslog ──► /var/log/syslog, auth.log, ...  (matn) ← tail, grep
 ilova o'zi yozadigan fayl ───────────────────► /var/log/<app>/*.log             ← logrotate aylantiradi
```

journald yozuvlarni metadata bilan saqlaydi: qaysi unit, qaysi PID, qaysi **priority** (jiddiylik darajasi). Shuning uchun `journalctl` "faqat nginx", "faqat xatolar", "faqat oxirgi soat", "faqat joriy boot" kabi filtrlarni grep'siz bajara oladi. Priority darajalari syslog'dan olingan: 0 `emerg`, 1 `alert`, 2 `crit`, 3 `err`, 4 `warning`, 5 `notice`, 6 `info`, 7 `debug`. `-p err` — `err` va undan jiddiyroq (0–3).

Jurnal diskda saqlanishi uchun `/var/log/journal` papkasi bo'lishi kerak: standart `Storage=auto` sozlamasi shu papka bor bo'lsa diskka, bo'lmasa faqat xotiraga (reboot'da yo'qoladi) yozadi. Ubuntu 24.04 da bu papka bor edi. Jurnal hajmi chegaralangan va uni `/etc/systemd/journald.conf` da sozlash mumkin.

logrotate o'zi daemon emas — uni kuniga bir marta systemd timer (`logrotate.timer`) ishga tushiradi. U `/etc/logrotate.conf` va `/etc/logrotate.d/` dagi qoidalarni o'qiydi va `/var/lib/logrotate/status` da qaysi fayl qachon aylantirilganini eslab qoladi.

Asosiy direktivalar:

- `daily` / `weekly` — qanchalik tez-tez; `rotate 7` — nechta eski nusxa saqlanadi.
- `compress` — eski nusxalarni gzip; `delaycompress` — eng yangi eski nusxani (`.1`) hali siqmaslik.
- `missingok` — fayl yo'q bo'lsa xato bermaslik; `notifempty` — bo'sh faylni aylantirmaslik.
- `create 0640 www-data adm` — yangi bo'sh fayl qaysi huquq bilan yaratilishi.
- `postrotate ... endscript` — aylantirishdan keyin buyruq (masalan, servisga "faylni qayta och" signali).
- `copytruncate` — faylni nusxalab, keyin asl faylni bo'shatish. Faylni qayta ocha olmaydigan ilovalar uchun, lekin nusxa olish va bo'shatish orasida yozilgan qatorlar yo'qolishi mumkin.

## Buyruqlar

Natijalar Ubuntu 24.04 + systemd 255 konteynerida olingan (qator boshidagi sana va host nomi qisqartirilgan).

```bash
journalctl -p err -b --no-pager | tail -3
```
```text
rsyslogd[49]: imklog: cannot open kernel log (/proc/kmsg): Operation not permitted.
rsyslogd[49]: activation of module imklog failed [v8.2312.0 try https://www.rsyslog.com/e/2145 ]
root[196]: demo xato xabari
```
Joriy boot'dagi xatolar. Oxirgisi `logger -p user.err "demo xato xabari"` bilan yozilgan; birinchi ikkitasi — konteynerda kernel logiga ruxsat yo'qligidan.

```bash
journalctl -u tick -n 3 --no-pager -o cat
```
```text
tick.service: Deactivated successfully.
Started tick.service - Tick demo.
tick 10:38:37
```
Bitta servis (`-u`), oxirgi 3 qator (`-n`), faqat xabar matni (`-o cat`). `-f` qo'shsangiz — jonli kuzatish.

```bash
journalctl -u tick --since "10 min ago" --no-pager | wc -l
```
```text
11
```
Vaqt bo'yicha filtr: `--since today`, `--since "2026-10-11 09:00" --until "09:30"` ham ishlaydi.

```bash
journalctl --disk-usage
ls -d /var/log/journal; grep -E "^#?Storage" /etc/systemd/journald.conf
```
```text
Archived and active journals take up 8.0M in the file system.
/var/log/journal
#Storage=auto
```
Jurnal hajmi va saqlash rejimi: papka bor, ya'ni jurnal reboot'dan keyin ham saqlanadi.

```bash
ls /var/log
```
```text
README  alternatives.log  apt  auth.log  bootstrap.log  btmp  dmesg  dpkg.log  faillog  journal  lastlog  private  syslog  wtmp
```
`auth.log` — kirishlar va sudo, `syslog` — umumiy, `dpkg.log` — paket o'rnatishlar tarixi.

```text
/var/log/myapp/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```
`/etc/logrotate.d/myapp` dagi namunaviy qoida.

```bash
logrotate -d /etc/logrotate.d/myapp
```
```text
warning: logrotate in debug mode does nothing except printing debug messages!  Consider using verbose mode (-v) instead if this is not what you want.
reading config file /etc/logrotate.d/myapp
...
rotating pattern: /var/log/myapp/*.log  after 1 days (7 rotations)
empty log files are not rotated, old logs are removed
considering log /var/log/myapp/app.log
...
  log does not need rotating (log has already been rotated)
```
Dry-run: hech narsani o'zgartirmaydi, faqat nima qilishini aytadi. Yangi qoidada logrotate faylni bugun "aylantirilgan" deb hisobladi.

```bash
logrotate -f /etc/logrotate.d/myapp && ls /var/log/myapp
```
```text
app.log
app.log.1
```
Majburiy aylantirish. `delaycompress` tufayli `app.log.1` hali `.gz` emas; keyingi aylantirishda siqiladi.

```bash
systemctl list-timers --all | grep logrotate
```
```text
Mon 2026-10-12 00:00:00 UTC   timer              logrotate.service
```
logrotate qachon avtomatik ishlashi.

## Odatiy xatolar

- **Hamma narsani `grep` bilan matnli logdan qidirish.** Belgi: servis xatosi `syslog` da ko'rinmayapti yoki shovqin ko'p. Sabab: kerakli ma'lumot journald'da, filtrlarsiz. To'g'ri usul: `journalctl -u servis -p err --since "1 hour ago"`.
- **Jurnal reboot'dan keyin bo'sh.** Belgi: `journalctl -b -1` → `No journal boot entry found from the specified boot offset (-1).` Sabab: `/var/log/journal` yo'q, jurnal faqat xotirada edi. To'g'ri usul: papkani yarating yoki `Storage=persistent`, keyin journald'ni qayta ishga tushiring.
- **Ilova logi aylantirilgandan keyin yozishni to'xtatdi.** Belgi: yangi `app.log` bo'sh, yozuvlar `app.log.1` ga tushyapti. Sabab: ilova eski fayl deskriptorini ushlab turibdi. To'g'ri usul: `postrotate` da servisga qayta ochish signalini yuboring yoki `copytruncate` ishlating.
- **logrotate qoidasini sinamasdan qoldirish.** Belgi: bir oydan keyin disk to'ldi, qoida hech qachon ishlamagan. Sabab: yo'l yoki sintaksis xatosi. To'g'ri usul: `logrotate -d` bilan tekshiring, bir marta `-f` bilan sinang.
- **`/var/log` dagi fayllarni qo'lda `rm` qilish.** Belgi: `df` o'zgarmadi yoki servis log yozishni to'xtatdi. Sabab: fayl ochiq turibdi. To'g'ri usul: logrotate'ga topshiring yoki `journalctl --vacuum-*` bilan jurnalni tozalang.

## Intervyuda

**Savol:** Servis tunda yiqildi. Sababni topish uchun loglarni qanday tekshirasiz?

**Namunaviy javob:** Avval `systemctl status servis` bilan oxirgi holat va exit kodini ko'raman, keyin `journalctl -u servis --since "yesterday 23:00" --until "today 02:00"` bilan aynan o'sha vaqt oralig'ini o'qiyman. Faqat xatolarni ko'rish uchun `-p err` qo'shaman; agar yiqilish reboot bilan bog'liq bo'lsa, oldingi boot'ni `-b -1` bilan ochaman. Ilova o'z faylga yozsa, `/var/log/<app>/` dagi fayllarni ham, kernel tomondan OOM bo'lgan-bo'lmaganini `journalctl -k` bilan tekshiraman.
