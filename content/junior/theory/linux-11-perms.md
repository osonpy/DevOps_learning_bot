## Tushuncha

Ko'p qavatli ofisni tasavvur qiling: har bir xonaning egasi bor, bo'lim xodimlari ba'zi xonalarga kira oladi, mehmonlar esa faqat qabulxonaga. Linux fayllari ham shunday himoyalangan. Har bir fayl va papkada uchta "kim" uchun uchta "nima" yozilgan: **egasi** (owner), **guruh** (group) va **boshqalar** (others) — o'qish, yozish va bajarish.

Bu DevOps'da har kuni uchraydi. Nginx sayt fayllarini o'qiy olmasa — 403. Deploy user papkaga yoza olmasa — deploy yiqiladi. `.env` faylni hamma o'qiy olsa — ma'lumotlar bazasi paroli serverdagi har qanday jarayonga ochiq. Eng xavfli "yechim" — `chmod 777`: xato yo'qoladi, lekin xavfsizlik ham yo'qoladi.

Maqsad — har bir fayl uchun **kerakli minimum** huquqni berish. Buning uchun huquqlarni o'qiy olish, ularni raqam (octal) va harf (symbolic) shaklida yoza olish va yangi fayllar qanday huquq bilan yaratilishini (umask) tushunish kerak.

## Qanday ishlaydi

`ls -l` chiqishidagi birinchi ustun:

```text
 -rwxr-x---  1  deploy  www-data  1024  app.sh
 │└┬┘└┬┘└┬┘     egasi   guruhi
 │ │  │  └── others:  ---  hech narsa
 │ │  └───── group:   r-x  o'qish + bajarish
 │ └──────── owner:   rwx  hammasi
 └────────── tur: - fayl, d papka, l symlink
```

Har bir harfning raqami bor: `r` = 4, `w` = 2, `x` = 1. Uchlikdagi raqamlar qo'shiladi: `rwx` = 7, `r-x` = 5, `r--` = 4, `---` = 0. Shuning uchun `-rwxr-x---` = **750**, `-rw-r--r--` = 644, `-rw-------` = 600.

Huquqlar **papka** uchun boshqacha ma'noga ega va bu ko'p chalkashlik sababi:

- `r` — papka ichidagi **nomlar ro'yxatini** ko'rish (`ls`);
- `w` — papkada fayl **yaratish, o'chirish, qayta nomlash** (faylning o'z huquqidan qat'i nazar!);
- `x` — papkaga **kirish** va undagi fayllarga yo'l bo'ylab yetib borish.

