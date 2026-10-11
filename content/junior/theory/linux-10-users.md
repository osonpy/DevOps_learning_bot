## Tushuncha

Yangi VPS sotib olganingizda sizga root paroli yoki kaliti beriladi va hamma narsani root bilan qilish oson tuyuladi. Lekin jamoada ishlaganda, servislar ko'payganda va xavfsizlik auditi kelganda bu odat qimmatga tushadi. Root bilan qilingan xato butun serverni buzadi, root sifatida ishlayotgan servis buzib kirilsa — hujumchi hamma narsani oladi, loglarda esa "kim nima qildi" degan savolga javob qolmaydi.

Linux bu muammoni **foydalanuvchilar va guruhlar** bilan hal qiladi. Har bir odam o'z akkaunti bilan kiradi, har bir servis o'z **system user**'i bilan ishlaydi (`www-data` — nginx, `postgres` — PostgreSQL). Shunda nginx buzib kirilsa ham, hujumchi faqat `www-data` qila oladigan narsalarni qila oladi. Bu **least privilege** (eng kam huquq) tamoyili — DevOps xavfsizligining asosi.

Administrator ishlari uchun esa root'ga doimiy kirish o'rniga **sudo** ishlatiladi: oddiy user kerakli paytda, kerakli buyruqni root huquqi bilan bajaradi, har bir urinish logga yoziladi. Yaxshi sozlangan serverda root bilan SSH orqali kirish umuman o'chirilgan bo'ladi.

## Qanday ishlaydi

Kernel uchun foydalanuvchi — bu **raqam** (UID). Nomlar faqat odamlar uchun. Root — UID `0`, va kernel aynan shu raqamga qarab cheklovlarni olib tashlaydi. Ma'lumotlar uchta faylda:

```text
/etc/passwd   carol:x:1002:1002::/home/carol:/bin/bash
              nom : parol joyi : UID : GID : izoh : uy papkasi : login shell
/etc/shadow   parol xeshlari — faqat root (va shadow guruhi) o'qiy oladi
/etc/group    guruh nomi, GID va a'zolari
```

`/etc/passwd` dagi `x` — "parol shadow faylda" degani. `/etc/passwd` hamma uchun o'qiladi (`ls` nomlarni ko'rsatishi uchun kerak), `/etc/shadow` esa yopiq (`-rw-r-----`).

Ubuntu'da (`/etc/login.defs`) oddiy userlar UID 1000 dan boshlanadi, undan pastdagilar system userlar uchun. `useradd -r` bilan yaratilgan system user tekshiruvda UID 999 oldi.

