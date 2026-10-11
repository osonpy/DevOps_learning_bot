## Tushuncha

Serverda ishlashning yarmi — o'qish: konfig faylni o'qish, logni o'qish, buyruq qanday ishlashini o'qish. Kimdir "nginx yiqildi" desa, siz birinchi navbatda logni ochasiz. Kimdir "bu flag nima qiladi?" desa — qo'llanmani. Shuning uchun bu darsdagi vositalar oddiy ko'rinadi, lekin ular bilan har kuni, kuniga o'nlab marta ishlaysiz.

Faylni o'qishning to'g'ri vositasi fayl hajmiga va maqsadga bog'liq. Kichik konfigni `cat` bilan butunlay chiqarish mumkin. 2 GB'lik logni `cat` qilsangiz, terminal bir necha daqiqa matn "qusadi" va siz baribir hech narsa ko'rmaysiz. Unday faylni `less` bilan sahifalab o'qiysiz yoki faqat oxirini `tail` bilan ko'rasiz. Hozir yozilayotgan logni esa `tail -f` bilan "jonli" kuzatasiz — bu incident paytida eng ko'p ishlatiladigan buyruqlardan biri.

Ikkinchi muhim ko'nikma — **yordam topish**. Hech kim barcha flag'larni yodlamaydi, shu jumladan senior'lar ham. Farq shundaki, tajribali odam kerakli ma'lumotni 30 soniyada topadi: `man`, `--help`, `tldr`, `apropos`. Bularni bilish — buyruqlarni yodlashdan muhimroq.

## Qanday ishlaydi

`cat` faylni boshidan oxirigacha o'qib, stdout'ga yozadi. `less` esa faylni oynaga sig'adigan qismlar bilan ko'rsatadi va o'qishni kerak bo'lgandagina davom ettiradi, shuning uchun katta fayllarda ham tez ochiladi. `less` ichidagi asosiy tugmalar: `Space` — keyingi sahifa, `b` — oldingi, `/so'z` — oldinga qidirish, `n` / `N` — keyingi / oldingi topilma, `g` / `G` — boshi / oxiri, `q` — chiqish.

`tail -f` bilan `tail -F` farqi loglar **aylantirilganda** (rotation) ko'rinadi:

```text
 logrotate:  app.log  →  app.log.1   (eski fayl qayta nomlandi)
             yangi app.log yaratildi
 tail -f app.log   eski faylni (endi app.log.1) kuzatishda qoladi → yangi qatorlar ko'rinmaydi
 tail -F app.log   NOMNI kuzatadi → "has been replaced; following new file" → yangi faylga o'tadi
```

`-f` fayl deskriptoriga yopishib oladi, `-F` esa `--follow=name --retry` ga teng: fayl nomini kuzatadi va fayl vaqtincha yo'q bo'lsa ham qayta urinadi. Loglar uchun deyarli doim `-F` to'g'ri tanlov.

`man` sahifalari **bo'limlarga** ajratilgan: 1 — oddiy buyruqlar, 5 — fayl formatlari, 8 — administrator buyruqlari. Shuning uchun `man passwd` buyruq haqida, `man 5 passwd` esa `/etc/passwd` fayli formati haqida. `apropos so'z` (yoki `man -k so'z`) qisqa tavsiflardan qidiradi — buyruq nomini bilmaganingizda qulay.

## Buyruqlar

Natijalar Ubuntu 24.04 konteynerida olingan.

```bash
head -n 3 /etc/passwd
```
```text
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
```
Faylning dastlabki 3 qatori. `-n` berilmasa — 10 qator.

```bash
tail -n 2 /etc/passwd
```
```text
messagebus:x:100:101::/nonexistent:/usr/sbin/nologin
syslog:x:101:102::/nonexistent:/usr/sbin/nologin
```
Oxirgi 2 qator. `tail -n +2 fayl` esa 2-qatordan boshlab hammasini chiqaradi — CSV sarlavhasini tashlab ketish uchun qulay.

```bash
wc -l /etc/passwd
```
```text
22 /etc/passwd
```
Qatorlar soni. `wc -w` — so'zlar, `wc -c` — baytlar.

```bash
tail --help | grep -E "^ +(-f|-F)"
```
```text
  -f, --follow[={name|descriptor}]
  -F                       same as --follow=name --retry
```
`--help` — qisqa ma'lumot, man o'rnatilmagan konteynerlarda ham ishlaydi.

```bash
tail -F /var/log/syslog
```
```text
tail: 'app.log' has been replaced;  following new file
```
Logni jonli kuzatish; Ctrl+C bilan chiqasiz. Pastdagi qator `-F` rotatsiyani sezganda stderr'ga chiqaradigan xabar (sinov faylida olingan). Ubuntu'da `/var/log/syslog` ni rsyslog yozadi; systemd jurnali uchun ekvivalent — `journalctl -f` (16-dars).

