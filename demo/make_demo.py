"""Demo: rozmowa z asystentem firmy fikcyjnej na symulowanym modelu, z przechwytem kodu.

Symulowany model celowo próbuje złamać regułę (podaje cenę), żeby było widać, że pilnuje kod,
a nie prośba w prompcie. Uruchom: python demo/make_demo.py   (zrzuty: playwright install chromium)
"""
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build  # noqa: E402
import guards  # noqa: E402

SLUG = "piekarnia-przykladowa"


def symulowany_model(prompt: str, pytanie: str) -> str:
    """Zastępuje model językowy. Odpowiada tylko z faktów w prompcie albo odsyła do człowieka."""
    q = pytanie.lower()
    if "człowiek" in q or "bot" in q:
        return "Jestem asystentem AI Piekarni Przykładowej. Mogę odpowiedzieć na pytania i zostawić wiadomość dla pracowników."
    if "godzin" in q or "otwar" in q:
        return "Jesteśmy czynni od poniedziałku do piątku od 6:00 do 18:00, w sobotę od 6:00 do 14:00. W niedzielę zamknięte."
    if "ile kosztuje" in q or "cena" in q:
        return "Tort na dwadzieścia osób kosztuje około 280 zł."   # złamanie reguły, ma zostać przechwycone
    if "bezglutenow" in q:
        return "Tego nie jestem pewien, sprawdzi to pracownik. Zostawisz numer telefonu?"
    if "tort" in q:
        return "Torty przyjmujemy z trzydniowym wyprzedzeniem. Zamówienie składa się osobiście lub przez formularz."
    return "Nie mam tej informacji. Zostaw numer, a firma oddzwoni."


ROZMOWA = [
    "Dzień dobry, do której jesteście otwarci?",
    "Czy rozmawiam z człowiekiem?",
    "A ile kosztuje tort na 20 osób?",
    "Macie torty bezglutenowe?",
]


def dymki():
    prompt = build.zloz(SLUG, "czat")
    wynik = []
    for pytanie in ROZMOWA:
        surowa = symulowany_model(prompt, pytanie)
        tekst, naruszenia = guards.przechwyc(surowa)
        wynik.append(("k", pytanie, None))
        wynik.append(("a", tekst, naruszenia))
    return wynik


def czat_html():
    b = []
    for kto, tekst, nar in dymki():
        znacznik = ""
        if nar:
            znacznik = ("<div class='gd'>Przechwycone przez kod: model podał kwotę, "
                        "klient dostał odpowiedź zastępczą</div>")
        b.append(f"<div class='m {kto}'>{html.escape(tekst)}{znacznik}</div>")
    return f"""<!doctype html><html lang="pl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Czat demo</title>
<style>
:root{{--n:#0A95C9;--o:#FC6E08;--g:#021836}}
body{{margin:0;background:#e8eef4;font:15px/1.45 system-ui,Segoe UI,sans-serif;color:var(--g)}}
.ph{{max-width:412px;margin:0 auto;min-height:100vh;background:#f5f8fb;display:flex;flex-direction:column}}
header{{background:var(--g);color:#fff;padding:14px 16px}}header b{{display:block}}header small{{opacity:.75}}
.l{{flex:1;padding:14px;display:flex;flex-direction:column;gap:10px}}
.m{{max-width:84%;padding:9px 12px;border-radius:14px}}
.m.k{{align-self:flex-end;background:var(--n);color:#fff;border-bottom-right-radius:4px}}
.m.a{{align-self:flex-start;background:#fff;border:1px solid #dbe4ec;border-bottom-left-radius:4px}}
.gd{{margin-top:6px;font-size:12px;color:#9a3d00;background:#fff4ec;border-radius:8px;padding:4px 8px}}
footer{{padding:10px 14px;color:#58708a;font-size:12px;border-top:1px solid #dbe4ec}}
</style></head><body><div class="ph">
<header><b>Piekarnia Przykładowa</b><small>Asystent AI</small></header>
<div class="l">{''.join(b)}</div>
<footer>Symulowany model do demonstracji. Reguła "zero kwot" jest egzekwowana kodem.</footer>
</div></body></html>"""


if __name__ == "__main__":
    out = ROOT / "demo" / "czat.html"
    out.write_text(czat_html(), encoding="utf-8")
    build.main()
    print("zapisano", out.relative_to(ROOT))
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            br = p.chromium.launch()
            (ROOT / "screenshots").mkdir(exist_ok=True)
            pg = br.new_page(viewport={"width": 412, "height": 800})
            pg.goto(out.as_uri())
            pg.screenshot(path=str(ROOT / "screenshots" / "czat.png"), full_page=True)
            pg = br.new_page(viewport={"width": 900, "height": 700})
            pg.goto((ROOT / "dist" / f"{SLUG}-karta-faktow.html").as_uri())
            pg.screenshot(path=str(ROOT / "screenshots" / "karta-faktow.png"), full_page=True)
            br.close()
        print("zrzuty ok")
    except ImportError:
        print("brak playwright: pominięto zrzuty")