Har bir user'ning bitta **asosiy guruhi** (GID) va bir nechta **qo'shimcha guruhlari** bo'ladi. Fayl huquqlari va `sudo` ruxsati ko'pincha guruh orqali beriladi: Ubuntu'da `sudo` guruhi a'zolari sudo qila oladi (RHEL'da bu `wheel`). Muhim nuance: guruh o'zgarishi **yangi login'dan keyin** kuchga kiradi — ishlab turgan sessiya eski ro'yxat bilan qoladi.

`sudo` qoidalari `/etc/sudoers` va `/etc/sudoers.d/` ichidagi fayllarda. Qoida shakli: `kim  qayerda=(kim_nomidan)  [NOPASSWD:] buyruq`. Ubuntu'dagi `/etc/sudoers` oxirida `@includedir /etc/sudoers.d` qatori bor, lekin bu papkadagi fayl nomida **nuqta bo'lsa yoki `~` bilan tugasa, u e'tiborga olinmaydi** — tekshiruvda `carol.conf` ishlamadi, `carol` esa darhol ishladi.

## Buyruqlar

Natijalar Ubuntu 24.04 konteynerida olingan.

```bash
id root
```
```text
uid=0(root) gid=0(root) groups=0(root)
```
UID, asosiy guruh va barcha guruhlar.

```bash
useradd bob && grep ^bob: /etc/passwd && ls -d /home/bob
```
```text
bob:x:1001:1001::/home/bob:/bin/sh
ls: cannot access '/home/bob': No such file or directory
```
Past darajali `useradd` flag'larsiz uy papka yaratmaydi va shell'ni `/bin/sh` qiladi. Shuning uchun:

```bash
useradd -m -s /bin/bash carol
```
`-m` — uy papka, `-s` — shell. Ubuntu'dagi `adduser` esa interaktiv "do'stona" o'ram: uy papka yaratadi, parol so'raydi — qo'lda user qo'shishda qulay.

```bash
usermod -aG devs carol; id carol
usermod -G docker carol; id carol
```
```text
uid=1002(carol) gid=1002(carol) groups=1002(carol),1004(devs)
uid=1002(carol) gid=1002(carol) groups=1002(carol),1003(docker)
```
`-aG` qo'shdi; `-a` siz `-G` esa ro'yxatni **almashtirdi** — `devs` dan chiqarib yubordi.

```bash
su carol -c "id -Gn; sleep 2; id -Gn"   # shu payt boshqa oynada: usermod -aG devs carol
```
```text
carol
carol
```
Ishlab turgan sessiya yangi guruhni ko'rmadi; qayta kirgandan keyin `carol devs` chiqdi.

```bash
useradd -r -s /usr/sbin/nologin appsvc
su - appsvc -c id
```
```text
This account is currently not available.
```
System user, interaktiv kirish yo'q — servislar uchun to'g'ri sozlama.

```bash
cd /tmp
su carol -c pwd
su - carol -c pwd
sudo -u carol whoami
```
```text
/tmp
/home/carol
carol
```
`su user` faqat foydalanuvchini almashtiradi va joriy papka hamda muhitni saqlaydi. `su - user` esa to'liq login qiladi: uy papkaga o'tadi, muhit o'zgaruvchilari tozalanadi. `sudo -u user buyruq` bitta buyruqni boshqa user nomidan bajaradi — masalan `sudo -u postgres psql`; root shell kerak bo'lsa — `sudo -i`.

```bash
echo "carol ALL=(root) NOPASSWD: /usr/bin/systemctl reload cron" > /etc/sudoers.d/carol
chmod 440 /etc/sudoers.d/carol
visudo -cf /etc/sudoers.d/carol
sudo -l -U carol
```
```text
/etc/sudoers.d/carol: parsed OK
User carol may run the following commands on 76ba695989ff:
    (root) NOPASSWD: /usr/bin/systemctl reload cron
```
Bitta aniq buyruqqa parolsiz ruxsat. Buyruq **to'liq yo'l** bilan yoziladi (`command -v systemctl` → `/usr/bin/systemctl`), `sudo -l` esa natijani tekshiradi. Haqiqiy serverda faylni to'g'ridan-to'g'ri emas, `visudo -f` bilan tahrirlang.

```bash
visudo -cf /tmp/bad
```
```text
/tmp/bad:1:17: syntax error
carol ALL=(root NOPASSWD: x
                ^~~~~~~~~
```
`visudo` xatoni saqlashdan oldin topadi.

## Odatiy xatolar

- **`usermod -G` da `-a` ni unutish.** Belgi: user `sudo` yoki `docker` guruhidan "yo'qolib qoldi". Sabab: `-G` ro'yxatni almashtiradi. To'g'ri usul: doim `usermod -aG guruh user`.
- **Guruhga qo'shib, darhol tekshirish.** Belgi: `docker ps` hali ham `permission denied`. Sabab: sessiya eski guruhlar bilan. To'g'ri usul: chiqib qayta kiring (yoki `newgrp guruh`), keyin `id` bilan tekshiring.
- **sudoers'ni oddiy muharrir bilan tahrirlash.** Belgi: `sudo` umuman ishlamay qoldi, `syntax error` chiqadi. Sabab: bitta xato sudoers butun faylni o'qib bo'lmas qiladi. To'g'ri usul: `visudo` / `visudo -f`, alohida sessiyada root ochiq tursin.
- **`sudoers.d` faylini kengaytma bilan nomlash.** Belgi: qoida yozilgan, lekin `sudo -l` uni ko'rmaydi. Sabab: nuqtali nomlar e'tiborga olinmaydi. To'g'ri usul: `/etc/sudoers.d/deploy` kabi nuqtasiz nom.
- **`authorized_keys` huquqlari juda ochiq.** Belgi: kalit to'g'ri, lekin SSH parol so'raydi. Sabab: sshd xavfsizlik uchun boshqalar yoza oladigan `.ssh` papka yoki faylni rad etadi. To'g'ri usul: `.ssh` — 700, `authorized_keys` — 600, egasi — user'ning o'zi.

## Intervyuda

**Savol:** Nima uchun servislar alohida system user bilan ishlaydi va uni qanday yaratasiz?

**Namunaviy javob:** Bu least privilege tamoyili: servis buzib kirilsa, hujumchi faqat o'sha user'ning huquqlarini oladi — root'ni emas, boshqa servislar fayllarini ham emas. System user'ni `useradd -r -s /usr/sbin/nologin` bilan yarataman: UID system diapazonida bo'ladi va interaktiv kirish yo'q. Keyin unga faqat kerakli papkalarga huquq beraman va systemd unit'da `User=` bilan ko'rsataman. Sudo kerak bo'lsa, umumiy `ALL` emas, `sudoers.d` da aniq buyruqni to'liq yo'l bilan ruxsat beraman va `visudo -c` bilan tekshiraman.
