"""Skład asystenta: rdzeń + wiedza klienta + warstwa kanału, potem lint.

Użycie:
    python build.py piekarnia-przykladowa            # zapisuje dist/<firma>-czat.md i -glos.md, karta faktów
"""
import html
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent

MYSLNIKI = {"\N{EM DASH}": "myślnik em", "\N{EN DASH}": "półpauza"}

# Nazwy własne agencji nie mają prawa wystąpić w asystencie klienta:
# klient płaci za swojego asystenta, a nie za naszą wizytówkę.
NAZWY_WEWNETRZNE = ("NazwaAgencji", "AsystentAgencji")

KWOTA = re.compile(r"\d[\d\s.,]*\s?(zł|zl|pln|PLN|złotych|euro|eur|EUR|\$)", re.I)


def lint(text, dozwolone=()):
    problemy = []
    for znak, opis in MYSLNIKI.items():
        if znak in text:
            problemy.append(f"zakazany znak: {opis}")
    for nazwa in NAZWY_WEWNETRZNE:
        if nazwa in text and nazwa not in dozwolone:
            problemy.append(f"nazwa wewnętrzna: {nazwa}")
    if KWOTA.search(text):
        problemy.append("kwota w prompcie")
    return problemy


def wczytaj_klienta(slug):
    with open(ROOT / "clients" / slug / "wiedza.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fakty_tekst(klient):
    """Do promptu trafiają wyłącznie fakty pewne. Niepewnych nie ma tu wcale."""
    return "\n".join(f"- {k.replace('_', ' ')}: {v}" for k, v in klient["fakty_pewne"].items())


def zloz(slug, kanal):
    klient = wczytaj_klienta(slug)
    rdzen = (ROOT / "core" / "rdzen.md").read_text(encoding="utf-8")
    warstwa = (ROOT / "core" / f"kanal_{kanal}.md").read_text(encoding="utf-8")
    tekst = rdzen.format(firma=klient["firma"], fakty=fakty_tekst(klient)) + "\n" \
        + warstwa.format(fraza_konczaca=klient["fraza_konczaca"])
    problemy = lint(tekst)
    if problemy:
        raise ValueError(f"lint odrzucił prompt {slug}/{kanal}: {problemy}")
    return tekst


def karta_faktow_html(klient):
    wiersze = "".join(f"<tr><td>{html.escape(k.replace('_', ' '))}</td><td>{html.escape(v)}</td>"
                      f"<td class='p'>&nbsp;</td></tr>" for k, v in klient["fakty_pewne"].items())
    pytania = "".join(f"<li>{html.escape(x)}<span></span></li>" for x in klient["fakty_niepewne"])
    return f"""<!doctype html><html lang="pl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Karta faktów</title>
<style>
:root{{--n:#0A95C9;--o:#FC6E08;--g:#021836}}
body{{margin:0;background:#f5f8fb;color:var(--g);font:15px/1.5 system-ui,Segoe UI,sans-serif}}
main{{max-width:820px;margin:0 auto;padding:28px 20px 40px}}h1{{font-size:26px;margin:0}}
.s{{color:#476;margin:2px 0 20px}}h2{{font-size:16px;margin:24px 0 8px}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #dbe4ec}}
th,td{{padding:9px 12px;border-bottom:1px solid #dbe4ec;text-align:left;vertical-align:top}}
th{{background:#eaf3f9;font-size:13px}}td:first-child{{width:28%;font-weight:600;text-transform:capitalize}}
td.p{{width:28%;background:repeating-linear-gradient(#fff,#fff 22px,#e3ebf2 23px)}}
ul{{background:#fff4ec;border:1px solid #f9c9a3;border-radius:10px;padding:10px 12px 10px 34px}}
li span{{display:block;border-bottom:1px dotted #c9a583;height:22px}}
</style></head><body><main>
<h1>Karta faktów: {html.escape(klient['firma'])}</h1>
<p class="s">Asystent powie tylko to, co tu jest. Popraw błędy w prawej kolumnie i odeślij kartę.</p>
<h2>Fakty, które asystent zna</h2>
<table><tr><th>Temat</th><th>Co mówi asystent</th><th>Poprawka</th></tr>{wiersze}</table>
<h2>Pytania bez pewnej odpowiedzi (asystent odeśle do człowieka)</h2>
<p>Dopisz odpowiedź, jeśli chcesz, żeby asystent ją znał.</p><ul>{pytania}</ul>
</main></body></html>"""


def main():
    slug = sys.argv[1] if len(sys.argv) > 1 else "piekarnia-przykladowa"
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    for kanal in ("czat", "glos"):
        (out / f"{slug}-{kanal}.md").write_text(zloz(slug, kanal), encoding="utf-8")
        print("zapisano", f"dist/{slug}-{kanal}.md")
    (out / f"{slug}-karta-faktow.html").write_text(karta_faktow_html(wczytaj_klienta(slug)), encoding="utf-8")
    print("zapisano", f"dist/{slug}-karta-faktow.html")


if __name__ == "__main__":
    main()
