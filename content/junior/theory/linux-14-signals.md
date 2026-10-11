## Tushuncha

Restoranni yopish vaqti keldi. Ikki xil yo'l bor: ofitsiantlarga "yangi buyurtma olmang, boshlanganlarini tugating, kassani yoping" deyish — yoki chiroqni o'chirib, hammani darhol ko'chaga chiqarish. Birinchisi — **SIGTERM**, ikkinchisi — **SIGKILL**. Ikkalasi ham dasturni to'xtatadi, lekin oqibatlari butunlay boshqacha.

**Signal** — kernel orqali process'ga yuboriladigan qisqa xabar: "to'xta", "konfigni qayta o'qi", "to'xtab tur". Dastur ko'p signallarni **ushlab**, o'zi qaror qila oladi: masalan, SIGTERM kelganda ochiq ulanishlarni yopib, buferdagi ma'lumotni diskka yozib, keyin chiqadi. Bu **graceful shutdown** deyiladi va production'da juda muhim: deploy, restart va konteyner to'xtatilishi aynan shunday ishlaydi.

Ikkinchi mavzu — **prioritet** (nice). Og'ir, lekin shoshilinch bo'lmagan ishni (backup arxivi, katta siqish) shunday ishga tushirish mumkinki, u asosiy servisdan CPU "tortib olmaydi".

## Qanday ishlaydi

Eng muhim signallar (raqamlar x86 Linux uchun, `kill -l` bilan tekshirilgan):

```text
  1  SIGHUP   "terminal uzildi"; ko'p daemon'lar uchun — konfigni qayta o'qish
  2  SIGINT   Ctrl+C
  9  SIGKILL  majburiy o'ldirish — USHLAB BO'LMAYDI, tozalash yo'q
 15  SIGTERM  "iltimos, to'xta" — kill'ning standart signali
 18  SIGCONT  to'xtatilganni davom ettirish
 19  SIGSTOP  majburiy to'xtatish (pauza) — ushlab bo'lmaydi
```

Dastur signalni oladi va uchta yo'ldan birini tanlaydi: standart harakat (ko'pincha — tugash), e'tiborsiz qoldirish yoki o'zining **handler**'ini ishga tushirish. SIGKILL va SIGSTOP bundan mustasno: ularni kernel o'zi bajaradi, dastur hech narsa qila olmaydi. Shuning uchun SIGKILL'dan keyin vaqtinchalik fayllar, lock'lar, yarim yozilgan ma'lumotlar qolib ketishi mumkin.

