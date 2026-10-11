## Tushuncha

Serverda hamma narsa matn: konfiglar, loglar, buyruqlar chiqishi. Ulardan kerakli qatorni topish — DevOps'ning kundalik ishi. "SSH'ga kim parol tanlab hujum qilyapti?", "konfigda bu sozlama qayerda yoqilgan?", "logda oxirgi soatda nechta 500 xato bor?" — bularning hammasi `grep` dan boshlanadi.

`grep` matnni qatorma-qator o'qib, naqshga mos kelgan qatorlarni chiqaradi. Naqsh oddiy so'z bo'lishi mumkin (`Failed`), lekin asl kuch **regular expression** (regex) da: "har qanday IP manzil", "qator boshidagi `#`", "uch xonali son" kabi qoidalarni yozish mumkin.

Regex'ni birdaniga to'liq o'rganish shart emas. Amalda 10 ga yaqin belgi ishlarning 90 foizini qoplaydi. Muhimi — `grep` qanday "o'ylashini" tushunish: u **qatorlar** bilan ishlaydi, har qatorni naqsh bilan solishtiradi va natijani stdout'ga chiqaradi. Shuning uchun uni pipe'ning istalgan joyiga qo'yish mumkin.

## Qanday ishlaydi

Asosiy flag'lar:

- `-i` — katta-kichik harf farqsiz; `-v` — **mos kelmagan** qatorlar (teskari).
- `-n` — qator raqami; `-c` — mos qatorlar **soni**; `-o` — qatorning faqat mos kelgan qismi.
- `-r` — papka ichida rekursiv; `-l` — faqat fayl nomlari.
- `-A 3` / `-B 3` / `-C 3` — topilgan qatordan keyingi / oldingi / atrofidagi 3 qator.
- `-E` — kengaytirilgan regex; `-F` — naqshni regex emas, oddiy matn deb qidirish; `-w` — butun so'z.

Regex asoslari:

```text
 ^        qator boshi            ^#        — # bilan boshlanadigan qator
 $        qator oxiri            ^$        — bo'sh qator
 .        istalgan bitta belgi   a.c       — abc, a-c, a1c
 *        oldingisi 0+ marta     ab*       — a, ab, abbb
 +        oldingisi 1+ marta     [0-9]+    — bir yoki ko'p raqam   (-E bilan)
 {n,m}    n dan m martagacha     [0-9]{1,3}                         (-E bilan)
 [abc]    to'plamdan bitta       [0-9] diapazon, [^0-9] — raqam emas
 (a|b)    yoki                   (GET|POST)                         (-E bilan)
 \b       so'z chegarasi         \bcat\b   — "cat", lekin "category" emas
 \s       bo'shliq belgisi
```

**BRE va ERE farqi.** Standart `grep` "basic" regex (BRE) ishlatadi: unda `+`, `?`, `{}`, `|`, `()` oddiy belgi sifatida qabul qilinadi. `-E` (extended, ERE) bilan ular maxsus ma'noga ega bo'ladi. Shuning uchun `grep "ab+"` so'zma-so'z "ab+" ni qidiradi, `grep -E "ab+"` esa "ab, abb, abbb" ni. GNU grep BRE'da `\+` ni ham tushunadi, lekin `-E` aniqroq va boshqa vositalarga ko'chiriladi.

Nuqta regex'da "istalgan belgi" ekanini unutmang: `grep "1.2.3.4"` — `1x2y3z4` ga ham mos keladi. Aniq matn kerak bo'lsa — `-F`.

