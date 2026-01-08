import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# --- 1. KONFIGURACJA DANYCH (SYMULACJA) ---
# W rzeczywistości te dane pobrałbyś z Excela lub SQL
data = {
    "Kategoria": [
        "Zaległe",
        "Zaległe",
        "Dziś",
        "Dziś",
        "Jutro",
        "Jutro",
        "Reszta Tygodnia",
        "Reszta Tygodnia",
        "Przyszłość",
        "Przyszłość",
    ],
    "Status_Materialowy": [
        "OK",
        "BRAK",
        "OK",
        "BRAK",
        "OK",
        "BRAK",
        "OK",
        "BRAK",
        "OK",
        "BRAK",
    ],
    # Ilość sztuk zamówień w danej kategorii
    "Ilosc_Sztuk": [
        800,
        200,  # Zaległe (Dużo zaległości!)
        1200,
        150,  # Dziś (Spiętrzenie - więcej niż limit)
        900,
        300,  # Jutro (Na styk)
        2500,
        800,  # Reszta tyg. (Duża górka)
        1500,
        1000,  # Przyszłość
    ],
}

# Definiujemy Limit Produkcyjny (Twoja "czerwona linia")
DZIENNY_LIMIT_PRODUKCJI = 1000
# Dla "Reszta Tygodnia" limit jest np. 3x większy (śr-pt), a dla "Przyszłość" umowny
LIMITY_PER_KATEGORIA = {
    "Zaległe": DZIENNY_LIMIT_PRODUKCJI,
    "Dziś": DZIENNY_LIMIT_PRODUKCJI,
    "Jutro": DZIENNY_LIMIT_PRODUKCJI,
    "Reszta Tygodnia": DZIENNY_LIMIT_PRODUKCJI * 3,
    "Przyszłość": DZIENNY_LIMIT_PRODUKCJI * 5,
}

df = pd.DataFrame(data)

# --- 2. PRZETWARZANIE DANYCH (LOGIKA NADLEWKI) ---

# Kolejność kategorii na osi X
kolejnosc = ["Zaległe", "Dziś", "Jutro", "Reszta Tygodnia", "Przyszłość"]

# Przygotowanie list do wykresu
ok_below_limit = []  # Niebieskie (Wchodzą w plan)
ok_above_limit = []  # Czerwone (Nadgodziny/Przesunięcie)
blocked = []  # Szare (Brak materiału)
limits = []  # Do narysowania linii limitu dla każdego słupka

for kat in kolejnosc:
    # Pobierz dane dla kategorii
    subset = df[df["Kategoria"] == kat]

    # 1. Oblicz ile mamy zablokowanych (Brak materiału)
    blocked_qty = subset[subset["Status_Materialowy"] == "BRAK"]["Ilosc_Sztuk"].sum()

    # 2. Oblicz ile mamy gotowych do produkcji (OK)
    ok_qty = subset[subset["Status_Materialowy"] == "OK"]["Ilosc_Sztuk"].sum()

    # 3. Pobierz limit dla tej kategorii
    limit = LIMITY_PER_KATEGORIA.get(kat, 1000)
    limits.append(limit)

    # 4. Logika podziału "Wody": Co się mieści, a co wylewa?
    if ok_qty <= limit:
        # Wszystko się mieści
        ok_below_limit.append(ok_qty)
        ok_above_limit.append(0)
    else:
        # Przepełnienie
        ok_below_limit.append(limit)  # Wypełniamy do pełna
        ok_above_limit.append(ok_qty - limit)  # Reszta to "nadlewka"

    blocked.append(blocked_qty)

# --- 3. RYSOWANIE WYKRESU (MATPLOTLIB) ---

fig, ax = plt.subplots(figsize=(12, 7))

# Ustawienie szerokości słupków
bar_width = 0.6
x_pos = np.arange(len(kolejnosc))

# Rysowanie warstw (Stacked Bar Chart)
# Warstwa 1: Produkcja w limicie (Niebieski)
p1 = ax.bar(
    x_pos,
    ok_below_limit,
    bar_width,
    label="Wykonalne (W limicie)",
    color="#2ecc71",
    edgecolor="white",
)

