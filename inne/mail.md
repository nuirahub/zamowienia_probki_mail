Oto gotowy szablon HTML, zaprojektowany tak, aby był czytelny, estetyczny i – co najważniejsze – **utrzymany w pozytywnym, partnerskim tonie**.

Zamiast straszyć "niezrealizowanymi zadaniami", używamy języka korzyści ("dbamy o relację") i zrozumienia ("w natłoku spraw").

### Cechy tego szablonu:

1.  **Responsywność:** Oparty na tabelach (bezpieczny dla Outlooka i Gmaila).
2.  **Modularność:** Sekcja "Przypomnienie o zaległościach" jest oddzielona wizualnie – można ją łatwo usunąć w kodzie Python, jeśli dany sprzedawca nie ma zaległości.
3.  **Placeholdery:** Miejsca w nawiasach klamrowych `{...}` są gotowe do podstawienia danych w Pythonie (f-string).

-----

### Kod HTML Szablonu

Zapisz ten kod np. jako `email_template.html` lub wklej bezpośrednio do zmiennej w Pythonie.

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Status Próbek i Zadania ERP</title>
    <style>
        /* Podstawowe style dla klientów pocztowych */
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; color: #333333; }
        .container { max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .header { background-color: #0056b3; color: #ffffff; padding: 20px; text-align: center; }
        .content { padding: 25px; line-height: 1.6; }
        .highlight-box { background-color: #eef7ff; border-left: 5px solid #0056b3; padding: 15px; margin: 20px 0; border-radius: 4px; }
        .task-list { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .task-list th { text-align: left; border-bottom: 2px solid #ddd; padding: 8px; font-size: 12px; color: #666; text-transform: uppercase; }
        .task-list td { border-bottom: 1px solid #eee; padding: 10px 8px; font-size: 14px; }
        .warning-section { background-color: #fff8e1; border: 1px solid #ffe082; border-radius: 6px; padding: 15px; margin-top: 30px; }
        .btn { display: inline-block; padding: 10px 20px; background-color: #28a745; color: #ffffff; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 10px; }
        .footer { background-color: #eeeeee; padding: 15px; text-align: center; font-size: 12px; color: #777777; }
        h2 { margin-top: 0; color: #0056b3; }
        h3 { margin-bottom: 5px; color: #444; }
    </style>
</head>
<body>

<div class="container">
    <div class="header">
        <h1>📦 Aktualizacja Statusu Próbek</h1>
    </div>

    <div class="content">
        <p>Cześć <strong>{imie_handlowca}</strong>,</p>
        
        <p>System odnotował wysyłkę nowych próbek do Twojego klienta. To idealny moment, aby zaplanować krótki telefon i zapytać o pierwsze wrażenia. Dbałość o ten etap często decyduje o finalnym zamówieniu!</p>

        <div class="highlight-box">
            <h3>🆕 Nowa wysyłka zrealizowana:</h3>
            <p><strong>Klient:</strong> {klient_nazwa}<br>
            <strong>Próbka:</strong> {probka_id} (Wysłano: {data_wysylki})</p>
            <p style="font-size: 13px; color: #555;">
                <em>ℹ️ W systemie ERP zostało automatycznie utworzone zadanie "Weryfikacja odbioru próbek".</em>
            </p>
        </div>

        <div class="warning-section">
            <h3>🗂️ Rzuć okiem na otwarte tematy</h3>
            <p>W natłoku codziennych obowiązków łatwo coś przeoczyć. Poniżej lista zadań związanych z próbkami, które w systemie widnieją jako <strong>niezrealizowane</strong> (starsze niż 7 dni).</p>
            
            <p>Być może temat jest już załatwiony, tylko nie został "odkliknięty"? Jeśli tak – zaktualizuj proszę status, abyśmy mieli porządek w danych.</p>

            <table class="task-list">
                <thead>
                    <tr>
                        <th>Klient</th>
                        <th>Próbka</th>
                        <th>Data utworzenia</th>
                    </tr>
                </thead>
                <tbody>
                    {tabela_zaleglosci_rows}
                </tbody>
            </table>

            <div style="text-align: center; margin-top: 20px;">
                <a href="https://twoj-system-erp.pl" class="btn">Przejdź do ERP i zamknij zadania</a>
            </div>
        </div>
    </div>

    <div class="footer">
        <p>Wiadomość wygenerowana automatycznie przez Asystenta Sprzedaży.<br>
        Jeśli masz pytania, skontaktuj się z administratorem.</p>
    </div>
</div>

</body>
</html>
```

-----

### Jak użyć tego w Pythonie?

Aby kod był czysty, proponuję funkcję pomocniczą, która generuje wiersze tabeli HTML dla drugiej części maila, a następnie skleja całość.

Oto przykład implementacji w Twoim skrypcie:

```python
def generate_email_body(imie, nowy_task, zalegle_taski):
    """
    imie: str - imię handlowca
    nowy_task: object Task - obiekt tego konkretnego, nowego zadania
    zalegle_taski: List[Task] - lista starych zadań do przypomnienia
    """
    
    # 1. Budowanie wierszy tabeli dla zaległości
    rows_html = ""
    if zalegle_taski:
        for t in zalegle_taski:
            data_str = t.created_at.strftime('%Y-%m-%d')
            rows_html += f"""
            <tr>
                <td>{t.customer_id}</td>
                <td>{t.sample_id}</td>
                <td style="color: #d9534f;">{data_str}</td>
            </tr>
            """
    else:
        # Jeśli brak zaległości, wstawiamy info, że czysto
        rows_html = "<tr><td colspan='3' style='text-align:center; color:green;'>Brak zaległych zadań! Dobra robota. 👍</td></tr>"

    # 2. Wczytanie szablonu (zakładam, że masz go w zmiennej string lub pliku)
    # Tu używam uproszczonej wersji zmiennej dla przykładu
    template = """... kod HTML z góry ...""" 
    
    # W praktyce lepiej trzymać HTML w osobnym pliku i robić:
    # with open('email_template.html', 'r', encoding='utf-8') as f:
    #    template = f.read()

    # 3. Wypełnienie danych
    # Używamy metody .format(), bo w HTML są klamry {} od CSS, 
    # więc f-stringi bywają problematyczne (trzeba podwajać klamry CSS {{ }}).
    # Bezpieczniej jest użyć replace lub .format z nazwanymi argumentami.
    
    # Najprostsza metoda "search & replace" dla uniknięcia konfliktów z CSS:
    filled_email = template.replace("{imie_handlowca}", imie)
    filled_email = filled_email.replace("{klient_nazwa}", nowy_task.customer_id)
    filled_email = filled_email.replace("{probka_id}", nowy_task.sample_id)
    filled_email = filled_email.replace("{data_wysylki}", nowy_task.created_at.strftime('%d.%m.%Y'))
    filled_email = filled_email.replace("{tabela_zaleglosci_rows}", rows_html)
    
    return filled_email

# UŻYCIE W KODZIE (wewnątrz process_new_samples):
# ...
# repo.add_task(sample.id, sample.customer_id)
# 
# # Pobierz zaległości dla TEGO KONKRETNEGO klienta lub handlowca (zależy jak masz dane)
# # Na potrzeby przykładu bierzemy wszystkie overdue:
# overdue_list = [t for t in repo.get_all_tasks() if t.status == 'OPEN'] 
#
# email_html = generate_email_body("Anna", nowy_task=sample_task, zalegle_taski=overdue_list)
# send_email("anna@firma.pl", "📦 Nowe próbki i status zadań", email_html)
```

### Kluczowe elementy psychologiczne w treści:

1.  **"Cześć [Imię]"** – personalizacja zmniejsza dystans.
2.  **"To świetna okazja"** – przekuwamy obowiązek ("musisz zadzwonić") w szansę sprzedażową ("okazja do rozmowy").
3.  **"Wskoczyło zadanie"** – informacja techniczna, ale podana lekko.
4.  **"Rzuć okiem" / "W natłoku obowiązków"** – zdejmujemy winę ze sprzedawcy. Nie mówimy "zaniedbałeś", tylko "rozumiemy, że jesteś zajęty, sprawdź tylko czy system ma rację".
5.  **Tabela** – konkret. Sprzedawca widzi czarno na białym, co "wisi", bez konieczności logowania się do ERP, żeby tylko to sprawdzić.
6.  **"Być może temat jest już załatwiony"** – to najważniejsze zdanie. Dajemy furtkę wyjścia z twarzą ("Zrobiłem to, tylko zapomniałem kliknąć").