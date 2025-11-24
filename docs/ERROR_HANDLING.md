# Obsługa Błędów i Zabezpieczenia

## Podsumowanie zabezpieczeń

### ✅ Zabezpieczenia w `CsvGenericRepository.load_all()`

1. **Brak pliku CSV** → zwraca pustą listę `[]` (linia 68-70)
2. **Błąd parsowania wiersza** → wiersz pomijany, logowany warning (linia 64-67)
3. **Brak wymaganych pól** → wiersz pomijany, logowany warning (linia 64-77)
4. **Błąd tworzenia obiektu** → wiersz pomijany, logowany warning (linia 80-82)
5. **Błąd konwersji typów** → pole pomijane, logowany warning (linia 141-143)

### ✅ Zabezpieczenia w `_map_row_to_types()`

1. **Puste opcjonalne pola** → ustawiane na `None` (linia 96-98)
2. **Pola z wartościami domyślnymi** → używane wartości domyślne (linia 101-104)
3. **Błąd parsowania daty** → pole pomijane, logowany warning (linia 125-128)
4. **Błąd konwersji int/bool** → pole pomijane, logowany warning (linia 141-143)

### ✅ Zabezpieczenia w `analyze_notes_with_llm()`

1. **`notes` jest None** → zwraca bezpieczny wynik (linia 44-58)
2. **`customer_id` jest pusty** → zwraca bezpieczny wynik (linia 60-68)
3. **`sample_date` jest None** → zwraca bezpieczny wynik (linia 70-78)
4. **Brak notatek dla klienta** → zwraca bezpieczny wynik (linia 66-75)
5. **Pusta treść notatki** → notatka pomijana (linia 84-88)
6. **Błąd LLM** → fallback do bezpiecznej odpowiedzi (linia 48-58)

### ✅ Zabezpieczenia w `sample_followup.py`

1. **Brak próbek** → wczesne zakończenie (linia 193-195)
2. **`all_notes` jest None** → ustawiane na pustą listę (linia 195-197)
3. **Pusta próbka w liście** → pomijana (linia 201-203)
4. **Brak `customer_id`** → próbka pomijana (linia 203-206)
5. **Brak `date_sent`** → próbka pomijana (linia 206-209)
6. **Brak klienta** → próbka pomijana (linia 240-243)
7. **Brak sprzedawcy** → próbka pomijana (linia 245-247)
8. **`best_note_analysis` jest None** → bezpieczny dostęp (linia 303-304)
9. **Brak zadań do wysłania** → wczesne zakończenie (linia 298-300)
10. **Pusta lista zadań** → pomijana (linia 301-303)
11. **Puste zadanie w liście** → pomijane (linia 320-322)
12. **Brak customer/sample dla zadania** → bezpieczne wartości domyślne (linia 323-325)

## Scenariusze testowe

Uruchom `python scripts/test_error_handling.py` aby zweryfikować wszystkie scenariusze.

## Rekomendacje

1. **Zawsze sprawdzaj wyniki** przed użyciem:
   ```python
   samples = repo.load_all()
   if not samples:
       logger.info("Brak danych do przetworzenia")
       return
   ```

2. **Używaj bezpiecznego dostępu do słowników**:
   ```python
   # Zamiast: analysis_result['best_note_analysis'].get('status')
   best_analysis = analysis_result.get('best_note_analysis')
   status = best_analysis.get('status') if best_analysis else 'unknown'
   ```

3. **Waliduj dane przed użyciem**:
   ```python
   if not sample.customer_id:
       logger.warning("Brak customer_id, pomijam")
       continue
   ```

