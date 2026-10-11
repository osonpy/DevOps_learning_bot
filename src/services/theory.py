"""'Batafsil nazariya': Markdown (cheklangan to'plam) -> Telegram HTML, ## bo'yicha xabarlarga bo'laklash.

Qo'llanadi: # / ## / ### sarlavhalar, **qalin**, `inline kod`, ```lang kod bloklari```, "- " / "* " ro'yxatlar.
Qolgan hamma narsa HTML-escape qilingan oddiy matn.
"""
import html
import re
from dataclasses import dataclass, field

CHUNK_LIMIT = 3500  # Telegram limiti 4096; HTML teglari va zaxira uchun joy qoldiramiz

_FENCE = re.compile(r"^```\s*([\w+-]*)\s*$")
_HEADING = re.compile(r"^(#{1,3})\s+(.*)$")
_BULLET = re.compile(r"^(\s*)[-*]\s+(.*)$")
_INLINE_CODE = re.compile(r"(`[^`\n]+`)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")


def _esc(text: str) -> str:
    return html.escape(text, quote=False)


def _inline(text: str) -> str:
    # Kod bo'laklari vaqtincha \x00N\x00 bilan almashtiriladi: **qalin** ichida `kod` bo'lishi mumkin,
    # kod ichidagi ** esa qalin bo'lmasligi kerak.
    codes: list[str] = []

    def stash(m: re.Match) -> str:
        codes.append(f"<code>{_esc(m[1][1:-1])}</code>")
        return f"\x00{len(codes) - 1}\x00"

    text = _BOLD.sub(r"<b>\1</b>", _esc(_INLINE_CODE.sub(stash, text)))
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m[1])], text)


def _line(line: str) -> str:
    m = _BULLET.match(line)
    if m:
        return f"{m[1]}• {_inline(m[2])}"
    return _inline(line)


@dataclass
class _Section:
    heading: str | None = None
    blocks: list[str] = field(default_factory=list)

    def html(self) -> str:
        body = "\n\n".join(self.blocks)
        if self.heading is None:
            return body
        return f"{self.heading}\n{body}" if body else self.heading


def _sections(md: str) -> list[_Section]:
    """Markdown'ni bo'limlarga (# / ## bo'yicha) va bo'lim ichida bloklarga ajratadi."""
    sections, buf = [_Section()], []
    lines = md.splitlines()

    def flush():
        if buf:
            sections[-1].blocks.append("\n".join(buf))
            buf.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        fence = _FENCE.match(line)
        if fence:
            flush()
            code, i = [], i + 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            lang = f' class="language-{fence[1]}"' if fence[1] else ""
            sections[-1].blocks.append(f"<pre><code{lang}>{_esc(chr(10).join(code))}</code></pre>")
        elif not line.strip():
            flush()
        elif heading := _HEADING.match(line):
            flush()
            title = f"<b>{_inline(heading[2].strip())}</b>"
            if len(heading[1]) <= 2:
                sections.append(_Section(heading=title))
            else:
                sections[-1].blocks.append(title)
        else:
            buf.append(_line(line))
        i += 1
    flush()
    return [s for s in sections if s.heading or s.blocks]


def md_to_html(md: str) -> str:
    return "\n\n".join(s.html() for s in _sections(md))


def theory_messages(md: str, header: str | None = None, limit: int = CHUNK_LIMIT) -> list[str]:
    """Bo'limlarni (##) xabarlarga joylaydi: har xabar <= limit, kod bloki hech qachon bo'linmaydi.

    Bo'lim sig'masa — bloklar (paragraf / ro'yxat / kod bloki) bo'yicha bo'linadi.
    Bitta blok limitdan katta bo'lsa — ValueError (kontentni qisqartirish kerak).
    """
    messages: list[str] = []
    cur = header or ""

    def add(piece: str) -> None:
        nonlocal cur
        if len(piece) > limit:
            raise ValueError(f"blok {len(piece)} belgi > {limit}: {piece[:60]!r}…")
        if not cur:
            cur = piece
        elif len(cur) + 2 + len(piece) <= limit:
            cur += "\n\n" + piece
        else:
            messages.append(cur)
            cur = piece

    for section in _sections(md):
        text = section.html()
        fits_current = len(cur) + 2 + len(text) <= limit
        if fits_current or (len(text) <= limit and cur != (header or "")):
            add(text)
            continue
        # bo'lim sig'madi: sarlavhani birinchi blokka yopishtirib, bloklar bo'yicha joylaymiz
        pieces = list(section.blocks)
        if section.heading:
            if pieces and len(section.heading) + 1 + len(pieces[0]) <= limit:
                pieces[0] = f"{section.heading}\n{pieces[0]}"
            else:
                pieces.insert(0, section.heading)
        for piece in pieces:
            add(piece)
    if cur:
        messages.append(cur)
    return messages
