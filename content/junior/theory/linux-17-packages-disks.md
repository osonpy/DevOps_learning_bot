## Tushuncha

Serverni boshqarishning ikki "xo'jalik" tomoni bor: **dasturlar** (nima o'rnatilgan, qaysi versiya, xavfsizlik yangilanishlari olinyaptimi) va **disklar** (qancha joy bor, qaysi disk qayerga ulangan, reboot'dan keyin hammasi joyidami). Ikkalasi ham kamdan-kam o'ylanadi — to biror narsa buzilmaguncha. Shuning uchun ularni oldindan to'g'ri sozlash kerak.

Ubuntu'da dasturlar **paketlar** orqali o'rnatiladi. Paket — dastur fayllari, ularning qayerga joylashishi, bog'liqliklari va o'rnatish skriptlari bitta arxivda (`.deb`). Paketlarni **repozitoriylardan** `apt` yuklab oladi. Bu qo'lda yuklab o'rnatishdan ancha xavfsiz: paketlar imzolangan, bog'liqliklar avtomatik hal bo'ladi, xavfsizlik yangilanishlari bitta buyruq bilan keladi.

Disklar tomonida eng muhim fikr: **"bo'sh joy" ikki xil tugaydi**. Baytlar tugashi mumkin (`df -h`) va **inode'lar** tugashi mumkin (`df -i`). Inode — har bir fayl uchun ajratiladigan yozuv; ularning soni fayl tizimi yaratilganda belgilanadi. Millionlab mayda fayl (sessiya, kesh, mail navbati) inode'larni tugatadi va disk "50% bo'sh" bo'lsa ham yangi fayl yaratib bo'lmaydi.

## Qanday ishlaydi

**apt** ikki bosqichda ishlaydi:

```text
 apt update    repozitoriylardan "qaysi paketlarning qaysi versiyasi bor" ro'yxatini yangilaydi
               (hech narsa o'rnatmaydi!)
 apt upgrade   o'rnatilgan paketlarni ro'yxatdagi yangi versiyalarga ko'taradi
 apt install   yangi paket (bog'liqliklari bilan);  remove — o'chirish, purge — konfiglari bilan
```

`apt-cache policy paket` — o'rnatilgan va mavjud versiyalarni hamda ular qaysi repozitoriydan kelishini ko'rsatadi. `dpkg` — past darajadagi vosita: `dpkg -L paket` paket qaysi fayllarni o'rnatganini, `dpkg -S /yo'l` esa fayl qaysi paketdan kelganini ko'rsatadi. `apt-mark hold` paket versiyasini qotiradi — masalan, ma'lumotlar bazasi rejalashtirilmagan katta yangilanishga o'tib ketmasligi uchun.

**unattended-upgrades** xavfsizlik yangilanishlarini avtomatik o'rnatadi. Uning yoqilganligi `/etc/apt/apt.conf.d/20auto-upgrades` faylida ko'rinadi. Ko'p cloud image'larda u oldindan o'rnatilgan bo'ladi — o'zingiznikida `systemctl status unattended-upgrades` bilan tekshirib ko'ring.

**Disklar**: `lsblk` — qurilmalar va bo'limlar daraxti, `df -h` — ulangan fayl tizimlari va bo'sh joy, `findmnt` — nima qayerga ulangan. Boot paytida nima ulanishi `/etc/fstab` da yoziladi, har qator 6 maydon:

```text
 # qurilma                                  mount nuqta  tur   opsiyalar        dump pass
 UUID=3f1c...-9a2b                          /mnt/data    ext4  defaults,nofail  0    2
 /swapfile                                  none         swap  sw               0    0
```

Qurilmani `/dev/sdb` deb emas, **UUID** bilan ko'rsatish kerak: disk nomlari qurilmalar topilish tartibiga bog'liq va reboot'da almashishi mumkin, UUID esa fayl tizimining o'zida yozilgan (uni `blkid` ko'rsatadi). `nofail` — disk topilmasa ham boot davom etsin. fstab'dagi xato serverni boot paytida emergency rejimga tushirishi mumkin, shuning uchun o'zgartirgandan keyin reboot'dan oldin tekshirish shart.

**Swap** — RAM tugaganda xotira sahifalari vaqtincha yoziladigan disk maydoni. U RAM'dan ancha sekin, lekin kichik VPS'da (1–2 GB RAM) OOM killer servislarni o'ldirishidan saqlab qolishi mumkin. Swap fayl yaratishda to'rt qadam bor: joy ajratish, huquqni 600 qilish (fayl ichida xotira mazmuni bo'ladi), `mkswap` bilan formatlash va `swapon` bilan yoqish; doimiy qilish — fstab qatori.

## Buyruqlar

Natijalar Ubuntu 24.04 konteynerida olingan; disk qurilmalari bilan bog'liq natijalar konteynerda host'nikini ko'rsatgani uchun ularni keltirmadim.

```bash
apt-cache policy nginx | head -6
```
```text
nginx:
  Installed: (none)
  Candidate: 1.24.0-2ubuntu7.18
  Version table:
     1.24.0-2ubuntu7.18 500
        500 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages
```
O'rnatilmagan (`none`), o'rnatilsa qaysi versiya kelishi (`Candidate`) va manbasi (`noble-updates`).

```bash
dpkg -L tree | head -5
dpkg -S /usr/bin/namei
```
```text
/.
/usr
/usr/bin
/usr/bin/tree
/usr/share
util-linux: /usr/bin/namei
```
Paketning fayllari va faylning paketi — "bu binary qayerdan kelgan?" savoliga javob.

```bash
apt-mark hold tree && apt-mark showhold && apt-mark unhold tree
```
```text
tree set on hold.
tree
Canceled hold on tree.
```
Versiyani qotirish va bo'shatish.

```bash
apt list --upgradable
```
```text
Listing...
libaudit-common/noble-updates 1:3.1.2-2.1ubuntu0.1 all [upgradable from: 1:3.1.2-2.1build1.1]
...
```
`apt update` dan keyin nimalar yangilanishi mumkinligi.

```bash
cat /etc/apt/apt.conf.d/20auto-upgrades
```
```text
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
```
Ikkalasi `"1"` — har kuni ro'yxat yangilanadi va xavfsizlik yangilanishlari o'rnatiladi.

```bash
df -i /
```
```text
Filesystem       Inodes   IUsed    IFree IUse% Mounted on
overlay        31137792 2653148 28484644    9% /
```
Inode'lar: jami, ishlatilgan, bo'sh. `IUse%` 100% bo'lsa — joy bo'lsa ham fayl yaratib bo'lmaydi.

```bash
lsblk
```
```text
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
vda    253:0    0   25G  0 disk
├─vda1 253:1    0   24G  0 part /
└─vda15 253:15  0  106M  0 part /boot/efi
vdb    253:16   0   10G  0 disk
```
Namuna (tipik VPS, tekshirilmagan): `vdb` — ulangan, lekin hali formatlanmagan va mount qilinmagan ikkinchi disk.

```bash
sudo mount -a && findmnt --verify
```
```text
Success, no errors or warnings detected
```
fstab'ni reboot'siz sinash: `mount -a` hamma yozuvni ulashga urinadi, `findmnt --verify` sintaksis va qurilmalarni tekshiradi (natija konteynerda olingan).

## Odatiy xatolar

- **`apt upgrade` ni `apt update` siz.** Belgi: "0 upgraded", garchi yangilanishlar chiqqan bo'lsa ham. Sabab: paketlar ro'yxati eski. To'g'ri usul: avval `apt update`.
- **Disk "bo'sh", lekin `No space left on device`.** Belgi: `df -h` 40% band ko'rsatadi. Sabab: inode'lar tugagan. To'g'ri usul: `df -i`, keyin millionlab mayda fayllar qayerda ekanini toping.
- **fstab'da `/dev/sdX` va tekshiruvsiz reboot.** Belgi: reboot'dan keyin server emergency rejimda yoki disk boshqa joyga ulangan. Sabab: qurilma nomi almashdi yoki qatorda xato. To'g'ri usul: UUID, ixtiyoriy disklar uchun `nofail`, reboot'dan oldin `mount -a` va `findmnt --verify`.
- **Swap faylni 644 qoldirish.** Belgi: `swapon` huquqlar haqida ogohlantiradi. Sabab: swap'da xotira mazmuni (parollar, kalitlar) bo'lishi mumkin. To'g'ri usul: `chmod 600`.
- **Qo'lda o'rnatilgan dasturni unutish.** Belgi: `apt upgrade` hamma narsani yangiladi, lekin `/usr/local/bin` dagi binary yillar davomida eski. Sabab: paket menejeridan tashqari o'rnatilgan. To'g'ri usul: imkon qadar paket yoki rasmiy repozitoriy ishlating, qo'lda o'rnatilganlarni hujjatlashtiring.

## Intervyuda

**Savol:** Server diskida 30% joy bor, lekin ilova "No space left on device" xatosini beryapti. Nimani tekshirasiz?

**Namunaviy javob:** Birinchi navbatda `df -i` bilan inode'larni tekshiraman — ko'p mayda fayl inode'larni tugatgan bo'lishi mumkin, bu holatda baytlar bo'lsa ham yangi fayl yaratib bo'lmaydi. Agar inode'lar joyida bo'lsa, ilova aynan qaysi papkaga yozayotganini va u boshqa, to'lib qolgan fayl tizimiga ulanmaganini `df -h <yo'l>` yoki `findmnt` bilan ko'raman. O'chirilgan, lekin ochiq turgan katta fayllarni ham tekshiraman. Sababni topgach, mayda fayllarni manbasida tozalaydigan yoki aylantiradigan doimiy yechim qilaman.
