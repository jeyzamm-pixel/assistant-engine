"""Warstwa kodu: przechwytuje odpowiedź modelu przed wysłaniem do klienta.

W produkcji to węzeł automatyzacji między modelem a kanałem. Tu to zwykła funkcja,
żeby dało się ją przetestować i pokazać.
"""
import re

from build import KWOTA, MYSLNIKI

ODPOWIEDZ_ZASTEPCZA = ("Wycenę przygotowuje pracownik po rozmowie. "
                       "Zostaw numer telefonu, a firma oddzwoni.")

# Słowa, po których poznajemy próbę podania ceny bez cyfr ("sto dwadzieścia złotych").
SLOWNE_KWOTY = re.compile(r"\b(złotych|złote|złotego|groszy)\b", re.I)


def przechwyc(odpowiedz: str) -> tuple[str, list]:
    """Zwraca (tekst do wysłania, lista naruszeń). Kwota zastępuje całą odpowiedź."""
    naruszenia = []
    tekst = odpowiedz
    if KWOTA.search(tekst) or SLOWNE_KWOTY.search(tekst):
        naruszenia.append("kwota")
        tekst = ODPOWIEDZ_ZASTEPCZA
    for znak, opis in MYSLNIKI.items():
        if znak in tekst:
            naruszenia.append(f"znak: {opis}")
            tekst = tekst.replace(znak, ",")
    return tekst, naruszenia
