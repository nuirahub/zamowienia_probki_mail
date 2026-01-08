import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# --- 1. KONFIGURACJA DANYCH I PARAMETRÓW ---

# Symulacja: Ile nowych zamówień spływa każdego dnia na dany termin
raw_data = {
    "Dzien": [
        "Poniedziałek",
        "Wtorek",
        "Środa",
        "Czwartek",
        "Piątek",
        "Sobota",
        "Niedziela",
    ],
    "Nowe_Zamowienia": [1100, 1200, 800, 900, 600, 200, 0],
}

# Twoja "Moc Przerobowa" (Capacity)
DZIENNY_LIMIT = 1000

df = pd.DataFrame(raw_data)

# --- 2. SYMULACJA "EFKETU KULI ŚNIEŻNEJ" (Obliczenia) ---

# Listy do przechowywania wyników symulacji
zaleglosci_z_wczoraj = []  # To, co musimy zrobić najpierw (Backlog)
planowane_nowe = []  # To, co przyszło na ten dzień
calkowite_obciazenie = []  # Suma
aktualny_backlog = 200  # Startujemy tydzień z "plecakiem" np. 200 sztuk z zeszłego tyg.

for nowe in df["Nowe_Zamowienia"]:
    # 1. Rejestrujemy ile zaległości weszło na ten dzień
    zaleglosci_z_wczoraj.append(aktualny_backlog)

    # 2. Rejestrujemy nowe zamówienia
    planowane_nowe.append(nowe)

    # 3. Sumujemy obciążenie
    total = aktualny_backlog + nowe
    calkowite_obciazenie.append(total)

    # 4. Obliczamy, co przechodzi na jutro
    # Jeśli total > limit, to nadwyżka przechodzi. Jeśli nie, backlog = 0.
    if total > DZIENNY_LIMIT:
        aktualny_backlog = total - DZIENNY_LIMIT
    else:
        aktualny_backlog = 0

# Dodajemy wyniki do DataFrame, żeby łatwiej rysować
df["Zalegle"] = zaleglosci_z_wczoraj
df["Nowe"] = planowane_nowe
df["Total"] = calkowite_obciazenie

# --- 3. RYSOWANIE WYKRESU (LOAD BALANCING) ---

fig, ax = plt.subplots(figsize=(12, 6))

x_pos = np.arange(len(df["Dzien"]))
bar_width = 0.6

# Rysowanie słupków skumulowanych (Stacked Bars)
# Najpierw rysujemy ZALEGŁOŚCI (na dole), bo one mają priorytet wykonania
p1 = ax.bar(
    x_pos,
    df["Zalegle"],
    bar_width,
    label="Zaległości (Przesunięte z wczoraj)",
    color="#e67e22",
    edgecolor="white",
    hatch="//",
)

# Na górze rysujemy NOWE ZAMÓWIENIA
p2 = ax.bar(
    x_pos,
    df["Nowe"],
    bar_width,
    bottom=df["Zalegle"],  # Zaczynamy tam, gdzie kończą się zaległości
    label="Nowe Zamówienia (Plan na dziś)",
    color="#3498db",
    edgecolor="white",
)

# --- 4. LINIA ODCINKA (CAPACITY LINE) ---

# Rysujemy czerwoną linię limitu
line = ax.axhline(
    y=DZIENNY_LIMIT,
    color="#c0392b",
    linewidth=2.5,
    linestyle="--",
    label="Maksymalna Wydajność (Limit)",
)

# Dodatkowy efekt: Wypełnienie tła powyżej limitu (strefa zagrożenia)
ax.axhspan(DZIENNY_LIMIT, df["Total"].max() * 1.1, color="#e74c3c", alpha=0.05)
ax.text(
    len(df) - 0.5,
    DZIENNY_LIMIT + 50,
    "STREFA NADGODZIN",
    color="#c0392b",
    fontstyle="italic",
    va="bottom",
    ha="right",
)

# --- 5. FORMATOWANIE I ETYKIETY ---

ax.set_title(
    'Histogram Obciążenia Tygodniowego: Efekt "Kuli Śnieżnej"',
    fontsize=16,
    fontweight="bold",
    pad=20,
)
ax.set_ylabel("Liczba sztuk do wykonania", fontsize=12)
ax.set_xticks(x_pos)
ax.set_xticklabels(df["Dzien"], fontsize=11)
ax.legend(loc="upper right", frameon=True, shadow=True)

# Usunięcie zbędnych ramek
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="y", linestyle=":", alpha=0.4)


# Adnotacje wartości (opcjonalnie, żeby nie zaciemniać)
def add_total_labels():
    for i, total in enumerate(df["Total"]):
        color = "#c0392b" if total > DZIENNY_LIMIT else "black"
        weight = "bold" if total > DZIENNY_LIMIT else "normal"
        ax.text(i, total + 20, f"{total}", ha="center", color=color, fontweight=weight)


add_total_labels()

plt.tight_layout()
plt.show()

"""
Co ten wykres pokazuje (Interpretacja dla Biznesu):
Pomarańczowa Podstawa (Zaległości): Zwróć uwagę na Wtorek. Mimo że nowych zamówień jest 1200 (niebieskie), to słupek jest wyższy, bo "niesie" na plecach pomarańczowy bagaż z Poniedziałku.

Strefa Nadgodzin: Wszystko co wystaje powyżej czerwonej przerywanej linii, fizycznie nie zostanie zrobione w danym dniu bez nadgodzin.

Decyzja Planistyczna:

Widzisz, że Poniedziałek i Wtorek drastycznie przekraczają linię.

Widzisz, że w Piątek i Sobotę słupek jest poniżej linii.

Wniosek: Należy "wypłaszczyć" (leveling) produkcję – czyli przesunąć część niebieskich klocków z poniedziałku/wtorku na czwartek/piątek, aby słupki wyrównały się do czerwonej linii.

Ten skrypt to gotowe narzędzie do symulacji – wystarczy, że podmienisz dane w zmiennej raw_data na te zaciągnięte z Twojego systemu ERP.
"""
