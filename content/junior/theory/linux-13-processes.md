## Tushuncha

"Server sekinlashdi" — DevOps'da eng ko'p eshitiladigan shikoyatlardan biri. Birinchi savol: **hozir serverda nima ishlayapti va qaysi biri resurslarni yeyapti?** Bunga jarayonlar (process) bilan ishlash ko'nikmasi javob beradi.

**Process** — ishlab turgan dastur nusxasi. Bitta dasturdan bir vaqtda bir nechta process bo'lishi mumkin: nginx bitta master va bir nechta worker process bilan ishlaydi. Har bir process'ning o'z raqami (**PID**), uni ishga tushirgan "ota"si (**PPID**), egasi (user), holati, xotirasi va CPU vaqti bor.

Ikkinchi mavzu — **fon ishlari**. SSH orqali uzoq ishni (katta arxiv, ma'lumot ko'chirish) boshladingiz, internet uzilib qoldi — ish ham to'xtadi. Bunga yo'l qo'ymaslik uchun `nohup` va ayniqsa `tmux` bor. Ammo esda tuting: bular qo'lda boshlangan vaqtinchalik ishlar uchun. Doimiy ishlashi kerak bo'lgan servislar systemd orqali boshqariladi (15-dars).

## Qanday ishlaydi

Linux'da har bir process boshqasidan tug'iladi: shell `ls` ni ishga tushirsa, `ls` ning PPID'i shell'ning PID'i bo'ladi. Hammasining ildizida PID 1 turadi (serverda — systemd). Bu daraxtni `ps -ef --forest` yoki `pstree` ko'rsatadi.

Process holatlari (`ps` dagi `STAT` ustuni):

```text
 R  running      CPU'da ishlayapti yoki navbatda turibdi
 S  sleeping     nimanidir kutyapti (tarmoq, taymer) — eng ko'p uchraydigan holat
 D  disk wait    to'xtatib bo'lmaydigan kutish, odatda disk yoki NFS I/O
 T  stopped      to'xtatilgan (masalan Ctrl+Z bilan)
 Z  zombie       tugagan, lekin otasi hali uning natijasini "olmagan"
```

**Zombie** resurs yemaydi, faqat process jadvalida joy egallaydi. Uni `kill` bilan o'ldirib bo'lmaydi — u allaqachon o'lgan. Uni ota process `wait` qilib tozalashi kerak. Ota o'lsa, zombie'ni PID 1 "asrab oladi" va tozalaydi. Ko'p zombie — ota dasturdagi xatoning belgisi.

**Load average** — 1, 5 va 15 daqiqalik o'rtacha "ish navbati": CPU'da ishlayotgan yoki unga navbat kutayotgan process'lar, Linux'da esa **D holatidagilar** ham hisoblanadi. Shuning uchun yuqori load har doim ham CPU yetishmasligi emas — disk sekin bo'lsa ham load o'sadi. Son **yadrolar soniga** nisbatan baholanadi: 4 yadroli serverda load 4 — to'liq band, 8 — ikki barobar ko'p ish navbatda. Yadrolar sonini `nproc` ko'rsatadi.

**Job control** — shell'ning o'z mexanizmi. Buyruq oxiriga `&` qo'ysangiz, u fonda ishlaydi va shell darhol bo'shaydi. Ctrl+Z oldingi plandagi ishni to'xtatadi (T holati), `bg` uni fonda davom ettiradi, `fg` oldingi planga qaytaradi, `jobs` ro'yxatni ko'rsatadi. Lekin job'lar shell'ga bog'langan: shell yopilsa (SSH uzilsa), ular odatda SIGHUP olib tugaydi.

`tmux` bu muammoni boshqacha hal qiladi: u serverda alohida ishlaydigan "terminal multiplexer". Siz uning ichida ishlaysiz, SSH uzilsa ham tmux sessiyasi va ichidagi hamma narsa davom etadi. Qayta kirib, `tmux attach` bilan o'sha joyga qaytasiz.

## Buyruqlar

Natijalar Ubuntu 24.04 konteynerida olingan.

```bash
sleep 300 &
ps -o pid,ppid,user,stat,cmd -p $!
```
```text
    PID    PPID USER     STAT CMD
     46      45 root     S    sleep 300
```
`$!` — oxirgi fon process PID'i. `sleep` — S (uxlayapti), otasi — shell (45).

```bash
ps aux
```
Barcha process'lar: `USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND`. `RSS` — haqiqiy RAM (KB), `VSZ` — virtual xotira (ancha katta bo'lishi normal). `--sort` bilan istalgan ustun bo'yicha saralash mumkin, masalan `--sort=-%cpu`.

