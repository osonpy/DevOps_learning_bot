## Tushuncha

Fayllar bilan ishlash — har kunlik ish: deploy uchun papka tayyorlash, konfig nusxasini olish, eski relizni o'chirish. Grafik muhitda buni sichqoncha bilan qilasiz, terminalda esa bir nechta qisqa buyruq bilan — va ko'pincha tezroq, chunki bitta buyruq yuzlab fayl ustida ishlay oladi.

Muhim farq: Linux terminalida **savatcha yo'q**. `rm` o'chirgan fayl darhol yo'qoladi, "bekor qilish" tugmasi ham yo'q. Shuning uchun tajribali muhandislar ikkita odatga ega: o'chirishdan oldin nima tanlanishini ko'rib olish va muhim narsaning zaxirasini saqlash.

Ikkinchi asosiy g'oya — **wildcard'lar** (globbing). `*.log` yozganingizda bu yulduzchani `rm` yoki `ls` emas, **shell** ochib beradi: buyruq ishga tushishidan oldin mos fayllar ro'yxatiga almashtiriladi. Ya'ni `rm *.log` aslida `rm app-1.log app-2.log app-3.log` bo'lib bajariladi. Bu oddiy tuyuladi, lekin ko'p xatolarning ildizi shu yerda.

Uchinchisi — **symlink** (ramziy havola). U boshqa fayl yoki papkaga ko'rsatuvchi "yorliq". Deploy'larda klassik naqsh: har reliz alohida papkada (`releases/v1`, `releases/v2`), `current` esa joriy relizga symlink. Yangi versiya chiqarish — symlinkni boshqa papkaga burish, rollback — eskisiga qaytarish.

## Qanday ishlaydi

Shell kengaytirishlari tartib bilan bajariladi. Siz uchun eng muhimlari:

```text
 Siz yozgan qator:     touch app-{1..3}.log ; ls app-[2-3].log
 1) brace expansion:   app-{1..3}.log  →  app-1.log app-2.log app-3.log
                       (fayl bormi-yo'qmi farqi yo'q — shunchaki matn hosil qiladi)
 2) globbing:          app-[2-3].log   →  mavjud fayllardan mos keladiganlari
 3) buyruq ishga tushadi va tayyor ro'yxatni oladi
```

