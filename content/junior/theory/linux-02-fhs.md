## Tushuncha

Windows'da `C:`, `D:` disklari bor. Linux'da esa disk qancha bo'lishidan qat'i nazar **bitta daraxt** bor va uning ildizi `/` (root directory). Ikkinchi disk, USB yoki tarmoq papkasi ham shu daraxtning biror shoxiga "ulab" qo'yiladi (mount). Shuning uchun Linux'da "fayl qaysi diskda?" emas, "fayl qaysi yo'lda?" degan savol beriladi.

Papkalar tasodifiy joylashmagan — ular **FHS** (Filesystem Hierarchy Standard) degan kelishuvga amal qiladi. Bu kelishuv tufayli istalgan Linux serverga kirib, konfiglar qayerda, loglar qayerda ekanini taxmin qila olasiz. Bu xuddi har bir shaharda pochta, kasalxona va bozor bo'lishiga o'xshaydi: ko'chalar boshqacha, lekin mantiq bir xil.

Eng ko'p ishlatiladigan papkalar:

- `/etc` — tizim va servislar **konfiguratsiyasi**: `/etc/nginx/`, `/etc/ssh/sshd_config`, `/etc/passwd`. Matnli fayllar, odatda faqat root o'zgartiradi.
- `/var` — **o'zgaruvchan** ma'lumot: `/var/log` (loglar), `/var/lib` (servislar ma'lumoti, masalan `/var/lib/postgresql`), `/var/cache`. Disk to'lib qolsa, birinchi qaraladigan joy.
- `/home` — oddiy foydalanuvchilar uy papkalari (`/home/deploy`). `/root` — root'ning uy papkasi, `/home` ichida emas.
- `/tmp` — vaqtinchalik fayllar; qayta yuklashda tozalanishi mumkin, muhim narsani saqlamang.
- `/usr` — o'rnatilgan dasturlar va kutubxonalar: `/usr/bin` (buyruqlar), `/usr/lib`, `/usr/share`. `/usr/local` — paket menejerisiz qo'lda o'rnatilganlar uchun.
- `/opt` — katta, o'zi bilan hamma narsani olib keladigan uchinchi tomon dasturlari.
- `/srv` — server beradigan ma'lumotlar (sayt fayllari, ilova) uchun mo'ljallangan joy.
- `/proc` va `/sys` — **virtual** fayl tizimlari: diskda yo'q, ularni kernel "hozir" yaratib beradi.
- `/dev` — qurilmalar fayl sifatida (`/dev/sda`, `/dev/null`).
- `/boot` — kernel va boot loader fayllari.

## Qanday ishlaydi

Har bir jarayonning **joriy papkasi** (working directory) bor. Siz yozgan nisbiy yo'llar shu papkaga nisbatan hisoblanadi:

```text
/                     absolute yo'l: doim / dan boshlanadi
├── etc/nginx         /etc/nginx            — qayerda bo'lsangiz ham bir xil
├── var/log           
└── home/deploy       siz shu yerdasiz (pwd)
    └── app/logs      relative: app/logs  yoki  ./app/logs
                      ../../../etc  →  /etc  (har .. bitta yuqoriga)
```

Maxsus belgilar: `.` — joriy papka, `..` — bir pog'ona yuqori, `~` — uy papkangiz (`/home/deploy` yoki `/root`), `-` — `cd` uchun "oldingi papka".

Zamonaviy Ubuntu'da (24.04 ham) `/bin`, `/sbin`, `/lib` alohida papka emas — ular `/usr` ichiga ko'rsatuvchi **symlink**. Buni "usr merge" deyishadi: eski skriptlar `/bin/bash` deb yozsa ham ishlayveradi, lekin haqiqiy fayl `/usr/bin/bash` da.

Daraxtning qaysi qismi qaysi diskda ekanini **mount point**lar belgilaydi. Masalan, katta diskni `/var/lib/postgresql` ga ulasangiz, bu papkadan pastdagi hamma narsa o'sha diskka yoziladi, qolgan tizim esa asosiy diskda qoladi. Foydalanuvchi uchun bu ko'rinmaydi — yo'llar o'zgarmaydi. Qaysi papka qaysi qurilmada ekanini `df -h` yoki `findmnt` ko'rsatadi; disklar bilan 17-darsda batafsil ishlaymiz.

`/proc` alohida e'tiborga loyiq. U yerda har bir jarayon uchun `/proc/<PID>/` papka bor, tizim haqida esa `/proc/meminfo`, `/proc/cpuinfo`, `/proc/loadavg` kabi fayllar. Ularni `cat` qilganingizda kernel ma'lumotni o'sha zahoti hosil qiladi — shuning uchun `ls -l` ularning hajmini 0 deb ko'rsatadi, lekin ichida matn bor. `top`, `ps`, `free` kabi vositalar aslida aynan shu fayllarni o'qiydi.

## Buyruqlar

Natijalar Ubuntu 24.04 konteynerida olingan.

```bash
ls -ld /bin /sbin /lib
```
```text
lrwxrwxrwx 1 root root 7 Apr 22  2024 /bin -> usr/bin
lrwxrwxrwx 1 root root 7 Apr 22  2024 /lib -> usr/lib
lrwxrwxrwx 1 root root 8 Apr 22  2024 /sbin -> usr/sbin
```
`l` va `->` — bu symlink: `/bin` aslida `/usr/bin`.

```bash
pwd
cd /var/log
cd /etc
cd -
```
```text
/var/log
```
`cd -` oldingi papkaga qaytadi va qaysi papkaga o'tganini chiqarib beradi. `cd` (argumentsiz) yoki `cd ~` — uy papkaga.

```bash
ls -lah
```
`-l` — batafsil (huquq, egasi, hajm, sana), `-a` — yashirin fayllar ham (nomi `.` bilan boshlanadiganlar), `-h` — hajm `K`, `M`, `G` ko'rinishida. `-S` qo'shsangiz — hajm bo'yicha saralanadi, kattasi tepada.

```bash
head -5 /proc/meminfo
```
```text
MemTotal:       15550256 kB
MemFree:          686632 kB
MemAvailable:    3846888 kB
Buffers:           99368 kB
Cached:          4678784 kB
```
Kernel bergan xotira statistikasi. Yangi dastur uchun qancha joy borligini `MemFree` emas, `MemAvailable` yaxshiroq ko'rsatadi.

```bash
ls -l /proc/self/exe /proc/self/cwd
```
```text
lrwxrwxrwx 1 root root 0 Oct 11 10:36 /proc/self/cwd -> /root
lrwxrwxrwx 1 root root 0 Oct 11 10:36 /proc/self/exe -> /usr/bin/ls
```
`/proc/self` — "o'zim" degani: bu yerda `ls` o'z jarayonini ko'ryapti. `exe` — qaysi dastur, `cwd` — joriy papka. Boshqa jarayon uchun `self` o'rniga uning PID'ini qo'yasiz.

```bash
cat /proc/loadavg
```
```text
1.92 1.94 1.50 1/2403 21
```
`uptime` dagi load average shu yerdan olinadi.

```bash
tree -L 1 /etc | head
```
Papka strukturasini daraxt ko'rinishida chiqaradi; `-L 1` — faqat bir pog'ona. `tree` standart o'rnatilmagan bo'lishi mumkin: `apt install tree`.

## Odatiy xatolar

- **Nisbiy yo'lni noto'g'ri papkada ishlatish.** Belgi: `No such file or directory`, garchi fayl "aniq bor" bo'lsa ham. Sabab: siz boshqa papkadasiz va yo'l unga nisbatan hisoblandi. To'g'ri usul: `pwd` bilan joyingizni tekshiring, skriptlarda esa absolute yo'l ishlating.
- **`/tmp` ga muhim narsani saqlash.** Belgi: reboot'dan keyin fayl yo'q. Sabab: `/tmp` vaqtinchalik va tozalanadi. To'g'ri usul: ilova ma'lumoti — `/var/lib/<app>` yoki `/srv/<app>`, zaxira — alohida joy.
- **Konfigni noto'g'ri joyda qidirish.** Belgi: `find / -name nginx.conf` ni butun disk bo'yicha uzoq kutish. Sabab: FHS'ni bilmaslik. To'g'ri usul: konfig — `/etc/<servis>/`, log — `/var/log/<servis>/`, ma'lumot — `/var/lib/<servis>/`.
- **Ildizdagi papkalarni "tozalash".** Belgi: joy bo'shatish uchun `/usr/share` yoki `/var/lib` dan nimadir o'chirildi, keyin servislar ishlamay qoldi. Sabab: bu papkalar paket menejeri va servislarga tegishli. To'g'ri usul: tizim papkalarida faqat paket menejeri (`apt remove`, `apt autoremove`) yoki servisning o'z vositasi bilan tozalang.
- **`/proc` fayllarini "0 bayt" deb tashlab ketish.** Belgi: `ls -l /proc/meminfo` hajmi 0, "bo'sh ekan" degan xulosa. Sabab: virtual fayl hajmi oldindan ma'lum emas. To'g'ri usul: `cat` yoki `head` bilan o'qing.

## Intervyuda

**Savol:** Serverda disk to'lib qoldi. FHS bo'yicha birinchi navbatda qaysi papkalarni tekshirasiz va nega?

**Namunaviy javob:** Avval `/var` ni ko'raman, chunki u o'zgaruvchan ma'lumot uchun: `/var/log` dagi aylantirilmagan loglar va `/var/lib` dagi servis ma'lumotlari (masalan, Docker yoki ma'lumotlar bazasi) eng ko'p o'sadi. Keyin `/tmp` va foydalanuvchilarning `/home` papkalarini, qo'lda o'rnatilgan dasturlar bo'lsa `/opt` ni tekshiraman. `/proc` va `/sys` ga qaramayman — ular diskda joy egallamaydi, kernel ularni xotirada hosil qiladi. O'chirishdan oldin nima joy egallaganini aniq o'lchab olaman.