**Exit code.** `grep` topsa `0`, topmasa `1`, xato (masalan, fayl yo'q) bo'lsa `2` qaytaradi. Skriptlarda `grep -q` (hech narsa chiqarmay faqat kod qaytarish) bilan shart tekshiriladi: `if grep -q "^PermitRootLogin no" /etc/ssh/sshd_config; then ...`.

## Buyruqlar

Natijalar Ubuntu 24.04 konteynerida, sinov uchun yaratilgan `auth.log` da olingan (IP'lar hujjatlar uchun ajratilgan diapazonlardan).

```bash
grep -c "Failed password" auth.log
```
```text
3
```
Mos kelgan **qatorlar** soni.

```bash
grep "Failed password" auth.log | grep -Eo "([0-9]{1,3}\.){3}[0-9]{1,3}"
```
```text
203.0.113.7
198.51.100.23
203.0.113.7
```
Har qatordan faqat IP qismi (`-o`). `\.` — haqiqiy nuqta, `{3}` — "raqam va nuqta" guruhi uch marta. Bu regex 999.1.1.1 ni ham qabul qiladi — log tahlili uchun yetarli, validatsiya uchun emas.

```bash
echo aaa | grep -c a
echo aaa | grep -o a | wc -l
```
```text
1
3
```
`-c` qatorlarni sanaydi, topilmalarni emas. Topilmalar soni kerak bo'lsa — `-o | wc -l`.

```bash
grep -n -i "accepted" auth.log
```
```text
3:Oct 11 09:02:11 vps sshd[1210]: Accepted publickey for deploy from 192.0.2.10 port 50000 ssh2
```
Qator raqami bilan, harf katta-kichikligiga qaramay.

```bash
grep -v "^#" sshd_test | grep -v "^$"
```
```text
Port 22
PermitRootLogin no
   # indent izoh
```
Izoh va bo'sh qatorlarsiz konfig. Lekin bo'shliq bilan boshlangan izoh o'tib ketdi.

```bash
grep -Ev "^\s*(#|$)" sshd_test
```
```text
Port 22
PermitRootLogin no
```
Bitta ERE bilan: qator boshida ixtiyoriy bo'shliq, keyin `#` yoki qator oxiri.

```bash
grep -rn "PermitRootLogin" /etc/ssh/
```
Rekursiv qidiruv fayl nomi va qator raqami bilan, masalan `cfg/a.conf:1:PermitRootLogin no`. Ubuntu 24.04 da `sshd_config` ning 12-qatorida `Include /etc/ssh/sshd_config.d/*.conf` bor, ya'ni sozlama shu papkadagi fayllarda ham bo'lishi mumkin — shuning uchun butun papka qidiriladi.

```bash
sudo sshd -T | grep -i "^permitrootlogin"
```
```text
permitrootlogin no
```
`grep` fayllardagi **yozuvni** topadi, `sshd -T` esa barcha fayllar birlashtirilgandan keyingi **amaldagi** qiymatni chiqaradi. Tekshiruvda asosiy faylda faqat izoh (`#PermitRootLogin prohibit-password`) bor edi, haqiqiy qiymat `sshd_config.d/` dagi fayldan kelgan.

```bash
grep -C1 ERR app.log
```
```text
2
ERR
4
```
Xato atrofidagi kontekst — ko'pincha sabab xatodan oldingi qatorda.

```bash
grep -F "1.2.3.4" ips
```
```text
ip 1.2.3.4
```
`-F` siz `ip 1x2y3z4` ham chiqqan edi.

## Odatiy xatolar

- **Naqshni qo'shtirnoqsiz yozish.** Belgi: `grep Failed password auth.log` → `grep: password: No such file or directory`. Sabab: shell bo'shliq bo'yicha bo'ldi, `password` fayl nomi deb tushunildi. To'g'ri usul: naqshni doim qo'shtirnoqqa oling; `$` va `\` ko'p bo'lsa — bittalik qo'shtirnoq.
- **`+` va `{}` ni `-E` siz ishlatish.** Belgi: aniq bor narsa topilmaydi. Sabab: BRE'da ular oddiy belgi. To'g'ri usul: `grep -E`.
- **`-c` ni topilmalar soni deb o'ylash.** Belgi: bitta qatorda 3 marta uchragan so'z uchun `1`. Sabab: `-c` qatorlarni sanaydi. To'g'ri usul: `grep -o naqsh | wc -l`.
- **Nuqtani ekranlamaslik.** Belgi: IP yoki domen qidirganda ortiqcha qatorlar. Sabab: `.` — istalgan belgi. To'g'ri usul: `\.` yoki `-F`.
- **Faqat `^#` ni olib tashlash.** Belgi: "faol" sozlamalar orasida izohlar qolgan. Sabab: izoh bo'shliq bilan boshlangan. To'g'ri usul: `^\s*#`.

## Intervyuda

**Savol:** Logdan xato qatorlarni topdingiz, lekin sababi ko'rinmayapti. `grep` bilan qanday davom etasiz?

**Namunaviy javob:** Avval kontekst olaman: `grep -B 5 -A 5 "ERROR" app.log` xato oldidan va keyingi qatorlarni ko'rsatadi, sabab ko'pincha oldingi qatorlarda bo'ladi. Keyin qidiruvni toraytiraman — vaqt oralig'i, so'rov ID yoki foydalanuvchi bo'yicha — va keraksiz shovqinni `grep -v` bilan olib tashlayman. Takrorlanishni bilish uchun natijani `sort | uniq -c` ga uzataman. Murakkab naqshlar uchun `-E` ishlataman, aniq matn uchun esa `-F`, chunki u tezroq va nuqta kabi belgilar bilan muammo bermaydi.