```bash
logger "salom devops"
```
Tizim logiga xabar yozadi — `tail -F` yoki `journalctl -f` oynasida paydo bo'lishini ko'rasiz. Skriptlardan log yozishning eng oddiy yo'li.

```bash
less +F /var/log/syslog
```
`less` ni "kuzatish" rejimida ochadi (`tail -f` kabi). Ctrl+C bosilsa oddiy `less` ga qaytadi — orqaga varaqlab qidirish mumkin, `F` yana kuzatishga qaytaradi.

```bash
file win.sh /etc/passwd
cat -A win.sh
```
```text
win.sh:      Bourne-Again shell script, ASCII text executable, with CRLF line terminators
/etc/passwd: ASCII text
#!/bin/bash^M$
echo hi^M$
```
`file` fayl turini mazmuniga qarab aniqlaydi (kengaytmaga emas) — binary faylni `cat` qilishdan oldin foydali. `cat -A` ko'rinmas belgilarni ko'rsatadi: `$` — qator oxiri, `^M` — Windows'dagi `\r`. Windows'da yozilib serverga ko'chirilgan skript `./win.sh` qilinganda `cannot execute: required file not found` beradi: kernel `#!` qatoridagi `/bin/bash\r` degan (mavjud bo'lmagan) interpretatorni qidiradi. `sed -i 's/\r$//' win.sh` (yoki `dos2unix`) bilan tuzatiladi.

```bash
man 5 passwd
apropos rotate
```
Birinchisi `/etc/passwd` formatini tushuntiradi, ikkinchisi tavsifida "rotate" bor buyruqlarni topadi. Minimal Docker image'larda man sahifalari olib tashlangan — haqiqiy serverda sinab ko'ring.

```bash
tldr tar
```
Eng ko'p ishlatiladigan misollar bilan qisqa sahifa. Ubuntu 24.04 da `tldr` paketi "transitional" (boshqa klientga o'tkazuvchi) paket sifatida keladi — qaysi klient o'rnatilganini o'zingiz tekshirib ko'ring, `pipx install tldr` ham variant.

## Odatiy xatolar

- **Katta logni `cat` qilish.** Belgi: terminal uzoq vaqt matn chiqaradi, SSH sekinlashadi. Sabab: butun fayl ekranga yuborildi. To'g'ri usul: `less`, `tail -n 100` yoki `grep` bilan kerakli qismini oling.
- **Rotatsiyadan keyin `tail -f` "jim" qolishi.** Belgi: servis ishlayapti, lekin yangi qatorlar ko'rinmaydi. Sabab: fayl qayta nomlandi, `tail -f` eski faylda qoldi. To'g'ri usul: `tail -F`.
- **`less` dan chiqa olmaslik.** Belgi: klaviatura "ishlamayapti". Sabab: `less` (yoki `man`) hali ochiq. To'g'ri usul: `q`; agar `F` rejimida bo'lsangiz — avval Ctrl+C, keyin `q`.
- **Windows'dan kelgan fayldagi `\r`.** Belgi: skript "required file not found" deydi yoki konfig qiymati g'alati ishlaydi, garchi matn to'g'ri ko'rinsa ham. Sabab: qator oxirida ko'rinmas `\r` (CRLF). To'g'ri usul: `file` yoki `cat -A` bilan tekshiring, `\r` ni olib tashlang, muharriringizni LF'ga sozlang.
- **Faqat internetdan qidirish.** Belgi: blog'dagi flag sizning versiyangizda yo'q. Sabab: boshqa versiya yoki boshqa OS (macOS'dagi BSD vositalari GNU'dan farq qiladi). To'g'ri usul: serverdagi `man` yoki `--help` — u aynan o'rnatilgan versiya uchun.

## Intervyuda

**Savol:** Production'da ilova logini kuzatish kerak. Qaysi buyruqni ishlatasiz va nega `tail -f` emas?

**Namunaviy javob:** Agar ilova faylga yozsa, `tail -F` ishlataman, chunki u fayl nomini kuzatadi: logrotate faylni qayta nomlab yangisini yaratganda ham avtomatik yangi faylga o'tadi, `tail -f` esa eski faylda qolib ketadi. Ilova systemd servisi bo'lsa va stdout'ga yozsa, `journalctl -u servis -f` qulayroq, chunki u filtr va vaqt bo'yicha qidirishni ham beradi. Kerakli joyni tez topish uchun `less +F` dan foydalanaman: kuzatishdan to'xtab, orqaga qidirib, yana kuzatishga qaytish mumkin.
