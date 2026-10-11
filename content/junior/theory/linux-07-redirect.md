## Tushuncha

Har bir dastur uchta "quvur" bilan tug'iladi. Biridan ma'lumot oladi, ikkitasiga yozadi: biri — oddiy natija uchun, ikkinchisi — xatolar uchun. Ular **stdin**, **stdout** va **stderr** deyiladi. Terminalda ikkala chiqish ham ekranga tushgani uchun ular bir xil ko'rinadi, lekin aslida ular alohida va buni bilish juda foydali.

Hayotiy misol: cron har tunda backup skriptini ishga tushiradi. Ertalab "backup ishladimi?" degan savol tug'iladi. Agar skript chiqishi hech qayerga yozilmagan bo'lsa — javob yo'q. Agar faqat stdout faylga yozilgan bo'lsa — xatolar baribir yo'qolgan. Shuning uchun DevOps'da `>> /var/log/backup.log 2>&1` kabi qatorlarni ko'p ko'rasiz: ikkala oqim ham bitta logga tushadi.

Ikkinchi g'oya — **pipe** (`|`). U bir dasturning stdout'ini keyingisining stdin'iga ulaydi. Bu Unix falsafasining yuragi: har bir vosita bitta ishni yaxshi qiladi, murakkab vazifa esa ularni zanjirga ulash bilan yechiladi. `cut`, `sort`, `uniq`, `grep`, `wc` alohida oddiy, birga esa kuchli tahlil vositasi.

## Qanday ishlaydi

Har bir oqimning raqami bor — **file descriptor** (fd):

```text
              ┌──────────────┐ 1 stdout ──► ekran / fayl / keyingi buyruq
 stdin 0 ───► │   buyruq     │
              └──────────────┘ 2 stderr ──► ekran / fayl
```

Yo'naltirish operatorlari shu raqamlar bilan ishlaydi:

