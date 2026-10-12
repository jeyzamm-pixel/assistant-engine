import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build  # noqa: E402
import guards  # noqa: E402

SLUG = "piekarnia-przykladowa"
KLIENT = build.wczytaj_klienta(SLUG)
PROMPTY = {k: build.zloz(SLUG, k) for k in ("czat", "glos")}


@pytest.mark.parametrize("kanal", ["czat", "glos"])
def test_prompt_zawiera_fakty_pewne(kanal):
    for wartosc in KLIENT["fakty_pewne"].values():
        assert wartosc in PROMPTY[kanal]


@pytest.mark.parametrize("kanal", ["czat", "glos"])
def test_faktow_niepewnych_nie_ma_w_prompcie(kanal):
    for pytanie in KLIENT["fakty_niepewne"]:
        assert pytanie not in PROMPTY[kanal]
    assert "bezglutenowe" not in PROMPTY[kanal]


@pytest.mark.parametrize("kanal", ["czat", "glos"])
def test_prompt_bez_kwot_i_myslnikow(kanal):
    assert build.lint(PROMPTY[kanal]) == []


def test_lint_lapie_zakazane_rzeczy():
    assert build.lint("tort \N{EM DASH} pyszny")
    assert build.lint("Zbudowała nas NazwaAgencji")
    assert build.lint("Tort kosztuje 120 zł")
    assert build.lint("Zbudowała nas NazwaAgencji", dozwolone=("NazwaAgencji",)) == []


def test_zloz_odrzuca_prompt_z_kwota(tmp_path, monkeypatch):
    zle = dict(KLIENT, fakty_pewne={"cena": "Tort kosztuje 150 zł"})
    monkeypatch.setattr(build, "wczytaj_klienta", lambda slug: zle)
    with pytest.raises(ValueError):
        build.zloz(SLUG, "czat")


def test_fraza_konczaca_jest_w_warstwie_glosu_i_w_konfiguracji_platformy():
    fraza = KLIENT["fraza_konczaca"]
    assert fraza in PROMPTY["glos"]
    assert fraza not in PROMPTY["czat"]
    cfg = json.loads((ROOT / "ustawienia_platformy" / "glos.json").read_text(encoding="utf-8"))
    assert cfg["endCallPhrases"] == [fraza]          # znak w znak, z polskimi znakami


def test_fraza_konczaca_nie_ma_wersji_bez_ogonkow():
    ascii_fraza = "do uslyszenia"
    assert ascii_fraza not in PROMPTY["glos"].lower()


@pytest.mark.parametrize("proba", [
    "Tort na dwadzieścia osób kosztuje 280 zł.",
    "To będzie około 300 PLN.",
    "Sto dwadzieścia złotych za blachę.",
    "Cena: 12,50 zł za sztukę.",
])
def test_straznik_zastepuje_odpowiedz_z_kwota(proba):
    tekst, naruszenia = guards.przechwyc(proba)
    assert naruszenia == ["kwota"]
    assert tekst == guards.ODPOWIEDZ_ZASTEPCZA
    assert not build.KWOTA.search(tekst)


def test_straznik_wycina_myslnik_z_odpowiedzi():
    tekst, naruszenia = guards.przechwyc("Piekarnia \N{EM DASH} otwarta od szóstej.")
    assert "\N{EM DASH}" not in tekst and naruszenia == ["znak: myślnik em"]


def test_straznik_przepuszcza_zwykla_odpowiedz():
    ok = "Jesteśmy czynni od poniedziałku do piątku od szóstej do osiemnastej."
    assert guards.przechwyc(ok) == (ok, [])