```bash
pstree -p 1 | head -3
```
```text
bash(1)-+-bash(51)-+-head(53)
        |          `-pstree(52)
        `-sleep(46)
```
Process daraxti PID'lar bilan. Konteynerda PID 1 — `bash`, serverda — `systemd`.

```bash
bash -c "sleep 100 & sleep 200 & jobs"
```
```text
[1]-  Running                 sleep 100 &
[2]+  Running                 sleep 200 &
```
`+` — joriy job (`fg` argumentsiz shuni oladi), `-` — oldingisi. `fg %1` — 1-job'ni oldingi planga.

```bash
nproc; cat /proc/loadavg
```
```text
12
2.01 2.06 1.59 3/2397 60
```
12 yadro, load ~2 — bemalol. `3/2397` — hozir ishlayotgan / jami thread'lar, oxirgisi — oxirgi berilgan PID.

```bash
ps -o pid,ppid,stat,cmd --ppid <ota_PID>
```
```text
    PID    PPID STAT CMD
     66      65 Z    [python3] <defunct>
```
Zombie shunday ko'rinadi: `Z` holati va `<defunct>`. Tekshiruvda bola process darhol tugadi, ota esa `wait` qilmadi.

```bash
nohup ./long_job.sh > job.log 2>&1 &
```
`nohup` SIGHUP'ni e'tiborsiz qoldiradi, shuning uchun terminal yopilganda ham ish davom etadi. Chiqishni o'zingiz faylga yo'naltiring.

```bash
tmux new -s work       # yangi sessiya
# Ctrl+b, keyin d      # detach: sessiyadan chiqish (u ishlashda davom etadi)
tmux ls                # sessiyalar ro'yxati
tmux attach -t work    # qaytish
```
Standart prefiks — Ctrl+b. Bu interaktiv buyruqlar, ularni konteynerda emas, haqiqiy SSH sessiyasida sinab ko'ring.

```bash
htop
```
Interaktiv monitor: F6 — saralash ustunini tanlash, F5 — daraxt ko'rinishi, F9 — signal yuborish, `q` — chiqish.

## Odatiy xatolar

- **Load'ni yadrolarsiz baholash.** Belgi: "load 6, server o'lyapti!" — 16 yadroli serverda. Sabab: load mutlaq son sifatida o'qildi. To'g'ri usul: `nproc` bilan solishtiring; yuqori load + past CPU bo'lsa — disk I/O'ni (D holat) tekshiring.
- **Zombie'ni `kill -9` qilish.** Belgi: process ro'yxatda qolaveradi. Sabab: zombie allaqachon tugagan. To'g'ri usul: ota process'ni toping (PPID) va uni tuzating yoki qayta ishga tushiring.
- **Uzoq ishni oddiy SSH'da qoldirish.** Belgi: ulanish uzildi, ish yarmida to'xtadi. Sabab: job'lar SIGHUP oldi. To'g'ri usul: `tmux` ichida ishga tushiring.
- **Servisni `nohup ... &` bilan "production"da yurgizish.** Belgi: reboot'dan keyin servis yo'q, yiqilsa hech kim qayta ishga tushirmaydi, loglar tarqoq. Sabab: `nohup` servis menejeri emas. To'g'ri usul: systemd unit.
- **VSZ'ni RAM sarfi deb o'ylash.** Belgi: "Java 10 GB yeyapti", aslida `free` yetarli joy ko'rsatadi. Sabab: VSZ virtual manzil maydoni. To'g'ri usul: `RSS` (va `free -h` dagi `available`) ga qarang.

## Intervyuda

**Savol:** 4 yadroli serverda load average 8, lekin `top` da CPU deyarli bo'sh. Bu nimani bildiradi?

**Namunaviy javob:** Linux'da load average CPU navbatidan tashqari to'xtatib bo'lmaydigan kutishdagi, ya'ni D holatidagi process'larni ham hisoblaydi. CPU bo'sh, load esa yadrolar sonidan ikki barobar ko'p bo'lsa, ko'p process diskni yoki NFS kabi tarmoq saqlagichini kutayotgan bo'lishi ehtimoli katta. `ps` da D holatidagi process'larni qidiraman, `top` dagi `wa` (I/O wait) ko'rsatkichiga qarayman va disk yuklamasini `iostat` kabi vosita bilan tekshiraman. Keyin qaysi servis diskni yuklayotganini yoki saqlagich sekinlashganini aniqlayman.