Tekshiruvda `744` papkada boshqa user nomlarni ko'rdi, lekin faylni o'qiy olmadi (`x` yo'q). `711` papkada esa `ls` rad etildi, lekin fayl nomini bilgan user uni o'qidi.

Kernel tekshiruvni tartib bilan qiladi: avval "siz egasimisiz?" — ha bo'lsa faqat owner huquqlari qo'llanadi; yo'q bo'lsa "guruhdamisiz?"; yo'q bo'lsa others. Ya'ni egasi uchun `---` qo'yilgan bo'lsa, u guruh huquqidan foydalana olmaydi. Root bu tekshiruvlardan deyarli to'liq ozod.

**umask** yangi fayl va papkalardan qaysi bitlarni **olib tashlashni** belgilaydi. Fayllar 666 (`rw-rw-rw-`), papkalar 777 dan boshlanadi, umask'dagi bitlar "o'chiriladi". `umask 022` → fayl 644, papka 755; `umask 027` → fayl 640, papka 750. Bu ayirish emas, **mask**: `umask 033` bilan fayl 633 emas, **644** bo'ldi (tekshirildi), chunki fayllarda `x` biti boshidanoq yo'q.

## Buyruqlar

Natijalar Ubuntu 24.04 konteynerida olingan.

```bash
umask; touch f644 && mkdir d755 && stat -c "%a %A %n" f644 d755
```
```text
0022
644 -rw-r--r-- f644
755 drwxr-xr-x d755
```
`stat -c "%a"` huquqni raqam bilan chiqaradi — skriptlarda solishtirish uchun qulay.

```bash
umask 027 && touch f027 && mkdir d027 && stat -c "%a %A %n" f027 d027
```
```text
640 -rw-r----- f027
750 drwxr-x--- d027
```
`umask` faqat joriy shell va undan ishga tushganlarga ta'sir qiladi; doimiy qilish uchun shell profiliga yoki servis sozlamasiga (`UMask=`) yoziladi.

```bash
chmod 640 s; stat -c "%a %A" s
chmod g+w,o-r s; stat -c "%a %A" s
chmod u=rw,go= s; stat -c "%a %A" s
```
```text
640 -rw-r-----
660 -rw-rw----
600 -rw-------
```
Symbolic shakl: `u`/`g`/`o`/`a` (hammasi), `+` qo'shish, `-` olish, `=` aniq o'rnatish. Mavjud huquqni qisman o'zgartirishda raqamdan xavfsizroq.

```bash
chown -R www-data:www-data /var/www/site
```
Egasi va guruhini rekursiv o'zgartirish. Faqat guruh — `chgrp` yoki `chown :guruh`. Fayl egasini o'zgartirish odatda root huquqini talab qiladi.

```bash
chmod -R a-x,u+rwX,go+rX tree/
stat -c "%a %n" tree tree/d tree/f
```
```text
755 tree
755 tree/d
644 tree/f
```
Katta `X` — "faqat papkalarga (yoki allaqachon bajariladigan fayllarga) `x`". Papkalar ochiq qoldi, oddiy fayllar bajariladigan bo'lib qolmadi — `chmod -R 755` ning to'g'ri muqobili.

```bash
su ali -c "ls /tmp/rx; cat /tmp/rx/a"      # /tmp/rx — 744
```
```text
a
cat: /tmp/rx/a: Permission denied
```
Papkada `r` bor, `x` yo'q: nom ko'rindi, fayl ochilmadi.

```bash
chown ali /tmp/o && chmod 074 /tmp/o
su ali -c "cat /tmp/o"
```
```text
cat: /tmp/o: Permission denied
```
Egasi `ali`, owner uchun `---`. Group va others'da `r` bor, lekin kernel egaga faqat owner uchligini qo'llaydi.

```bash
chmod 777 /tmp/w && chmod 444 /tmp/w/f     # f — root'niki, faqat o'qish uchun
su ali -c "rm -f /tmp/w/f"; ls /tmp/w | wc -l
```
```text
0
```
Fayl o'chdi: o'chirish papkaning `w` huquqiga bog'liq, faylning o'ziga emas.

## Odatiy xatolar

- **`chmod 777` bilan "tuzatish".** Belgi: xato yo'qoldi, lekin keyin fayl o'zgartirilgan yoki o'g'irlangan. Sabab: hamma — har qanday servis va user — yoza va o'qiy oladi. To'g'ri usul: kim kirishi kerakligini aniqlang va egasi/guruhini to'g'rilang; odatda 750/640 yetarli.
- **`chmod -R 755` ni butun ilovaga qo'llash.** Belgi: barcha fayllar (konfig, `.env`) bajariladigan va hammaga o'qiladigan bo'ldi. Sabab: rekursiv raqam fayl va papkani farqlamaydi. To'g'ri usul: katta `X` yoki `find -type d` / `find -type f` bilan alohida.
- **Faqat faylni tekshirish.** Belgi: fayl 644, lekin `Permission denied`. Sabab: yo'ldagi papkalardan birida `x` yo'q. To'g'ri usul: butun yo'lni tekshiring (12-darsda `namei -l`).
- **Maxfiy fayllarni ochiq qoldirish.** Belgi: `ls -l .env` → `-rw-r--r--`. Sabab: standart umask 022. To'g'ri usul: `.env`, SSH kalitlar, sertifikat kalitlari — 600 (yoki egasi servis user bo'lgan 640).
- **umask'ni ayirish deb hisoblash.** Belgi: kutilgan 633 o'rniga 644. Sabab: umask bitlarni o'chiradi, ayirmaydi. To'g'ri usul: "boshlang'ich huquqdan umask'dagi bitlarni olib tashlash" deb o'ylang.

## Intervyuda

**Savol:** Papkadagi `r`, `w`, `x` huquqlari fayldagidan qanday farq qiladi?

**Namunaviy javob:** Papka — bu nomlar ro'yxati, shuning uchun `r` ro'yxatni o'qish, ya'ni `ls` ga ruxsat beradi. `w` papkada fayl yaratish, o'chirish va qayta nomlashga ruxsat beradi — hatto faylning o'zi faqat o'qish uchun bo'lsa ham, shuning uchun umumiy papkalarda sticky bit kerak. `x` papkaga kirish va undan o'tib ichidagi fayllarga yetishga ruxsat beradi: `x` siz faylning o'z huquqi qanday bo'lishidan qat'i nazar unga yetib bo'lmaydi. Shuning uchun "Permission denied" ni tekshirganda butun yo'ldagi har bir papkani ko'raman.
