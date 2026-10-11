## Tushuncha

Monitoring ogohlantiradi: "web-01: disk 95%". Bu juniorning birinchi haqiqiy incidentlaridan biri bo'lishi mumkin. Vahima qilmasdan ikkita savolga javob topish kerak: **nima joy egallayapti** va **nimani xavfsiz o'chirish mumkin**. Birinchisiga `du` va `df`, ikkinchisiga `find` javob beradi.

`find` — fayl tizimini aylanib chiqib, shartlarga mos fayllarni topadigan vosita. Shartlar nom, tur, hajm, o'zgarish vaqti, egasi va huquqlar bo'yicha bo'lishi mumkin. Topilgan fayllar bilan darhol biror ish ham qilish mumkin: ro'yxatini chiqarish, `ls -l` qilish, o'chirish.

Bu laboratoriya darsi, shuning uchun asosiy qoida oldindan: **o'chirishdan oldin har doim ro'yxatni ko'ring**. Avval `find ... ` ni o'chirish qismisiz ishga tushirasiz, natijani o'qiysiz, faqat keyin oxiriga `-delete` qo'shasiz. Tajribali muhandislar ham shunday qiladi — chunki `find` xato shart bilan bir soniyada minglab faylni o'chira oladi.

## Qanday ishlaydi

`find` buyrug'i uch qismdan iborat: **qayerdan** qidirish, **qanday shartlar** va **nima qilish**:

```text
 find  /var/log   -type f -name "*.log" -size +10M -mtime +29   -exec ls -lh {} +
       └ qayerdan ┘└──────────── shartlar (AND bilan) ────────────┘└── harakat ──┘
```

Shartlar chapdan o'ngga tekshiriladi va standart holatda "VA" bilan bog'lanadi. `!` — inkor (`! -user root`), `-o` — "YOKI". Harakat berilmasa, `find` topilganini `-print` qiladi.

Raqamli shartlarda belgi ma'noni o'zgartiradi: `+N` — N dan katta, `-N` — N dan kichik, `N` — aynan N. Ikki joyda yaxlitlash tuzoq bo'ladi:

- **`-mtime`** kunlarni butun songa qirqib hisoblaydi. `-mtime +7` — "7 kundan ko'p", amalda **8 kun va undan eski** fayllar. `-mtime -7` — oxirgi 7×24 soat ichida o'zgarganlar. Tekshiruvda 169 soatlik (7,04 kun) fayl `-mtime 7` ga tushdi, `+7` ga esa faqat 193 soatlik fayl tushdi.
- **`-size`** hajmni birlikkacha **yuqoriga** yaxlitlaydi. Shuning uchun `-size -1M` 500 baytlik faylni topmaydi (u "1M" ga yaxlitlanadi), faqat bo'sh fayllarni topadi. Kichik fayllar uchun kichikroq birlik ishlating: `-size -1024k`.

Harakatlar: `-delete` — o'chirish; `-exec cmd {} \;` — har fayl uchun alohida buyruq; `-exec cmd {} +` — fayllarni to'plab, kamroq marta chaqirish (tezroq). Natijani `xargs` ga uzatish ham mumkin, lekin nomida bo'shliq bor fayllar uchun `-print0 | xargs -0` shart.

`du` (disk usage) papka ichidagi fayllar hajmini yig'ib hisoblaydi. `df` (disk free) esa fayl tizimining o'zidan "qancha band, qancha bo'sh" deb so'raydi. Ba'zan ular mos kelmaydi: fayl o'chirilgan, lekin uni hali ham biror jarayon ochib turibdi — `du` uni ko'rmaydi, `df` esa joy hali band deb ko'rsatadi. Bunday fayllar `/proc/<PID>/fd` da `(deleted)` belgisi bilan ko'rinadi; joy jarayon qayta ishga tushirilganda bo'shaydi.

## Buyruqlar

Natijalar Ubuntu 24.04 konteynerida, sinov papkasida olingan.

