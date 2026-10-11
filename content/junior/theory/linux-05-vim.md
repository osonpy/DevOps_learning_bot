## Tushuncha

Kechasi soat ikkida server ishlamay qoldi, sizda faqat SSH bor va bitta konfig qatorini tuzatish kerak. VS Code yo'q, sichqoncha yo'q. Mana shunday paytda muharrirni bilish kerak bo'ladi. Deyarli har bir Linux serverda **vim** (yoki uning kichik akasi `vi`) bor, ko'pchiligida **nano** ham bor.

nano oddiy: ochasiz, yozasiz, pastdagi yordam qatorida tugmalar ko'rsatilgan (`^O` saqlash, `^X` chiqish; `^` — Ctrl). Boshlash uchun yetarli. Vim esa boshida g'alati tuyuladi, lekin uni o'rganishga arziydi: u hamma joyda bor, kuchli va qo'l klaviaturadan chiqmaydi. Bu darsning maqsadi — vim ustasi bo'lish emas, balki faylni ochib, o'zgartirib, saqlab, **xotirjam chiqib keta olish**.

Vim'dan qo'rqishning asosiy sababi — **rejimlar**. Oddiy muharrirda har bosilgan tugma matnga yoziladi. Vim'da esa tugmalar rejimga qarab har xil ish qiladi: bir rejimda `d` harfi yoziladi, boshqasida u "o'chirish" buyrug'ining boshlanishi. Buni tushunsangiz, vim mantiqli bo'lib qoladi.

## Qanday ishlaydi

```text
                 i, a, o                       :
  ┌──────────┐ ───────────►  ┌──────────┐   ┌──────────┐
  │  Normal  │               │  Insert  │   │ Command  │  :w  :q  :wq  :q!  :%s/../../g
  │ harakat, │ ◄─────────── │  matn    │   │  qatori  │
  │ buyruqlar│      Esc      │  yozish  │   └──────────┘
  └──────────┘ ◄──────────────────────────────── Enter yoki Esc
```

Vim **Normal** rejimda ochiladi. Bu yerda tugmalar buyruq: harakatlanish, o'chirish, nusxalash. `i` bosilsa **Insert** rejim (pastda `-- INSERT --` yozuvi) — endi oddiy muharrirdek yozasiz. `Esc` — Normal'ga qaytish. Normal'da `:` bosilsa pastda **Command** qatori ochiladi: saqlash, chiqish, almashtirish shu yerda. Qayerda ekaningizni bilmasangiz — `Esc` ni bir-ikki bosing, Normal'ga qaytasiz.

Normal rejim buyruqlari "fe'l + harakat" kabi tuziladi: `d` (delete) + `d` = butun qatorni o'chirish, `y` (yank, nusxa) + `y` = qatorni nusxalash. Oldiga son qo'yish mumkin: `3dd` — 3 qator.

Almashtirish buyrug'ining tuzilishi: `:[diapazon]s/eski/yangi/[flag]`. Diapazon berilmasa — faqat joriy qator, `%` — butun fayl. `g` flag'i bo'lmasa, har qatorda faqat **birinchi** topilma almashtiriladi. `c` flag'i har almashtirishdan oldin tasdiq so'raydi.

Bu darsdagi buyruqlarning kichik to'plami bilan ham ish bitadi. Amalda eng ko'p ishlatiladiganlari: qidirish (`/`), qator o'chirish (`dd`), bekor qilish (`u`), saqlash va chiqish. Qolganlarini kerak bo'lganda `vimtutor` yoki `:help` dan topasiz — masalan, `:help :s` almashtirish buyrug'ining barcha flag'larini ko'rsatadi.

Vim fayl ochilganda yonida yashirin `.fayl.swp` (swap) yaratadi — kutilmagan uzilishda ishingizni tiklash uchun. SSH uzilib qolsa, keyingi safar faylni ochganingizda "E325: ATTENTION" ogohlantirishi chiqadi.

## Buyruqlar

Quyidagi natijalar Ubuntu 24.04 da vim'ning skript rejimi (`vim -es`) orqali tekshirilgan — interaktiv rejimda xuddi shu tugmalar bir xil ishlaydi.

```bash
vim ~/hosts.test
```
Faylni ochish. Fayl yo'q bo'lsa — saqlaganingizda yaratiladi.

```text
i        kursor oldidan yozishni boshlash (a — keyin, o — yangi qator ostida)
Esc      Normal rejimga qaytish
:w       saqlash          :q    chiqish (o'zgarish bo'lsa ruxsat bermaydi)
:wq      saqlab chiqish   :q!   saqlamasdan chiqish (o'zgarishlar yo'qoladi)
:x       saqlab chiqish (faqat o'zgarish bo'lsa yozadi)
```
Eng muhim besh buyruq — ularni bilsangiz, vim'da "qamalib qolmaysiz".