Signal bilan tugagan process'ning exit code'i `128 + signal raqami`: SIGTERM → 143, SIGKILL → 137. Loglarda yoki konteyner statusida 137 ni ko'rsangiz — process majburan o'ldirilgan (ko'pincha OOM yoki timeout).

To'g'ri tartib: avval `kill PID` (SIGTERM), bir necha soniya kutish, faqat process javob bermasa — `kill -9`. Docker ham aynan shunday: `docker stop` avval SIGTERM yuboradi, 10 soniya kutadi (`-t` bilan o'zgaradi), keyin SIGKILL.

Konteynerlarda bitta muhim nuance bor: **PID 1** uchun kernel signallarning standart harakatini qo'llamaydi. Agar PID 1 dagi dastur SIGTERM'ga handler o'rnatmagan bo'lsa, signal shunchaki e'tiborsiz qoladi. Tekshiruvda `sleep 1000` bilan ishlagan konteyner `docker stop` dan keyin 10,2 soniyada exit code 137 bilan o'ldirildi. `docker run --init` bilan esa (kichik init PID 1 bo'ladi va signalni uzatadi) 0,1 soniyada 143 bilan to'xtadi.

**Nice** qiymati −20 (eng yuqori prioritet) dan 19 gacha (eng past), standart — 0. Oddiy user faqat prioritetni **pasaytira** oladi (son oshiriladi), oshirish (manfiy son) uchun root kerak.

## Buyruqlar

Natijalar Ubuntu 24.04 konteynerida olingan.

```bash
kill -l TERM KILL HUP INT STOP CONT
```
```text
15
9
1
2
19
18
```
Signal nomidan raqamni topish. `kill -l` — to'liq ro'yxat.

```bash
bash -c 'trap "echo graceful shutdown; exit 0" TERM; echo ready; sleep 30 & wait' &
sleep 0.5; kill $!; wait $!; echo "exit=$?"
```
```text
ready
graceful shutdown
exit=0
```
`trap` — bash'da signal handler. SIGTERM kelganda skript o'z ishini tugatib, toza chiqdi. Python'da xuddi shu g'oya `signal` moduli bilan amalga oshiriladi.

```bash
bash -c 'trap "echo graceful shutdown; exit 0" TERM; sleep 30 & wait' &
sleep 0.5; kill -9 $!; wait $!; echo "exit=$?"
```
```text
bash: line 1:    80 Killed                  bash -c "trap ..."
exit=137
```
O'sha skript, lekin SIGKILL: handler ishlamadi, "graceful shutdown" yozilmadi, exit code 137.

```bash
sleep 30 & sleep 0.2; kill $!; wait $!; echo "exit=$?"
```
```text
exit=143
```
Handler'siz dastur SIGTERM'da standart harakat — tugash; kod 128+15.

```bash
pkill -f "python3 worker.py"
killall nginx
```
Nom bo'yicha signal yuborish. `pkill` nom bo'yicha qidiradi, `-f` — to'liq buyruq qatori bo'yicha. Ehtiyot bo'ling: `-f` bilan qisqa naqsh kutilmagan process'larga ham mos kelishi mumkin. Avval `pgrep -a naqsh` bilan kimlar tanlanishini ko'ring.

```bash
nice -n 10 sleep 5 &
ps -o pid,ni,cmd -p $!
renice -n 15 -p $!
```
```text
    PID  NI CMD
     87  10 sleep 5
87 (process ID) old priority 10, new priority 15
```
`NI` ustuni — nice qiymati; `renice` ishlab turgan process'ni o'zgartiradi.

```bash
su ali -c "nice -n -5 true"
```
```text
nice: cannot set niceness: Permission denied
```
Oddiy user prioritetni oshira olmaydi.

```bash
docker stop -t 30 app
```
SIGTERM'dan keyin 30 soniya kutadi — sekin to'xtaydigan ilovalar uchun.

## Odatiy xatolar

- **Darhol `kill -9`.** Belgi: servis qayta ishga tushganda "lock file exists", buzilgan fayl yoki yo'qolgan ma'lumot. Sabab: SIGKILL dasturga tozalash imkonini bermaydi. To'g'ri usul: avval `kill` (TERM), kutish, faqat keyin `-9`.
- **`kill -9` ham ishlamasligi.** Belgi: process ro'yxatda qolaveradi. Sabab: u D holatida (diskni kutyapti) yoki zombie. To'g'ri usul: D bo'lsa — I/O manbasini (disk, NFS) tekshiring; zombie bo'lsa — ota process'ni.
- **Konteyner `docker stop` da 10 soniya "osilib" qolishi.** Belgi: har to'xtatish aniq 10 soniya, exit code 137. Sabab: PID 1 SIGTERM'ni ushlamaydi yoki shell skript signalni bola process'ga uzatmaydi. To'g'ri usul: ilovada SIGTERM handler, `exec` bilan ishga tushirish yoki `--init`.
- **`pkill -f` bilan ortiqcha process'larni o'ldirish.** Belgi: kerakli servis ham to'xtadi. Sabab: naqsh boshqa buyruq qatorlariga ham mos keldi. To'g'ri usul: avval `pgrep -a`, aniqroq naqsh.
- **SIGHUP har qanday dasturni "reload" qiladi deb o'ylash.** Belgi: dastur reload o'rniga tugadi. Sabab: SIGHUP'ning standart harakati — tugash; reload faqat buni ataylab qo'llab-quvvatlaydigan daemon'larda ishlaydi. To'g'ri usul: hujjatga qarang yoki `systemctl reload` ishlating.

## Intervyuda

**Savol:** SIGTERM va SIGKILL farqi nima va nima uchun `docker stop` birinchi SIGTERM yuboradi?

**Namunaviy javob:** SIGTERM — so'rov: dastur uni ushlab, yangi so'rovlarni qabul qilishni to'xtatadi, ochiq ulanish va fayllarni yopadi, keyin chiqadi. SIGKILL'ni esa ushlab bo'lmaydi — kernel process'ni darhol to'xtatadi va tozalash imkoni bo'lmaydi. `docker stop` avval SIGTERM yuboradi va standart 10 soniya kutadi, shunda ilova graceful shutdown qila oladi; faqat vaqt tugasa SIGKILL. Shu sababli konteynerdagi ilova PID 1 sifatida SIGTERM handler'ga ega bo'lishi yoki init jarayoni orqali ishga tushirilishi kerak.