```bash
du -sh /var/* 2>/dev/null | sort -h | tail -5
```
Har bir papkaning umumiy hajmi (`-s` — yig'indi, `-h` — K/M/G), `sort -h` bunday qiymatlarni to'g'ri saralaydi, eng kattasi pastda. Avval kattaroq papkani topib, keyin ichiga kirib takrorlaysiz.

```bash
df -h /
```
```text
Filesystem      Size  Used Avail Use% Mounted on
overlay         467G  439G  4.6G  99% /
```
Butun fayl tizimi holati (konteyner ichida `overlay` ko'rinadi, VPS'da odatda `/dev/vda1` kabi).

```bash
find . -size +1M
```
```text
./big.log
```
1 MB dan katta fayllar (sinov papkasida 2 MB'lik fayl).

```bash
find . -size -1M -type f
```
```text
./empty.log
...
```
Kutilmagan natija: 500 baytlik `small.log` ro'yxatda yo'q — yuqoridagi yaxlitlash tufayli. `-size -1024k` uni topdi.

```bash
find . -name "*.log" -mtime +7
```
```text
./old10.log
./old8.log
```
10 va 8 kun oldingi fayllar topildi, aynan 7 kunlik fayl esa yo'q. Naqshni qo'shtirnoqqa oling — aks holda `*.log` ni `find` emas, shell kengaytirib yuboradi.

```bash
find . -name "*.log" -mtime +7 -exec ls -lh {} +
```
O'chirishdan oldingi tekshiruv: aynan qaysi fayllar va qancha hajm. Ro'yxat to'g'ri bo'lsa, `-exec ...` o'rniga `-delete` qo'yiladi.

```bash
find /var/www ! -user www-data -type f
```
`www-data` ga tegishli **bo'lmagan** fayllar (`!` — inkor). `-user`, `-group`, `-perm` bilan egalik va huquq muammolarini topasiz.

```bash
find . -name "*.log" | xargs ls
```
```text
ls: cannot access './with': No such file or directory
ls: cannot access 'space.log': No such file or directory
```
`with space.log` ikki so'zga bo'linib ketdi. To'g'risi:

```bash
find . -name "*.log" -print0 | xargs -0 ls
```
`-print0` nomlarni nol bayt bilan ajratadi, `xargs -0` ham shunday o'qiydi — bo'shliq va maxsus belgilar xavfsiz.

```bash
find /proc/[0-9]*/fd -lname "*(deleted)" 2>/dev/null
```
```text
/proc/8/fd/3
```
O'chirilgan, lekin hali ochiq turgan fayllar (sinovda 5 MB'lik log). Shu jarayonni qayta ishga tushirish joyni bo'shatadi.

## Odatiy xatolar

- **`-delete` ni shartlardan oldin yozish.** Belgi: papkadagi **hamma** narsa o'chdi. Sabab: `find . -delete -name "*.log"` — shartlar chapdan o'ngga, `-delete` birinchi bajarilib, har bir faylga qo'llandi (tekshiruvda papka bo'shab qoldi). To'g'ri usul: `-delete` doim oxirida va avval usiz ishga tushiring.
- **`-mtime` va `-size` ni noto'g'ri tushunish.** Belgi: "7 kundan eski" deb o'chirganingizda 7-kun fayllari qoldi yoki kichik fayllar topilmadi. Sabab: kunlar va hajm yaxlitlanadi. To'g'ri usul: chegaradagi holatni kichik sinov papkasida tekshiring.
- **Naqshni qo'shtirnoqsiz yozish.** Belgi: `find: paths must precede expression` yoki faqat joriy papkadagi fayllar qidiriladi. Sabab: shell `*.log` ni oldindan kengaytirdi. To'g'ri usul: `-name "*.log"`.
- **Ishlab turgan servis logini o'chirish.** Belgi: `rm` dan keyin `df` o'zgarmadi. Sabab: servis faylni ochib turibdi, joy bo'shamaydi. To'g'ri usul: servisni reload/restart qiling yoki faylni o'chirish o'rniga bo'shating (`: > app.log`); uzoq muddatda — logrotate (16-dars).
- **Butun `/` bo'ylab qidirish.** Belgi: `find /` uzoq ishlaydi va `/proc` xatolari bilan to'ladi. Sabab: virtual va tarmoq fayl tizimlari ham aylanib chiqiladi. To'g'ri usul: aniq papkadan boshlang, kerak bo'lsa `-xdev` bilan bitta fayl tizimida qoling va `2>/dev/null`.

## Intervyuda

**Savol:** `df` disk 100% to'la deydi, lekin `du -sh /*` yig'indisi ancha kam. Sabab nima bo'lishi mumkin?

**Namunaviy javob:** Eng ko'p uchraydigan sabab — o'chirilgan, lekin hali ham biror jarayon ochib turgan fayl: `du` fayl nomlari orqali hisoblaydi va uni ko'rmaydi, `df` esa fayl tizimidagi haqiqiy band joyni ko'rsatadi. Tekshirish uchun `lsof +L1` yoki `/proc/*/fd` dagi `(deleted)` havolalarni qarayman, keyin o'sha servisni restart qilaman. Boshqa sabablar ham bo'lishi mumkin: mount qilingan disk ostida "yashiringan" fayllar yoki `df -i` bilan ko'rinadigan inode tugashi. Shuning uchun men `df -h` va `df -i` ni birga tekshiraman.