```bash
printf "1\n2\n3\n" > v.txt
vim -es -c "normal ggdd" -c wq v.txt; cat v.txt
```
```text
2
3
```
`gg` — fayl boshiga, `dd` — qatorni o'chirish. `G` — fayl oxiriga.

```bash
printf "1\n2\n3\n" > v.txt
vim -es -c "normal ggyyp" -c wq v.txt; cat v.txt
```
```text
1
1
2
3
```
`yy` — qatorni nusxalash, `p` — kursor ostiga qo'yish. `dd` bilan o'chirilgan qator ham `p` bilan qo'yiladi — bu "kesib olish".

```bash
printf "1\n2\n3\n" > v.txt
vim -es -c "normal Gdd" -c "normal u" -c wq v.txt; cat v.txt
```
```text
1
2
3
```
`u` — oxirgi o'zgarishni bekor qilish, Ctrl+R — qaytarish.

```bash
printf "127.0.0.1 localhost\n::1 localhost ip6-localhost\n" > hosts.test
vim -es -c "%s/localhost/LOCAL/g" -c wq hosts.test; cat hosts.test
```
```text
127.0.0.1 LOCAL
::1 LOCAL ip6-LOCAL
```
`%` va `g` bilan — butun fayldagi barcha topilmalar. E'tibor bering: `ip6-localhost` ichidagisi ham almashdi.

```bash
vim -es -c "s/LOCAL/X/" -c wq hosts.test; cat hosts.test
```
```text
127.0.0.1 LOCAL
::1 X ip6-LOCAL
```
`%` siz va `g` siz: faqat joriy qatorda va faqat birinchi topilma. Skript rejimida joriy qator oxirgi qator edi.

```text
/so'z    oldinga qidirish; n — keyingi, N — oldingi topilma
:set number     qator raqamlarini ko'rsatish
```

```bash
export EDITOR=vim
```
`crontab -e`, `git commit`, `visudo` kabi buyruqlar qaysi muharrirni ochishini belgilaydi. Doimiy qilish uchun `~/.bashrc` ga yoziladi.

```bash
vimtutor
```
O'rnatilgan interaktiv darslik (~30 daqiqa) — vim'ni o'rganishning eng yaxshi boshlanishi.

## Odatiy xatolar

- **Vim'dan chiqa olmaslik.** Belgi: `:q` yozilsa matnga `:q` qo'shiladi. Sabab: siz Insert rejimdasiz. To'g'ri usul: `Esc`, keyin `:q!` (saqlamasdan) yoki `:wq`.
- **`:%s` da `g` ni unutish.** Belgi: ba'zi joylar almashmagan. Sabab: `g` siz har qatorda faqat birinchi topilma almashadi. To'g'ri usul: `:%s/eski/yangi/g`, shubhali bo'lsa `gc` bilan tasdiqlab.
- **Kerakmas joylar ham almashishi.** Belgi: `localhost` → `LOCAL` qilganda `ip6-localhost` ham buzildi. Sabab: naqsh qator ichidagi istalgan joyda topiladi. So'z chegarasi `\<localhost\>` ham bu yerda yordam bermaydi — `-` so'z belgisi emas, shuning uchun `ip6-` dan keyin ham chegara bor (tekshirildi). To'g'ri usul: `:%s/localhost/LOCAL/gc` bilan har birini tasdiqlash yoki naqshni aniqroq yozish (masalan, atrofidagi bo'shliq bilan).
- **E325: ATTENTION (swap fayl).** Belgi: fayl ochilganda ogohlantirish. Sabab: oldingi sessiya uzilgan yoki faylni boshqa odam ochib turibdi. To'g'ri usul: boshqa sessiya yo'qligiga ishonch hosil qiling, `R` (tiklash) yoki `D` (swap'ni o'chirish) tanlang.
- **Root faylni oddiy user bilan tahrirlash.** Belgi: `:w` da `E45: 'readonly' option is set (add ! to override)`, `:w!` da esa `E212: Can't open file for writing`. Sabab: faylga yozish huquqi yo'q — `!` buni chetlab o'ta olmaydi. To'g'ri usul: `:q!` bilan chiqib, `sudoedit /etc/fayl` yoki `sudo vim` bilan qayta oching; uzun tahrirdan oldin buni o'ylab oling.

## Intervyuda

**Savol:** Production serverda konfig faylni xavfsiz tahrirlash uchun qanday yo'l tutasiz?

**Namunaviy javob:** Avval faylning zaxira nusxasini olaman, masalan `cp nginx.conf nginx.conf.bak`. Keyin `sudoedit` yoki `sudo vim` bilan tahrirlayman; almashtirishlarni butun faylga qo'llashdan oldin tasdiq rejimida tekshiraman. Saqlagach, servisning o'z tekshiruvini ishga tushiraman — `nginx -t`, `sshd -t` yoki `visudo -c` — va faqat u o'tsa reload qilaman. Ideal holatda konfig Git'da yoki Ansible kabi vositada saqlanadi, shunda qo'lda tahrir istisno bo'ladi va har o'zgarish tarixda qoladi.
