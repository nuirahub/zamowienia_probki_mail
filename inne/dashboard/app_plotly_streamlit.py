from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Dashboard Produkcyjny", layout="wide")


# --- 1. GENEROWANIE DANYCH (MOCKUP) ---
@st.cache_data
def get_data():
    # Generujemy przykładowe dane na najbliższe 14 dni
    today = datetime.now().date()
    data = []

    # Symulacja zamówień
    for i in range(14):
        date = today + timedelta(days=i)
        # Losowa ilość zamówień na dzień
        num_orders = np.random.randint(5, 15)

        for _ in range(num_orders):
            qty = np.random.randint(50, 200)
            # Losujemy czy brakuje surowca (20% szans na brak)
            material_status = np.random.choice(["OK", "BRAK"], p=[0.8, 0.2])

            data.append(
                {
                    "Data": date,
                    "Zamówienie": f"ZAM-{np.random.randint(1000, 9999)}",
                    "Ilość": qty,
                    "Status_Materialowy": material_status,
                    "Klient": f"Klient {np.random.choice(['A', 'B', 'C'])}",
                }
            )

    return pd.DataFrame(data)


df = get_data()

# --- 2. PASEK BOCZNY (INTERAKCJA) ---
st.sidebar.header("⚙️ Ustawienia Operacyjne")
st.sidebar.write("Symuluj zmiany wydajności:")

# Suwak do zmiany wydajności - to sprawia, że dashboard jest DYNAMICZNY
capacity_limit = st.sidebar.slider(
    "Dzienny Limit Produkcji (szt.)",
    min_value=500,
    max_value=3000,
    value=1500,
    step=100,
)

st.sidebar.markdown("---")
st.sidebar.info(
    f"""
    **Aktualny scenariusz:**
    Przy wydajności **{capacity_limit}** szt./dzień,
    sprawdzamy czy powstaną zatory.
    """
)

# --- 3. PRZETWARZANIE DANYCH (LOGIKA BIZNESOWA) ---

# Agregacja danych do widoku dziennego
daily_load = (
    df.groupby(["Data", "Status_Materialowy"])["Ilość"]
    .sum()
    .unstack(fill_value=0)
    .reset_index()
)
if "BRAK" not in daily_load.columns:
    daily_load["BRAK"] = 0
daily_load["Total_Order"] = daily_load.get("OK", 0) + daily_load.get("BRAK", 0)

# --- LOGIKA SYMULACJI (KULA ŚNIEŻNA) ---
# Obliczamy jak zamówienia się przesuwają przy zadanym limicie
backlog_history = []
current_backlog = 0  # Startujemy z zerem lub wartością z wczoraj

simulation_data = []

for index, row in daily_load.iterrows():
    incoming = row["Total_Order"]
    # Ile mamy do zrobienia łącznie (to co przyszło + to co zalega)
    total_load = incoming + current_backlog

    # Ile realnie zrobimy (nie więcej niż limit)
    produced = min(total_load, capacity_limit)

    # Ile zostaje na jutro
    remaining = total_load - produced

    simulation_data.append(
        {
            "Data": row["Data"],
            "Nowe": incoming,
            "Zaległe_Start": current_backlog,
            "Do_Wykonania_Total": total_load,
            "Wyprodukowano": produced,
            "Przeniesione_Na_Jutro": remaining,
            "Nadwyżka_Flag": remaining > 0,  # Czy mamy problem?
        }
    )

    current_backlog = remaining

sim_df = pd.DataFrame(simulation_data)

# --- 4. DASHBOARD (WIZUALIZACJA) ---

st.title("🏭 Dashboard Obciążenia Produkcji")
st.markdown(f"Status na dzień: **{datetime.now().strftime('%Y-%m-%d')}**")

