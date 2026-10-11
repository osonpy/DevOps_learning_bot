## Tushuncha

Menejer so'raydi: "Kecha saytga eng ko'p qaysi IP'lar murojaat qildi?" Sizda 2 GB'lik access log bor, Excel yo'q, vaqt ham kam. Bunday savollarga terminalda bir qatorlik pipeline bilan javob beriladi: kerakli ustunni ajratasiz, saralaysiz, takrorlarni sanaysiz, eng kattalarini olasiz. Bir necha soniyada.

Bu darsdagi vositalar — `cut`, `sort`, `uniq`, `tr`, `wc`, `paste`, `column` — har biri juda oddiy ishni bajaradi. `cut` ustunni kesib oladi, `sort` saralaydi, `uniq` takrorlarni birlashtiradi, `tr` belgilarni almashtiradi. Ularning kuchi pipe orqali birlashganda ochiladi. Bu xuddi oshxonadagi pichoq, taxta va qozonga o'xshaydi: alohida oddiy, birga — ovqat.

Eng muhim naqsh **"top-N"**:

```text
 ... | sort | uniq -c | sort -rn | head
```

Uni yodlab oling: loglardagi eng ko'p IP, endpoint, xato turi, user agent — hammasi shu shablon bilan topiladi. Faqat birinchi qismi (qaysi ustunni olish) o'zgaradi.

## Qanday ishlaydi

Top-N naqshining har bir bosqichi nima qilishini ko'raylik:

```text
 GET /api      cut -f2     /api        sort     /api        uniq -c     3 /api       sort -rn    3 /api
 GET /login   ────────►    /login    ──────►   /api      ──────────►  1 /login   ─────────►   1 /login
 POST /api                 /api                /api
 GET /api                  /api                /login
```

`uniq` faqat **ketma-ket** turgan bir xil qatorlarni birlashtiradi. Tartibsiz ro'yxatda `/api` uch joyda tarqoq bo'lsa, `uniq -c` uni uch marta "1" deb sanaydi. Shuning uchun undan oldin `sort` shart: u bir xil qatorlarni yonma-yon to'playdi. Ikkinchi `sort -rn` esa natijani son bo'yicha (`-n`) kamayish tartibida (`-r`) saralaydi.

`sort` ning muhim flag'lari:

- `-n` — son sifatida (busiz `10` < `2`, chunki matn sifatida "1" "2" dan oldin keladi).
- `-h` — `512K`, `10M`, `2G` kabi hajmlar (`du -h` chiqishi uchun).
- `-r` — teskari; `-u` — takrorlarni tashlab saralash.
- `-t:` — ajratgich; `-k2,2` — faqat 2-ustun bo'yicha. `-k2` esa "2-ustundan qator oxirigacha" degani — bu farq ko'pincha e'tibordan chetda qoladi.

`cut -d: -f1,7` — `:` bilan ajratilgan 1- va 7-maydonlar. `cut` har bir ajratgich belgisini alohida hisoblaydi: ikki bo'shliq ketma-ket kelsa, ular orasida "bo'sh maydon" bor deb tushunadi. `ps` yoki `ls -l` kabi bo'shliqlar bilan tekislangan chiqishda shuning uchun `cut` o'rniga `awk '{print $2}'` yoki avval `tr -s ' '` ishlatiladi.

