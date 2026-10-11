## Tushuncha

Tasavvur qiling: siz yangi ishga keldingiz va sizga "mana bu serverga kirib, nima o'rnatilganini ko'rib chiq" deyishdi. Grafik oyna yo'q, sichqoncha yo'q — faqat qora ekran va kursor. DevOps ishining katta qismi aynan shu yerda o'tadi: serverlarning ko'pchiligi Linux'da ishlaydi va ularni boshqarishning asosiy vositasi — terminal.

"Linux" so'zi aslida faqat **kernel**ni (yadro) bildiradi. Kernel — apparat bilan dasturlar o'rtasidagi qatlam: xotirani taqsimlaydi, jarayonlarni navbatga qo'yadi, disk va tarmoq bilan ishlaydi. Lekin faqat kernel bilan hech narsa qilib bo'lmaydi — sizga `ls`, `cp`, shell, kutubxonalar kerak. Bularning ko'pi GNU loyihasidan keladi. Kernel + GNU vositalari + paket menejeri + sozlamalar birgalikda **distributiv** deyiladi.

Ishda eng ko'p uchraydigan oilalar:

- **Debian / Ubuntu** — paket menejeri `apt` (ichida `dpkg`). Bulutdagi VPS'larning katta qismi Ubuntu.
- **RHEL / Rocky / AlmaLinux** — paket menejeri `dnf`. Korporativ muhitlarda ko'p.
- **Alpine** — paket menejeri `apk`. Juda kichik, shuning uchun Docker image'larda mashhur.

Bitta oiladagi bilim boshqasiga deyarli to'liq o'tadi: fayl tizimi, jarayonlar, ruxsatlar bir xil. Asosan paket menejeri va ba'zi konfig yo'llari farq qiladi.

Server uchun versiya tanlashda **LTS** (Long Term Support) so'zini ko'rasiz. Ubuntu LTS har ikki yilda chiqadi (22.04, 24.04 ...) va uzoq muddat xavfsizlik yangilanishlarini oladi. Production'da odatda LTS ishlatiladi: har yarim yilda OS'ni ko'chirib yurish hech kimga kerak emas. Versiyaning kod nomi ham bor — 24.04 "Noble Numbat", qisqacha `noble`. Bu nomni apt manbalari va Docker image teglarida uchratasiz.

## Qanday ishlaydi

Uchta tushunchani ajratib oling — ular ko'pincha aralashtiriladi:

```text
 Siz ──► Terminal (oyna) ──► Shell (bash) ──► Kernel ──► Apparat
         SSH klient,         buyruqni o'qiydi,  tizim
         Windows Terminal    dasturni topadi,   chaqiruvlari
                             ishga tushiradi
```