- `> fayl` — stdout faylga, fayl **ustidan** yoziladi (eski mazmun o'chadi). `1>` bilan bir xil.
- `>> fayl` — stdout fayl **oxiriga** qo'shiladi.
- `2> fayl` — stderr faylga.
- `2>&1` — "stderr'ni stdout hozir qayerga ketayotgan bo'lsa, o'sha yerga yubor".
- `&> fayl` — bash'da ikkalasini birga faylga (`> fayl 2>&1` ning qisqasi).
- `< fayl` — stdin'ni fayldan olish.
- `/dev/null` — "qora tuynuk": yozilgan hamma narsa yo'qoladi.

Eng ko'p chalkashtiriladigan joy — **tartib**. Shell yo'naltirishlarni chapdan o'ngga bajaradi va `2>&1` stdout'ning **o'sha paytdagi** manzilidan nusxa oladi:

```text
 cmd > log 2>&1     1) stdout → log   2) stderr → (stdout hozir log'da) → log   ✔ ikkalasi log'da
 cmd 2>&1 > log     1) stderr → (stdout hozir ekranda) → ekran   2) stdout → log   ✘ xato ekranda
```

Pipe stdout'ni ulaydi, stderr'ni emas. `cmd 2>&1 | grep ...` yozilsa, xatolar ham pipe orqali o'tadi.

Pipeline'ning exit code'i standart holatda **oxirgi** buyruqniki. Ya'ni `muhim_buyruq | tee log` da birinchi buyruq yiqilsa ham natija "muvaffaqiyatli" ko'rinadi. Skriptlarda `set -o pipefail` buni tuzatadi: zanjirdagi biror buyruq yiqilsa, butun pipeline xato qaytaradi.

## Buyruqlar

Natijalar Ubuntu 24.04 konteynerida olingan (`/etc/hostname` mavjud, `/yoq-papka` yo'q).

```bash
ls /etc/hostname /yoq-papka > out.txt 2> err.txt
cat out.txt; cat err.txt
```
```text
/etc/hostname
ls: cannot access '/yoq-papka': No such file or directory
```
Natija va xato alohida fayllarga ajraldi. `ls` ning exit code'i `2` — qisman xato bo'ldi.

```bash
ls /etc/hostname /yoq-papka > both.txt 2>&1; cat both.txt
```
```text
ls: cannot access '/yoq-papka': No such file or directory
/etc/hostname
```
Ikkalasi bitta faylda. `&> all.txt` ham aynan shunday natija berdi.

```bash
ls /etc/hostname /yoq-papka 2>&1 > only.txt
```
```text
ls: cannot access '/yoq-papka': No such file or directory
```
Teskari tartib: xato ekranga chiqdi, faylda faqat `/etc/hostname`.

```bash
cut -d: -f1 /etc/passwd | sort | tee users.txt | wc -l
```
```text
22
```
`tee` oqimni ikkiga bo'ldi: tartiblangan ro'yxat `users.txt` ga yozildi va bir vaqtda `wc -l` ga uzatildi. `tee -a` — faylga qo'shib yozadi.

```bash
false | true; echo $?
set -o pipefail
false | true; echo $?
```
```text
0
1
```
`pipefail` siz yiqilgan birinchi buyruq "ko'rinmay" qoldi.

```bash
wc -l < /etc/passwd
wc -l /etc/passwd
```
```text
19
19 /etc/passwd
```
`<` bilan `wc` fayl nomini bilmaydi — faqat sonni chiqaradi, skriptda qiymatni o'zgaruvchiga olish uchun qulay (bu toza `ubuntu:24.04` image'ida olingan, shuning uchun 19).

```bash
NAME=web
cat > app.conf <<EOF
server_name $NAME
EOF
cat > raw.conf <<"EOF"
server_name $NAME
EOF
cat app.conf raw.conf
```
```text
server_name web
server_name $NAME
```
**Here-doc** (`<<EOF ... EOF`) — bir nechta qatorni stdin sifatida berish; skriptlarda konfig fayl yozishning standart usuli. Belgi qo'shtirnoqsiz bo'lsa (`<<EOF`) o'zgaruvchilar almashtiriladi, qo'shtirnoqli bo'lsa (`<<"EOF"`) matn aynan yoziladi.

```bash
backup.sh >> /var/log/backup.log 2>&1
```
Cron va skriptlar uchun klassik qator: ikkala oqim ham logga, oldingi yozuvlar saqlanadi.

```bash
noisy_command > /dev/null 2>&1
```
Hamma chiqishni tashlab yuborish. Ehtiyot bo'ling: xatolar ham yo'qoladi — buni faqat chiqish haqiqatan kerak bo'lmaganda qiling.

## Odatiy xatolar

- **`>` bilan muhim faylni ustidan yozish.** Belgi: konfig yoki log bo'shab qoldi. Sabab: `>>` o'rniga `>` yozildi. To'g'ri usul: qo'shish uchun `>>`; interaktiv shell'da `set -o noclobber` mavjud faylni `>` bilan ustidan yozishni taqiqlaydi.
- **`2>&1` tartibi.** Belgi: logda xatolar yo'q, ular cron xatida yoki ekranda. Sabab: `2>&1 > log` yozilgan. To'g'ri usul: avval fayl, keyin `2>&1`: `> log 2>&1`.
- **`sudo echo ... > /etc/fayl`.** Belgi: `Permission denied`, garchi `sudo` bo'lsa ham. Sabab: `>` ni sizning (oddiy) shell'ingiz bajaradi, `sudo` esa faqat `echo` ga ta'sir qiladi (tekshiruvda oddiy user `echo test > /etc/denied.txt` da aynan shu xatoni oldi). To'g'ri usul: `echo test | sudo tee /etc/fayl` (qo'shish uchun `tee -a`).
- **Pipe xatoni "yutib yuborishi".** Belgi: skript muvaffaqiyatli tugadi, lekin natija bo'sh. Sabab: pipeline exit code'i faqat oxirgi buyruqniki. To'g'ri usul: skript boshida `set -o pipefail` (ko'pincha `set -euo pipefail`).
- **O'qilayotgan faylga yozish.** Belgi: `sort fayl > fayl` dan keyin fayl bo'sh. Sabab: shell avval faylni `>` bilan bo'shatadi, keyin `sort` bo'sh faylni o'qiydi. To'g'ri usul: vaqtinchalik faylga yozib `mv` qiling yoki `sort -o fayl fayl`.

## Intervyuda

**Savol:** `cmd > file 2>&1` va `cmd 2>&1 > file` farqi nima?

**Namunaviy javob:** Shell yo'naltirishlarni chapdan o'ngga bajaradi, `2>&1` esa stderr'ni stdout'ning shu lahzadagi manziliga yo'naltiradi. Birinchi holatda stdout avval faylga yo'naltiriladi, keyin stderr ham o'sha faylga ketadi — ikkala oqim faylda. Ikkinchi holatda stderr stdout hali terminalga qarab turgan paytda unga ulanadi, keyin faqat stdout faylga o'tadi, shuning uchun xatolar terminalda qoladi. Cron va servis loglarida doim birinchi shakldan foydalanaman.