`tr` belgilar ustida ishlaydi (so'zlar emas): `tr 'a-z' 'A-Z'` — harflarni kattalashtirish, `tr -d '-'` — belgini o'chirish, `tr -s ' '` — ketma-ket takrorlanganini bittaga siqish.

## Buyruqlar

Natijalar Ubuntu 24.04 konteynerida olingan.

```bash
printf "b\n10\n2\n1\n" | sort
printf "b\n10\n2\n1\n" | sort -n
```
```text
1
10
2
b
b
1
2
10
```
Birinchisi matn tartibi (`10` `2` dan oldin), ikkinchisi son tartibi.

```bash
printf "512K\n2G\n10M\n1K\n" | sort -h
```
```text
1K
512K
10M
2G
```
`-h` birliklarni tushunadi — `du -sh * | sort -h` shu uchun ishlaydi.

```bash
printf "a\nb\na\na\nb\nc\n" | uniq -c
```
```text
      1 a
      1 b
      2 a
      1 b
      1 c
```
`sort` siz: faqat yonma-yon turgan ikki `a` birlashdi.

```bash
printf "a\nb\na\na\nb\nc\n" | sort | uniq -c | sort -rn
```
```text
      3 a
      2 b
      1 c
```
To'liq top-N naqshi.

```bash
cut -d" " -f2 access.txt | sort | uniq -c | sort -rn | head -2
```
```text
      3 /api
      1 /login
```
Sinov logidagi eng ko'p so'ralgan endpoint'lar.

```bash
printf "x 3 z\ny 1 b\nz 2 a\n" | sort -k2,2n
```
```text
y 1 b
z 2 a
x 3 z
```
Faqat 2-ustun, son sifatida.

```bash
line="root      1234  0.5  nginx"
echo "$line" | cut -d" " -f2
echo "$line" | tr -s " " | cut -d" " -f2
echo "$line" | awk '{print $2}'
```
```text

1234
1234
```
Birinchi qator bo'sh: `cut` ikki bo'shliq orasidagi bo'sh maydonni oldi.

```bash
echo "Hello DevOps" | tr "a-z" "A-Z"
echo "12-34-56" | tr -d "-"
```
```text
HELLO DEVOPS
123456
```
Birinchisi har bir kichik harfni mos katta harfga almashtirdi, ikkinchisi `-` belgisini o'chirdi.

```bash
sort -t: -k3,3n /etc/passwd | cut -d: -f1,3 | tail -3
sort -t: -k3,3 /etc/passwd | cut -d: -f1,3 | head -4
```
```text
_apt:42
ubuntu:1000
nobody:65534
root:0
daemon:1
uucp:10
ubuntu:1000
```
`-t:` ajratgichni `:` qiladi, `-k3,3n` — UID maydoni bo'yicha son sifatida (eng katta UID oxirida). Ikkinchi buyruqda `n` yo'q: `10` va `1000` `2` dan oldin keldi — matn tartibi yana "aldadi" (toza `ubuntu:24.04` image'ida olingan).

```bash
printf "name size\nnginx 10M\npostgres 120M\n" | column -t
```
```text
name      size
nginx     10M
postgres  120M
```
Ustunlarni tekislaydi — hisobotni o'qishga qulay qiladi.

```bash
paste -sd, users.txt
```
```text
_apt,backup,bin,daemon,games,irc,list,lp,...
```
Ko'p qatorni bitta qatorga vergul bilan birlashtiradi (`-s` — ketma-ket, `-d,` — ajratgich).

## Odatiy xatolar

- **`uniq` dan oldin `sort` qilmaslik.** Belgi: bir xil qiymat natijada bir necha marta, kichik sonlar bilan chiqadi. Sabab: `uniq` faqat qo'shni qatorlarni solishtiradi. To'g'ri usul: `sort | uniq -c`.
- **Sonlarni `-n` siz saralash.** Belgi: `100` `20` dan oldin turibdi. Sabab: matn tartibi. To'g'ri usul: `sort -n` (hajmlar uchun `-h`).
- **`-k2` ni "faqat 2-ustun" deb o'ylash.** Belgi: teng qiymatlar kutilmagan tartibda. Sabab: `-k2` qator oxirigacha bo'lgan qismni kalit qiladi. To'g'ri usul: `-k2,2` (son bo'lsa `-k2,2n`).
- **Tekislangan chiqishda `cut -d' '`.** Belgi: bo'sh natija yoki noto'g'ri ustun. Sabab: ketma-ket bo'shliqlar bo'sh maydon hosil qiladi. To'g'ri usul: `awk '{print $N}'` yoki `tr -s ' '` dan keyin `cut`.
- **Saralash locale'ga bog'liqligini unutish.** Belgi: ikki serverda bir xil buyruq turli tartib beradi. Sabab: `sort` joriy locale'ning harf tartibidan foydalanadi. To'g'ri usul: skriptlarda barqaror natija uchun `LC_ALL=C sort`.

## Intervyuda

**Savol:** Nginx access log'idan eng ko'p murojaat qilgan 10 ta IP'ni qanday topasiz?

**Namunaviy javob:** Nginx'ning standart formatida IP birinchi maydon, shuning uchun uni `awk '{print $1}'` bilan ajrataman. Keyin `sort | uniq -c | sort -rn | head -10` — saralash bir xil IP'larni yonma-yon qo'yadi, `uniq -c` ularni sanaydi, so'nggi `sort -rn` son bo'yicha kamayish tartibida saralaydi. Log juda katta bo'lsa, avval `grep` bilan kerakli vaqt oralig'ini olib, hajmni kamaytiraman. Natija doimiy kerak bo'lsa, bu tahlilni monitoring tizimiga ko'chirish kerakligini ham aytaman.