# Warstwa 2: Nadwyżka (Czerwony) - zaczyna się tam, gdzie kończy Warstwa 1
p2 = ax.bar(
    x_pos,
    ok_above_limit,
    bar_width,
    bottom=ok_below_limit,
    label="Spiętrzenie (Ponad limit)",
    color="#e74c3c",
    hatch="//",
    edgecolor="white",
)

# Warstwa 3: Zablokowane (Szary) - zaczyna się na szczycie OK (Suma W1 + W2)
# Sumujemy listy element po elemencie, żeby wiedzieć gdzie zacząć rysować szare
bottom_for_grey = [i + j for i, j in zip(ok_below_limit, ok_above_limit)]
p3 = ax.bar(
    x_pos,
    blocked,
    bar_width,
    bottom=bottom_for_grey,
    label="Zablokowane (Brak surowca)",
    color="#95a5a6",
    alpha=0.6,
    edgecolor="white",
)

# --- 4. DODATKI WIZUALNE I LINIE LIMITU ---

# Rysowanie linii limitów (Step plot - schodki, bo limit się zmienia dla tyg/msc)
ax.step(
    x_pos,
    limits,
    where="mid",
    color="#2c3e50",
    linestyle="--",
    linewidth=2,
    label="Możliwości Produkcyjne",
)
# Opcjonalnie: Czerwona linia ciągła dla dziennego limitu
ax.axhline(
    y=DZIENNY_LIMIT_PRODUKCJI,
    color="red",
    linestyle=":",
    alpha=0.5,
    label="Nominalny Limit Dzienny",
)

# Etykiety i Tytuły
ax.set_ylabel("Ilość Zamówień (Sztuki)", fontsize=12)
ax.set_title(
    "Wirtualna Tablica Planistyczna: Obciążenie vs Możliwości",
    fontsize=16,
    fontweight="bold",
)
ax.set_xticks(x_pos)
ax.set_xticklabels(kolejnosc, fontsize=11)
ax.legend(loc="upper left")


# Dodanie etykiet z wartościami na słupkach
def add_labels(rects):
    for rect in rects:
        height = rect.get_height()
        if height > 0:  # Pisz tylko jeśli słupek istnieje
            ax.annotate(
                f"{int(height)}",
                xy=(rect.get_x() + rect.get_width() / 2, rect.get_y() + height / 2),
                xytext=(0, 0),
                textcoords="offset points",
                ha="center",
                va="center",
                color="white",
                fontweight="bold",
                fontsize=9,
            )


add_labels(p1)
add_labels(p2)
add_labels(p3)

# Dodatkowe sformatowanie
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="y", linestyle="--", alpha=0.3)

plt.tight_layout()
plt.show()

""" 
Jak czytać ten wykres (i co on mówi Twojemu szefowi):
Kolumna "Zaległe": Jeśli widzisz tam czerwone prążki, oznacza to katastrofę – nie wyrobiliśmy się wczoraj i nawet gdybyśmy dziś rzucili wszystkie siły, to i tak jest tego za dużo na jeden dzień.

Kolumna "Dziś":

Zielone: To zrobimy.

Czerwone (hatch //): To jest Twoje "Spiętrzenie". Tę część musisz natychmiast przesunąć na "Jutro".

Kolumna "Jutro": Jeśli po przesunięciu z "Dziś", słupek "Jutro" też zrobi się czerwony – masz efekt domina.

Szary kolor: To jest Twój potencjał, który marnujesz. Pokazujesz zarządowi: "Moglibyśmy produkować więcej (szare pola), ale dział zakupów nie dostarczył surowca".

Wskazówki techniczne do skryptu:
Zmienna LIMITY_PER_KATEGORIA jest kluczowa. Dla kolumny "Reszta Tygodnia" limit musi być sumą limitów z pozostałych dni (np. Środa+Czwartek+Piątek), inaczej słupek zawsze będzie czerwony.

Dane wejściowe (data) są słownikiem list, co łatwo zamienić na DataFrame. Możesz podmienić ten fragment na pd.read_excel('zamowienia.xlsx').

"""