Glob belgilari: `*` — istalgan belgilar (bo'sh ham), `?` — aynan bitta belgi, `[abc]` yoki `[2-4]` — to'plamdan bitta belgi. `{a,b}` va `{1..5}` esa glob emas, **brace expansion**: u fayl tizimiga qaramaydi, shuning uchun yangi fayl va papkalar yaratishda ishlatiladi.

Ikki muhim qoida:

- Glob nomi nuqta bilan boshlanadigan **yashirin fayllarni** tanlamaydi (`.env`, `.hidden.log`).
- Hech narsa mos kelmasa, bash naqshni **o'zgartirmasdan** buyruqqa beradi. `rm *.txt` papkada .txt bo'lmasa, `rm` ga aynan `*.txt` degan nom yetib boradi.

Symlink faylda boshqa yo'lning matnini saqlaydi. **Nisbiy** symlink link turgan papkaga nisbatan hisoblanadi, siz turgan papkaga emas. `ln -s releases/v2 current` buyrug'ini `app` papkasida bersangiz, `current` faqat `app/releases/v2` mavjud bo'lsa ishlaydi.

Ubuntu 24.04 dagi GNU `ln` mavjud linkni `ln -sfn` bilan almashtirganda avval vaqtinchalik nom bilan yangi symlink yaratadi, keyin uni `rename` bilan ustiga qo'yadi. `rename` atomik bo'lgani uchun `current` hech bir lahzada "yo'q" bo'lib qolmaydi — buni strace bilan ko'rish mumkin (pastda). `-n` flag'i muhim: busiz `current` papkaga ko'rsatgan bo'lsa, `ln` yangi linkni o'sha papkaning **ichiga** yaratadi.

Symlinkni **hard link** bilan adashtirmang. Hard link (`ln` flag'siz) — bitta faylning ikkinchi nomi: ikkalasi bir xil inode'ga (diskdagi fayl yozuviga) ishora qiladi. Asl nomni o'chirsangiz ham ma'lumot ikkinchi nom orqali ochilaveradi; symlink esa bu holda "singan" bo'lib qoladi. Hard link papkalar uchun ham, boshqa fayl tizimiga ham ishlamaydi, shuning uchun deploy'larda deyarli doim symlink ishlatiladi.

```bash
echo data > orig && ln orig hard && ln -s orig soft
ls -li orig hard soft
rm orig; cat hard; cat soft
```
```text
13786477 -rw-r--r-- 2 root root 5 Oct 11 10:43 hard
13786477 -rw-r--r-- 2 root root 5 Oct 11 10:43 orig
13786478 lrwxrwxrwx 1 root root 4 Oct 11 10:43 soft -> orig
data
cat: soft: No such file or directory
```
Birinchi ustun — inode raqami: `orig` va `hard` da bir xil, link soni `2`. `orig` o'chgach `hard` ishlaydi, `soft` esa yo'q.

## Buyruqlar

Natijalar Ubuntu 24.04 konteynerida olingan.

```bash
mkdir -p /tmp/a/b/c && ls -R /tmp/a
```
```text
/tmp/a:
b

/tmp/a/b:
c

/tmp/a/b/c:
```
`-p` (parents) yo'q oraliq papkalarni ham yaratadi va papka allaqachon bor bo'lsa xato bermaydi.

```bash
mkdir /tmp/x/y/z
```
```text
mkdir: cannot create directory '/tmp/x/y/z': No such file or directory
```
`-p` siz — `x` va `y` yo'qligi uchun xato.

```bash
echo app-{1..3}.log
```
```text
app-1.log app-2.log app-3.log
```
Brace expansion: fayl yaratmaydi, faqat matn hosil qiladi. `touch` yoki `mkdir` bilan birga ishlatiladi.

```bash
touch app-1.log app-2.log app-3.log .hidden.log
echo *.log
echo app-?.log
echo nomatch-*.txt
```
```text
app-1.log app-2.log app-3.log
app-1.log app-2.log app-3.log
nomatch-*.txt
```
`.hidden.log` tanlanmadi, mos kelmagan naqsh esa o'zgarmay qoldi. `echo` bilan glob natijasini xavfsiz ko'rish — eng yaxshi odat.

```bash
cp -r config config.bak
mv app.conf app.conf.old
rm -r old-release
```
`cp -r` papkani ichidagilari bilan nusxalaydi; `mv` ko'chiradi yoki qayta nomlaydi (bir xil buyruq); `rm -r` papkani o'chiradi. `-i` qo'shsangiz har fayl uchun tasdiq so'raydi.

```bash
ln -s releases/v2 current && ls -l current && readlink -f current
```
```text
lrwxrwxrwx 1 root root 11 Oct 11 10:36 current -> releases/v2
/tmp/rel/releases/v2
```
`ls -l` link qayerga ko'rsatishini, `readlink -f` esa oxirgi haqiqiy yo'lni ko'rsatadi.

```bash
strace -e trace=symlinkat,renameat ln -sfn releases/v1 current
```
```text
symlinkat("releases/v1", AT_FDCWD, "current") = -1 EEXIST (File exists)
symlinkat("releases/v1", AT_FDCWD, "Cu1vc5DT") = 0
renameat(AT_FDCWD, "Cu1vc5DT", AT_FDCWD, "current") = 0
```
Vaqtinchalik nomdagi link yaratilib, `rename` bilan almashtirildi. `strace` standart o'rnatilmagan, bu faqat ichki mexanizmni ko'rish uchun.

## Odatiy xatolar

- **`rm` dan oldin tekshirmaslik.** Belgi: keraksiz fayllar bilan birga keraklilari ham ketdi. Sabab: glob kutilganidan ko'proq faylga mos keldi. To'g'ri usul: avval aynan o'sha naqsh bilan `ls` yoki `echo`, natijani o'qing, keyin o'qini yuqoriga bosib `ls` ni `rm` ga almashtiring.
- **`rm -rf $DIR/` dagi bo'sh o'zgaruvchi.** Belgi: skript kutilmagan papkani o'chirdi. Sabab: `DIR` bo'sh qolgan va buyruq `rm -rf /` ga aylangan. To'g'ri usul: skriptda `set -u`, `"${DIR:?}"` kabi tekshiruv va doim qo'shtirnoq.
- **Nisbiy symlink "singan".** Belgi: `cat link` → `No such file or directory`, `ls -l` esa linkni ko'rsatadi. Sabab: link boshqa papkada yaratilgan, nisbiy yo'l endi hech qayerga ko'rsatmaydi. To'g'ri usul: `readlink -f` bilan tekshiring; link papkasidan turib nisbiy yo'l yozing yoki absolute yo'l ishlating.
- **`ln -sf` ni `-n` siz papka linkiga ishlatish.** Belgi: `current` o'zgarmadi, `releases/v1/v2` kabi kutilmagan link paydo bo'ldi. Sabab: `ln` mavjud papka-linkni papka deb tushundi. To'g'ri usul: papkaga ko'rsatuvchi linklar uchun `ln -sfn`.
- **Bo'shliqli fayl nomlari.** Belgi: `rm my file.txt` ikki faylni qidiradi. Sabab: shell bo'shliq bo'yicha so'zlarga ajratadi. To'g'ri usul: `"my file.txt"` yoki `my\ file.txt`.

## Intervyuda

**Savol:** Deploy'da `current` symlinkdan nima uchun foydalaniladi va rollback qanday bo'ladi?

**Namunaviy javob:** Har bir reliz alohida, o'zgarmaydigan papkaga yoziladi, servis esa doim `current` yo'lidan ishlaydi. Yangi reliz to'liq tayyor bo'lgach, `current` yangi papkaga buriladi — bu bir zumlik operatsiya, foydalanuvchi yarim ko'chirilgan fayllarni ko'rmaydi. Rollback uchun linkni oldingi reliz papkasiga qaytarish va servisni qayta yuklash kifoya. Linkni almashtirishni atomik qilish muhim, shuning uchun men `ln -sfn` yoki "vaqtinchalik link + `mv -T`" naqshidan foydalanaman va eski relizlardan bir nechtasini saqlab qolaman.
