## Tushuncha

Oddiy `rwx` ko'p holatni qoplaydi, lekin hammasini emas. Bir nechta savol bor:

- Oddiy user parolini o'zgartiradi, parol esa faqat root yoza oladigan `/etc/shadow` da. Qanday qilib?
- `/tmp` ga hamma yoza oladi. Unda nega boshqa user'ning faylini o'chira olmaysiz?
- Jamoa papkasida har kim fayl yaratadi. Fayllar egasining shaxsiy guruhiga emas, jamoa guruhiga tegishli bo'lishi uchun nima qilish kerak?

Javob — uchta **maxsus bit**: SUID, SGID va sticky bit. Ular kam uchraydi, lekin ularni bilmasangiz, ba'zi ruxsat muammolari "sehr"dek tuyuladi. Ba'zan esa bitta odamga oddiy `rwx` dan tashqari huquq kerak bo'ladi — buning uchun **ACL** bor.

Bu darsning ikkinchi qismi — **break-fix** ko'nikmasi. "Permission denied" — eng ko'p uchraydigan xatolardan biri, va uni tasodifiy `chmod` bilan emas, tartibli tekshiruv bilan hal qilish kerak. Tajribali muhandis avval sababni topadi, keyin minimal o'zgarish qiladi.

## Qanday ishlaydi

Maxsus bitlar oddiy huquqlar oldidagi to'rtinchi raqam:

```text
 4000  SUID    faylda: dastur EGASI huquqi bilan ishlaydi      -rwsr-xr-x  (passwd)
 2000  SGID    papkada: yangi fayllar PAPKA guruhini oladi     drwxrws---
 1000  sticky  papkada: faylni faqat egasi (yoki root) o'chiradi drwxrwxrwt  (/tmp)
```

`ls -l` da ular `x` o'rnida ko'rinadi: `s` (SUID/SGID) yoki `t` (sticky). Agar ostidagi `x` yo'q bo'lsa, katta harf chiqadi — `S` yoki `T`. Bu odatda xato sozlamaning belgisi: bit qo'yilgan, lekin bajarish huquqi yo'q.

**SUID** xavfli quvvat: SUID root dasturdagi har qanday zaiflik root huquqini beradi. Shuning uchun tizimda ular kam va ro'yxati nazorat qilinadi. Linux interpretatorli **skriptlar** uchun SUID'ni e'tiborsiz qoldiradi — tekshiruvda `4755` qilingan shell skript `id -u` ni root emas, oddiy user UID'i bilan chiqardi.

**ACL** (Access Control List) oddiy owner/group/others'dan tashqari aniq user yoki guruhga huquq qo'shadi: `setfacl -m u:ali:rx papka`. ACL bor fayl `ls -l` da huquqlar oxirida `+` bilan belgilanadi, batafsil ko'rish — `getfacl`.

**"Permission denied" tekshiruv tartibi:**

```text
 1) Men kimman?          id                    → UID, guruhlar (yangi guruh hali kuchga kirmagan bo'lishi mumkin)
 2) Yo'l bo'ylab huquq   namei -l /to'liq/yo'l  → / dan faylgacha HAR BIR papkada x bormi
 3) Faylning o'zi        ls -l, getfacl        → rwx va ACL
 4) Qo'shimcha himoya    AppArmor (Ubuntu) / SELinux (RHEL), mount opsiyalari (noexec, nosuid)
```

Ko'pchilik 3-qadamdan boshlaydi va 2-qadamni o'tkazib yuboradi. Fayl 644 bo'lsa ham, yo'ldagi bitta papkada `x` bo'lmasa, unga yetib bo'lmaydi.

## Buyruqlar

Natijalar Ubuntu 24.04 konteynerida olingan.

```bash
ls -l /usr/bin/passwd; ls -ld /tmp
stat -c %a /usr/bin/passwd /tmp
```
```text
-rwsr-xr-x 1 root root 64152 May 30  2024 /usr/bin/passwd
drwxrwxrwt 1 root root 4096 Oct 11 10:37 /tmp
4755
1777
```
`passwd` — SUID root (shu sababli `/etc/shadow` ga yoza oladi), `/tmp` — hamma yozadi + sticky.

```bash
su ali -c "rm -f /tmp/sticky_f"      # fayl root'niki, huquqi 666
```
```text
rm: cannot remove '/tmp/sticky_f': Operation not permitted
```
Fayl hammaga yozish uchun ochiq bo'lsa ham, sticky bit uni boshqa user o'chirishiga yo'l qo'ymadi.