# KPI Metrics (Kluczowe wskaźniki na górze)
col1, col2, col3, col4 = st.columns(4)
total_orders = df["Ilość"].sum()
blocked_orders = df[df["Status_Materialowy"] == "BRAK"]["Ilość"].sum()
max_backlog = sim_df["Przeniesione_Na_Jutro"].max()
days_overloaded = sim_df[sim_df["Nadwyżka_Flag"]].shape[0]

col1.metric("Suma Zamówień (14 dni)", f"{total_orders} szt.")
col2.metric(
    "Zablokowane (Brak Surowca)", f"{blocked_orders} szt.", delta_color="inverse"
)
col3.metric(
    "Max Zator (Backlog)",
    f"{max_backlog} szt.",
    delta=-int(max_backlog) if max_backlog > 0 else 0,
)
col4.metric(
    "Dni z przeciążeniem",
    f"{days_overloaded} dni",
    delta="Ryzyko" if days_overloaded > 0 else "OK",
)

st.markdown("---")

# ZAKŁADKI
tab1, tab2, tab3 = st.tabs(
    [
        "📊 Symulacja Obciążenia (Load Graph)",
        "📋 Struktura Zamówień (Kanban)",
        "🗃️ Dane Szczegółowe",
    ]
)

with tab1:
    st.subheader("Symulacja: Efekt 'Kuli Śnieżnej'")
    st.write(
        "Wykres pokazuje, jak niewykonane zamówienia przenoszą się na kolejne dni przy obecnym limicie."
    )

    # Wykres Combo w Plotly
    fig_sim = go.Figure()

    # Słupki: Zaległości (Na dole)
    fig_sim.add_trace(
        go.Bar(
            x=sim_df["Data"],
            y=sim_df["Zaległe_Start"],
            name="Zaległości z wczoraj",
            marker_color="#e67e22",
        )
    )

    # Słupki: Nowe (Na górze)
    fig_sim.add_trace(
        go.Bar(
            x=sim_df["Data"],
            y=sim_df["Nowe"],
            name="Nowe Zamówienia",
            marker_color="#3498db",
        )
    )

    # Linia Limitu
    fig_sim.add_trace(
        go.Scatter(
            x=sim_df["Data"],
            y=[capacity_limit] * len(sim_df),
            mode="lines",
            name="Twój Limit Produkcji",
            line=dict(color="red", width=3, dash="dash"),
        )
    )

    fig_sim.update_layout(
        barmode="stack",
        height=500,
        xaxis_title="Data",
        yaxis_title="Ilość sztuk",
        hovermode="x unified",
    )

    st.plotly_chart(fig_sim, use_container_width=True)

    if days_overloaded > 0:
        st.warning(
            f"⚠️ Uwaga! Przy wydajności {capacity_limit} szt., system generuje opóźnienia w {days_overloaded} dniach. Rozważ zwiększenie mocy lub przesunięcie terminów."
        )

with tab2:
    st.subheader("Struktura Zamówień: Co blokuje produkcję?")

    # Wykres Stacked Bar: OK vs BRAK
    fig_mat = go.Figure()

    fig_mat.add_trace(
        go.Bar(
            x=daily_load["Data"],
            y=daily_load.get("OK", [0] * len(daily_load)),
            name="Surowiec Dostępny",
            marker_color="#2ecc71",
        )
    )

    fig_mat.add_trace(
        go.Bar(
            x=daily_load["Data"],
            y=daily_load.get("BRAK", [0] * len(daily_load)),
            name="BRAK Surowca",
            marker_color="#95a5a6",
            text=daily_load.get("BRAK", 0),
            textposition="auto",
        )
    )

    fig_mat.update_layout(
        barmode="stack", height=400, title="Dostępność Materiałowa vs Popyt"
    )

    st.plotly_chart(fig_mat, use_container_width=True)

with tab3:
    st.subheader("Lista Zamówień")
    # Filtrowanie tabeli
    filter_status = st.multiselect(
        "Filtruj status:", ["OK", "BRAK"], default=["OK", "BRAK"]
    )
    st.dataframe(
        df[df["Status_Materialowy"].isin(filter_status)], use_container_width=True
    )
