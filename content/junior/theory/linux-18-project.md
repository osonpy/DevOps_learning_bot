## Tushuncha

Uch hafta davomida alohida g'ishtlarni o'rgandingiz: fayl tizimi, foydalanuvchilar, ruxsatlar, jarayonlar, signallar, systemd, loglar. Bu loyihada ulardan bitta uy quriladi — kichik ilovani **production'dagidek** ishga tushirasiz. "Ishlayapti" va "production'ga tayyor" orasidagi farqni his qilish — bu modulning asosiy natijasi.

"Production'dagidek" nimani anglatadi? Oddiy savollar ro'yxati bilan tekshirib ko'ring:

- Ilova kim nomidan ishlaydi? Buzib kirilsa, hujumchi nimaga ega bo'ladi?
- Maxfiy sozlamalar (parollar, tokenlar) qayerda va ularni kim o'qiy oladi?
- Ilova yiqilsa nima bo'ladi? Server qayta yuklansa-chi?
- Uning loglari qayerda, ular diskni to'ldirmaydimi?
- Boshqa odam (yoki olti oydan keyingi siz) uni README bo'yicha qayta o'rnata oladimi?

Har bir savolga oldingi darslarning birida javob bor. Loyiha ularni bir joyga yig'ishingizni talab qiladi. Ish beruvchilar aynan shu ko'nikmani qidiradi: buyruqlarni bilish emas, ularni ishonchli tizimga birlashtira olish.

## Qanday ishlaydi

Maqsadli arxitektura:

```text
 systemd (PID 1, root)
   │  EnvironmentFile=/srv/app/.env  ← root o'qiydi, ilovaga o'zgaruvchi sifatida beradi
   │  User=appsvc, Restart=on-failure
   ▼
 uvicorn (appsvc, nologin)  ──► 127.0.0.1:8000  ◄── curl / keyinchalik nginx (reverse proxy)
   │  stdout/stderr
   ▼
 journald  ──►  journalctl -u app
```

**Least privilege.** Ilova o'zining system user'i (`appsvc`, shell'i `nologin`) bilan ishlaydi. `/srv/app` unga tegishli, lekin boshqalar uchun yopiq (750). Ilova faqat o'z papkasini o'qiy oladi, yozishi kerak bo'lgan joy bo'lsa — faqat o'sha alohida papka.

**Maxfiy sozlamalar.** Parol va tokenlar kodda emas, `.env` faylda, huquqi 600. Muhim nuance: `EnvironmentFile=` ni ilovaning o'zi emas, **systemd** o'qiydi va o'zgaruvchilarni ilova jarayoniga beradi. Tekshiruvda root'ga tegishli 600 `.env` dagi qiymat `appsvc` sifatida ishlayotgan jarayonga yetib bordi, lekin o'sha jarayon faylni `cat` qilmoqchi bo'lganda `Permission denied` oldi. Ya'ni ilova o'z sirlarini ko'radi, lekin fayl egasi bo'lishi shart emas.

**Virtual muhit.** Python bog'liqliklari tizim paketlariga aralashmasligi uchun ilova `venv` ichida ishlaydi. Ubuntu'da buning uchun `python3-venv` paketi kerak. Unit'dagi `ExecStart` aynan venv ichidagi interpretator yoki `uvicorn` ga to'liq yo'l bilan ko'rsatadi — `source activate` systemd'da kerak emas.

**Faqat localhost.** Ilova `127.0.0.1` da tinglaydi, `0.0.0.0` da emas. Tashqi dunyo bilan keyingi modulda nginx gaplashadi; hozircha port internetga ochiq bo'lmasligi kerak.

**Xavfsizlik cheklovlari.** systemd ilovaga qo'shimcha "devorlar" qo'ya oladi: `NoNewPrivileges=yes` (jarayon va bolalari yangi imtiyoz ololmaydi, masalan SUID orqali), `PrivateTmp=yes` (o'z alohida `/tmp`), `ProtectSystem=strict` (deyarli butun fayl tizimi faqat o'qish uchun) va `ReadWritePaths=` (yozishga ruxsat berilgan istisno papkalar). Ular mount namespace'larga tayanadi — men ularni oddiy Docker konteynerida tekshira olmadim (konteyner ichida ta'sir qilmadi), shuning uchun natijani o'zingiz VPS'da `systemd-analyze security app` bilan oldin va keyin solishtiring.