```bash
chgrp team /srv/team && chmod 770 /srv/team && chmod g+s /srv/team
ls -ld /srv/team; touch /srv/team/new; ls -l /srv/team/new
```
```text
drwxrws--- 2 root team 4096 Oct 11 10:37 /srv/team
-rw-r--r-- 1 root team 0 Oct 11 10:37 /srv/team/new
```
Fayl yaratuvchining guruhini emas, papka guruhini (`team`) oldi. Guruh a'zolari bir-birining faylini tahrirlay olishi uchun ularning umask'i ham guruhga yozishga ruxsat berishi kerak (masalan 002).

```bash
chmod 2660 /tmp/S && ls -ld /tmp/S
chmod 1644 /tmp/Tf && ls -l /tmp/Tf
```
```text
drw-rwS--- 2 root root 4096 Oct 11 10:37 /tmp/S
-rw-r--r-T 1 root root 0 Oct 11 10:37 /tmp/Tf
```
Katta `S` va `T`: bit bor, ostida `x` yo'q — deyarli har doim xato.

```bash
namei -l /tmp/px/sub/f
```
```text
f: /tmp/px/sub/f
drwxr-xr-x root root /
drwxrwxrwt root root tmp
drwx------ root root px
drwxr-xr-x root root sub
-rw-r--r-- root root f
```
Fayl 644, lekin `px` papkasi 700 — boshqa user'lar shu yerda to'xtaydi (tekshiruvda `cat` → `Permission denied`). `namei` yo'lni bo'laklab, har biri huquqini bitta jadvalda ko'rsatadi.

```bash
chmod 700 /srv/acl && setfacl -m u:ali:rx /srv/acl
ls -ld /srv/acl; getfacl -p /srv/acl
```
```text
drwxr-x---+ 2 root root 4096 Oct 11 10:37 /srv/acl
# file: /srv/acl
# owner: root
# group: root
user::rwx
user:ali:r-x
group::r-x
mask::r-x
other::---
```
`+` — ACL bor. `ali` ga alohida `r-x` berildi. E'tibor bering: ACL bilan `ls -l` dagi guruh ustuni endi `mask` ni ko'rsatadi (`r-x`), haqiqiy guruh huquqini emas.

## Odatiy xatolar

- **Faqat faylning huquqiga qarash.** Belgi: `ls -l` 644, user baribir o'qiy olmaydi. Sabab: ota papkalardan birida `x` yo'q. To'g'ri usul: `namei -l /to'liq/yo'l`.
- **Muammoni `chmod -R 777` bilan "yopish".** Belgi: ishladi, lekin keyin xavfsizlik muammosi. Sabab: sabab topilmadi, hamma narsa ochildi. To'g'ri usul: 4 qadamli tartib, keyin faqat to'sayotgan joyni minimal o'zgartirish.
- **Katta `S`/`T` ni sezmaslik.** Belgi: SGID papka "ishlamayapti" yoki dastur ishga tushmaydi. Sabab: maxsus bit bor, `x` yo'q. To'g'ri usul: `ls -l` dagi harf kattaligiga qarang, kerakli `x` ni qo'shing.
- **Skriptga SUID qo'yish.** Belgi: skript root huquqini olmaydi. Sabab: Linux skriptlar uchun SUID'ni e'tiborsiz qoldiradi (va bu to'g'ri). To'g'ri usul: aniq buyruq uchun `sudoers` qoidasi.
- **Guruhga qo'shib, eski sessiyada sinash.** Belgi: SGID papkaga yozib bo'lmayapti. Sabab: yangi guruh faqat qayta login'dan keyin ishlaydi. To'g'ri usul: chiqib qayta kiring va `id` bilan tekshiring.

## Intervyuda

**Savol:** User faylni o'qiy olmayapti, `ls -l` esa `-rw-r--r--` ko'rsatyapti. Qanday tekshirasiz?

**Namunaviy javob:** Avval `id` bilan user aslida kim va qaysi guruhlarda ekanini ko'raman. Keyin `namei -l` bilan butun yo'lni tekshiraman — faylga yetish uchun har bir ota papkada `x` huquqi kerak, ko'pincha muammo shu yerda bo'ladi. Agar yo'l joyida bo'lsa, `getfacl` bilan ACL'ni, keyin AppArmor yoki SELinux loglarini va mount opsiyalarini ko'raman. Sababni topgach, faqat to'sayotgan joyni o'zgartiraman, hech qachon `777` qilmayman.