**Terminal** — shunchaki matn kiritish va chiqarish oynasi. **Shell** (Ubuntu'da odatda `bash`) — siz yozgan qatorni o'qiydigan, uni so'zlarga bo'ladigan, kerakli dasturni topib ishga tushiradigan dastur. Masalan, `ls -l /etc` yozsangiz, bash `ls` degan dasturni `PATH` dagi papkalardan qidiradi (`/usr/bin/ls`), unga `-l` va `/etc` ni argument sifatida beradi. `cd` kabi ba'zi buyruqlar esa alohida dastur emas — shell'ning o'zida qurilgan (builtin). Buni `type` ko'rsatadi.

Enter bosilganda taxminan shunday bo'ladi: shell qatorni so'zlarga ajratadi, birinchi so'z builtin emasligini tekshiradi, keyin `PATH` o'zgaruvchisidagi papkalarni chapdan o'ngga ko'rib chiqadi. Birinchi topilgan fayl yangi jarayon sifatida ishga tushadi, shell esa u tugashini kutadi va keyin yana prompt chiqaradi. Hech qayerda topilmasa — `command not found`. Shu sababli `/usr/local/bin` ga qo'yilgan dastur odatda tizimdagi `/usr/bin` dagi bir xil nomli dasturdan oldin topiladi: u `PATH` da oldinroq turadi.

Buyruqning umumiy shakli: `buyruq -flag argument`. Flag'lar odatda qisqa (`-l`) yoki uzun (`--all`) bo'ladi, qisqalarini birlashtirish mumkin: `ls -l -a` = `ls -la`.

**Prompt** sizga qayerda va kim ekaningizni aytadi:

```text
deploy@web-01:~$      oddiy foydalanuvchi, uy papkasida (~)
root@web-01:/etc#     root (administrator), /etc papkasida
```

Oxiridagi `$` — oddiy foydalanuvchi, `#` — root. Root uchun tizimda deyarli hech qanday cheklov yo'q: noto'g'ri bitta buyruq butun serverni buzishi mumkin. Shuning uchun `#` ni ko'rsangiz — sekinlashing.

## Buyruqlar

Quyidagi natijalar Ubuntu 24.04 konteynerida olingan (sizda soat, nom va raqamlar boshqacha bo'ladi).

```bash
whoami
```
```text
root
```
Hozir qaysi foydalanuvchi nomidan ishlayotganingiz.

```bash
cat /etc/os-release
```
```text
PRETTY_NAME="Ubuntu 24.04.5 LTS"
VERSION_ID="24.04"
ID=ubuntu
...
```
Distributiv nomi va versiyasi — skriptlar ham shu fayldan o'qiydi (yuqorida faqat 3 qator ko'rsatilgan).

```bash
uname -a
```
```text
Linux web-01 6.8.0-45-generic #45-Ubuntu SMP PREEMPT_DYNAMIC ... x86_64 GNU/Linux
```
Kernel nomi, host nomi, kernel versiyasi va arxitektura. Bu qator namuna: Ubuntu 24.04 standart holatda 6.8 seriyali kernel bilan keladi. Konteyner ichida `uname` host mashinaning kernelini ko'rsatadi — konteynerning o'z kerneli yo'q.

```bash
echo $PATH
```
```text
/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
```
Shell dasturlarni qidiradigan papkalar, `:` bilan ajratilgan, tartib muhim.

```bash
uname -r; uname -m
```
```text
6.8.0-45-generic
x86_64
```
Faqat kernel versiyasi va arxitektura (namuna). `x86_64` o'rniga `aarch64` chiqsa — ARM server, ba'zi binary va image'lar boshqacha kerak bo'ladi.

```bash
uptime
```
```text
 10:36:23 up 50 min,  0 user,  load average: 1.92, 1.94, 1.50
```
Server qancha vaqtdan beri yoniq va oxirgi 1, 5, 15 daqiqadagi o'rtacha yuklama (load average'ni 13-darsda batafsil ko'ramiz).

```bash
hostnamectl
```
Host nomi, OS, kernel va virtualizatsiya turini bitta jadvalda ko'rsatadi. Bu buyruq systemd orqali ishlaydi, shuning uchun oddiy konteynerda emas, haqiqiy VPS yoki VM'da sinab ko'ring — natijani bu yerda keltirmadim.

```bash
type cd ls
```
```text
cd is a shell builtin
ls is /usr/bin/ls
```
Qaysi buyruq shell ichida, qaysi biri alohida fayl ekanini ko'rsatadi.

```bash
history | tail -5
```
Siz tergan oxirgi buyruqlar raqamlari bilan. `!123` — 123-raqamli buyruqni qayta bajaradi, Ctrl+R — tarix bo'yicha qidiradi.

## Odatiy xatolar

- **Root bilan kundalik ish.** Belgi: prompt doim `#`. Sabab: VPS'ga birinchi marta `ssh root@IP` bilan kirilgan va shu odat qolgan. To'g'ri usul: alohida user yaratib, kerak joyda `sudo` ishlatish (10-dars).
- **"command not found".** Belgi: `bash: htop: command not found`. Sabab: dastur o'rnatilmagan yoki `PATH` da yo'q. To'g'ri usul: `type nom` bilan tekshiring, keyin paket menejeri bilan o'rnating (`apt install htop`).
- **Distributivni bilmasdan buyruq ko'chirish.** Belgi: Ubuntu'da `dnf: command not found` yoki Alpine'da `apt` ishlamaydi. Sabab: internetdagi qo'llanma boshqa oila uchun yozilgan. To'g'ri usul: avval `cat /etc/os-release` — keyin mos qo'llanma.
- **Tushunmagan buyruqni root bilan ishga tushirish.** Belgi: forumdan `curl ... | sudo bash` yoki `rm -rf` li qatorni ko'chirib, keyin "server ochilmayapti". Sabab: buyruq nima qilishini o'qimasdan bajarish. To'g'ri usul: avval `man`/`--help` bilan har bir flag'ni tushuning, skriptni yuklab, ichini o'qib, keyin ishga tushiring.
- **Katta-kichik harfga e'tibor bermaslik.** Belgi: `LS` yoki `Cat` ishlamaydi, `File.txt` va `file.txt` ikki xil fayl. Sabab: Linux'da hamma narsa case-sensitive. To'g'ri usul: buyruqlar deyarli doim kichik harfda.

## Intervyuda

**Savol:** Linux kernel bilan Linux distributivining farqi nima?

**Namunaviy javob:** Kernel — tizimning yadrosi: jarayonlar, xotira, qurilmalar va tarmoqni boshqaradi, lekin o'zi foydalanuvchiga tayyor tizim emas. Distributiv kernel ustiga GNU vositalari, shell, kutubxonalar, paket menejeri va standart sozlamalarni yig'ib beradi. Masalan, Ubuntu va Rocky bir xil Linux kernelidan foydalanadi, lekin biri `apt`, ikkinchisi `dnf` ishlatadi va yangilanish siyosati farq qiladi. Serverda qaysi distributiv ekanini `/etc/os-release` dan, kernel versiyasini `uname -r` dan bilaman. Amalda bu farq paket nomlari, konfig yo'llari va yangilanish jadvalini tanlashda muhim: production uchun men LTS versiyani tanlayman va uning qo'llab-quvvatlash muddatini oldindan tekshiraman.