**README — loyihaning yarmi.** Yaxshi README'ni boshqa odam sizga savol bermasdan bajara oladi. Unda kamida to'rt narsa bo'lsin: talablar (OS versiyasi, paketlar), o'rnatish qadamlari tartib bilan (nusxalab ishlatsa bo'ladigan buyruqlar), tekshirish (qanday buyruq va qanday natija "hammasi joyida" degani) va muammo bo'lsa qayerga qarash (qaysi log, qaysi buyruq). Sirlar README'ga yozilmaydi — faqat `.env.example` dagi o'zgaruvchi nomlari.

## Buyruqlar

Natijalar Ubuntu 24.04 konteynerida olingan (systemd qismlari — systemd ishlaydigan konteynerda).

```bash
python3 -m venv /srv/app/venv
```
```text
The virtual environment was not created successfully because ensurepip is not
available.  On Debian/Ubuntu systems, you need to install the python3-venv
package using the following command.
```
Toza Ubuntu'da birinchi uchraydigan xato: avval `apt install python3-venv`.

```bash
/srv/app/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
```
```text
INFO:     Started server process [202]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```
Avval qo'lda ishga tushirib ko'ring — unit yozishdan oldin ilovaning o'zi ishlashiga ishonch hosil qiling. Keyin aynan shu buyruq (to'liq yo'l bilan) `ExecStart` ga ko'chadi.

```bash
curl -si localhost:8000/health
```
```text
HTTP/1.1 200 OK
...
{"status":"ok"}
```
Health endpoint — "ilova tirik va javob beryapti" degan eng oddiy tekshiruv. Monitoring, load balancer va deploy skriptlari aynan shunga murojaat qiladi.

```bash
sudo -u appsvc cat /srv/app/.env
```
```text
cat: /srv/app/.env: Permission denied
```
Ilova user'i faylni bevosita o'qiy olmaydi (fayl root'niki, 600) — lekin systemd orqali o'zgaruvchilarni oladi. Huquqlarni `namei -l /srv/app/.env` bilan ham ko'ring.

```bash
systemctl status app --no-pager
journalctl -u app -n 50 --no-pager
```
Holat va oxirgi 50 qator log. Ikkalasi README'dagi "tekshirish" bo'limiga kiradi.

```bash
sudo kill -9 $(systemctl show -p MainPID --value app); sleep 3; curl -s localhost:8000/health
sudo reboot     # qayta kirgach: curl -s localhost:8000/health
```
Ikki chidamlilik testi: majburan o'ldirilgandan keyin (`Restart=on-failure` qayta ko'taradi — 15-darsda ko'rgandek) va reboot'dan keyin (`enable` tufayli).

## Odatiy xatolar

- **Ilovani root bilan ishga tushirish.** Belgi: unit'da `User=` yo'q, `ps` da ilova `root`. Sabab: tezroq ishlatish uchun "hozircha". To'g'ri usul: `appsvc` system user va `User=appsvc`; huquq muammosi chiqsa, user'ni emas, papka huquqlarini tuzating.
- **`.env` ni Git'ga qo'shish yoki 644 qoldirish.** Belgi: repo'da parol, yoki istalgan user o'qiy oladi. Sabab: `.gitignore` va huquqlar unutilgan. To'g'ri usul: `.env` faqat serverda, 600; repo'da faqat `.env.example`.
- **`ExecStart` da nisbiy yo'l yoki tizim Python'i.** Belgi: qo'lda ishlaydi, servis sifatida `ModuleNotFoundError`. Sabab: venv emas, tizim interpretatori ishga tushdi. To'g'ri usul: `/srv/app/venv/bin/...` to'liq yo'l va `WorkingDirectory=/srv/app`.
- **`0.0.0.0` da tinglash.** Belgi: port internetdan ochiq, firewall'siz har kim ulanadi. Sabab: misollardan ko'chirilgan. To'g'ri usul: `127.0.0.1`, tashqi kirish — faqat reverse proxy orqali.
- **Faqat "hozir ishlayapti" bilan to'xtash.** Belgi: reboot'dan keyin servis yo'q yoki README bo'yicha qayta o'rnatib bo'lmaydi. Sabab: chidamlilik va qayta takrorlanish tekshirilmagan. To'g'ri usul: kill va reboot testlari, README'ni toza serverda boshidan oxirigacha sinab ko'rish.

## Intervyuda

**Savol:** Docker'siz Linux serverga Python veb-ilovani qanday deploy qilasiz va uni ishonchli qilish uchun nimalarga e'tibor berasiz?

**Namunaviy javob:** Ilova uchun alohida system user va `/srv/app` papkasini yarataman, bog'liqliklarni venv ichiga o'rnataman va sirlarni 600 huquqli `.env` faylda saqlayman. Ishga tushirishni systemd unit'ga topshiraman: `User=`, `WorkingDirectory=`, `EnvironmentFile=`, venv'dagi interpretatorga to'liq yo'l, `Restart=on-failure` va xavfsizlik cheklovlari bilan, keyin `enable --now`. Ilova faqat localhost'da tinglaydi, tashqariga nginx orqali chiqadi; loglar journald'da. Oxirida health endpoint bilan, servisni majburan o'ldirib va serverni reboot qilib tekshiraman va hammasini README'da hujjatlashtiraman.
