Skoro działamy w środowisku korporacyjnym (gdzie zapewne króluje Windows) i chcesz to zrobić **lokalnie**, to kluczem do wydajności i stabilności jest **WSL2 (Windows Subsystem for Linux 2)**. Docker na Windowsie bez WSL2 działa, ale znacznie wolniej (korzysta ze starej wirtualizacji Hyper-V).

Oto kompletny przewodnik instalacji środowiska pod Twój projekt **Local AI (Postgres + pgvector)** na systemie Windows.

-----

### Krok 1: Instalacja WSL2 (Fundament)

WSL2 pozwala uruchomić prawdziwe jądro Linuxa wewnątrz Windowsa. To niezbędne, by Postgres i narzędzia AI działały z natywną szybkością.

1.  Otwórz **PowerShell** jako **Administrator**.
2.  Wpisz komendę:
    ```powershell
    wsl --install
    ```
    *(Jeśli system powie, że WSL jest już zainstalowany, wpisz `wsl --update`, aby mieć najnowszą wersję).*
3.  **Zrestartuj komputer.**
4.  Po restarcie otworzy się okno, poprosi o stworzenie użytkownika i hasła dla Linuxa (Ubuntu). Wpisz cokolwiek (np. user: `admin`, pass: `admin`). To jest niezależne od Twojego konta Windows.

### Krok 2: Instalacja Docker Desktop

1.  Pobierz **Docker Desktop for Windows** ze strony oficjalnej.
2.  Podczas instalacji upewnij się, że zaznaczona jest opcja: **"Use WSL 2 based engine"**. To krytyczne\!
3.  Po zainstalowaniu wejdź w ustawienia Dockera (zębatka) -\> **Resources** -\> **WSL Integration**.
4.  Upewnij się, że integracja z Twoim Ubuntu jest włączona (suwak na ON).

-----

### Krok 3: Konfiguracja Zasobów (Pro Tip - Ochrona RAMu)

To jest punkt, o którym zapomina 90% ludzi. Docker na WSL2 potrafi "zjeść" cały RAM Twojego komputera, jeśli go nie ograniczysz. Przy uruchamianiu modeli LLM (Ollama) i bazy danych, musisz zostawić trochę RAMu dla Windowsa, żeby system nie "zwisł".

1.  Naciśnij `Win + R`, wpisz `%UserProfile%` i naciśnij Enter.
2.  Stwórz tam plik tekstowy o nazwie `.wslconfig` (upewnij się, że nie ma końcówki .txt).
3.  Wklej do środka taką konfigurację (dostosuj do swojego sprzętu):

<!-- end list -->

```ini
[wsl2]
# Jeśli masz 32GB RAM, daj 24GB dla WSL. Jeśli 16GB, daj 12GB.
memory=12GB 
# Ogranicz użycie procesora, żeby Windows nie zamarł przy indeksowaniu wektorów
processors=8
# Swap file - wyłącz lub ogranicz, żeby nie zajechać dysku SSD
swap=4GB
localhostForwarding=true
```

4.  W PowerShell wykonaj restart WSL, żeby zmiany weszły w życie:
    ```powershell
    wsl --shutdown
    ```

-----

### Krok 4: Uruchomienie Twojej Bazy (Project Setup)

Teraz postawimy kontener z Postgresem i pgvectorem.

1.  Stwórz folder na projekt, np. `C:\Projekty\AI-KnowledgeBase`.
2.  Wewnątrz stwórz plik `docker-compose.yml`.
3.  Wklej do niego zoptymalizowaną konfigurację (z uwzględnieniem mapowania portów tylko na localhost dla bezpieczeństwa):

<!-- end list -->

```yaml
version: '3.8'

services:
  vectordb:
    image: pgvector/pgvector:pg16
    container_name: postgres_vector
    restart: always
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: SecretPassword123! # Zmień na własne
      POSTGRES_DB: knowledge_base
    ports:
      - "127.0.0.1:5432:5432" # Dostępne TYLKO z tego komputera (localhost)
    volumes:
      - ./pg_data:/var/lib/postgresql/data
    # Tuning pod wektory (dostosowany do przydziału RAM z kroku 3)
    command: >
      postgres 
      -c shared_buffers=2GB 
      -c work_mem=32MB 
      -c maintenance_work_mem=512MB 
      -c max_parallel_maintenance_workers=2
```

4.  Otwórz terminal w tym folderze i wpisz:
    ```powershell
    docker compose up -d
    ```

### Krok 5: Weryfikacja (Czy to żyje?)

Sprawdźmy, czy baza wstała i czy rozszerzenie `vector` działa.

1.  Wpisz w terminalu:

    ```powershell
    docker exec -it postgres_vector psql -U admin -d knowledge_base
    ```

    (To wejdzie do środka kontenera i uruchomi konsolę SQL).

2.  Wewnątrz konsoli SQL wpisz:

    ```sql
    CREATE EXTENSION IF NOT EXISTS vector;
    SELECT * FROM pg_extension;
    ```

    Jeśli zobaczysz na liście `vector`, to **gratulacje\! Masz w pełni funkcjonalną bazę wektorową na własnym serwerze.**

3.  Aby wyjść, wpisz `\q`.

-----

### Typowe problemy w sieci firmowej (Troubleshooting)

Skoro jesteś w korpo, możesz napotkać te problemy:

1.  **VPN (Cisco AnyConnect / FortiClient):**
      * Często VPNy blokują dostęp do lokalnych podsieci Dockera. Jeśli po włączeniu VPN baza przestaje odpowiadać, musisz dodać wyjątki w ustawieniach VPN lub zmienić podsieć w Dockerze.
2.  **Firewall Windows:**
      * Przy pierwszym uruchomieniu Windows zapyta o zgodę na dostęp do sieci dla "Docker Desktop Backend". **Zezwól na to.**
3.  **Port 5432 zajęty:**
      * Jeśli masz zainstalowanego lokalnie "zwykłego" Postgresa, port 5432 będzie zajęty.
      * Rozwiązanie: Zmień port w `docker-compose.yml` na np. `5433:5432`. Wtedy w Pythonie będziesz łączył się na port 5433.

W tym momencie masz gotowy "fundament". Następnym krokiem jest uruchomienie skryptu Python, który połączy się z tą bazą (na `localhost`) i z Ollamą. Jesteś gotowy, by wkleić ten kod Pythona, który omawialiśmy wcześniej?


-------------------------
darmowe:


**Tak, i jest to bardzo ważny aspekt**, o którym często się zapomina w ferworze prac technicznych.

W sierpniu 2021 roku Docker zmienił politykę licencyjną. Aplikacja **Docker Desktop** (czyli to wygodne okienko na Windows, które instalujesz) **NIE JEST darmowa** dla większych firm.

### 1\. Kiedy musisz płacić?

Twoja firma musi wykupić płatną subskrypcję (Docker Pro, Team lub Business), jeśli spełnia **chociaż jeden** z poniższych warunków:

1.  Zatrudnia **więcej niż 250 pracowników**.
2.  Generuje **ponad 10 milionów dolarów** rocznego przychodu.

Biorąc pod uwagę, że wspomniałeś o oddziałach w Brazylii i pracownikach zagranicznych, **prawdopodobnie Twoja firma wpada w ten płatny próg**. Koszt to zazwyczaj od $5 do $9 za użytkownika miesięcznie.

-----

### 2\. Jak to obejść legalnie i za darmo? (Alternatywy Open Source)

Jeśli dział IT nie chce płacić za licencje Docker Desktop, masz doskonałe, darmowe alternatywy, które działają na Windowsie i robią dokładnie to samo (uruchamiają kontenery).

Najlepszym zamiennikiem dla Ciebie będzie **Rancher Desktop**.

#### Dlaczego Rancher Desktop?

  * Jest w 100% **Open Source i darmowy** (również dla korporacji).
  * Działa na Windowsie z wykorzystaniem **WSL2** (tak jak Docker Desktop).
  * Może używać silnika `moby` (to ten sam silnik co w Dockerze), więc komendy `docker ps`, `docker-compose up` działają tak samo.
  * Nie wymaga zmiany nawyków ani plików konfiguracyjnych.

### Tabela porównawcza: Docker Desktop vs Rancher Desktop

| Cecha | Docker Desktop | Rancher Desktop |
| :--- | :--- | :--- |
| **Licencja** | Płatna dla dużych firm (\>250 os.) | **Darmowa (Apache 2.0)** |
| **GUI (Interfejs)** | Bardzo dopracowany, łatwy | Prostszy, ale wystarczający |
| **Silnik pod spodem** | Docker Engine | Containerd lub Docker (Moby) |
| **Kubernetes** | Wbudowany | Wbudowany (k3s - lżejszy) |
| **Instalacja** | One-click installer | One-click installer |
| **Zgodność z `docker-compose`** | Pełna | **Pełna** (po wybraniu `dockerd` w opcjach) |

-----

### 3\. Jak zainstalować darmową alternatywę (Rancher Desktop)?

Jeśli chcesz uniknąć problemów prawnych w firmie, zrób tak:

1.  **Odinstaluj** Docker Desktop (jeśli już zainstalowałeś).
2.  Pobierz **Rancher Desktop** ze strony oficjalnej (rancherdesktop.io).
3.  Zainstaluj go na Windowsie.
4.  Przy pierwszym uruchomieniu zapyta o konfigurację:
      * **Container Engine:** Wybierz **dockerd (moby)**. To kluczowe\! Dzięki temu będziesz mógł używać standardowych komend `docker`.
      * **Kubernetes:** Możesz wyłączyć (uncheck), jeśli nie potrzebujesz – oszczędzisz RAM.
5.  Rancher automatycznie skonfiguruje WSL2.

**Weryfikacja:**
Otwórz PowerShell i wpisz:

```powershell
docker ps
```

Jeśli komenda działa (mimo braku Docker Desktop), to znaczy, że Rancher przejął stery i działasz w pełni legalnie za darmo.

### 4\. Alternatywa dla Hardkorowców: "Czysty" Docker w WSL2

Możesz też zainstalować samego **Docker Engine** (który jest zawsze darmowy, bo to czysty Linux) bezpośrednio wewnątrz Ubuntu (WSL2), bez żadnej nakładki graficznej w Windowsie.

  * **Zaleta:** Najlżejsze rozwiązanie, zero dodatkowego softu w Windows.
  * **Wada:** Brak GUI. Wszystko robisz z linii komend w terminalu Ubuntu. Trzeba ręcznie uruchamiać usługę dockera (`sudo service docker start`) po każdym restarcie komputera.

**Rekomendacja:**
Dla wygody i szybkości wdrożenia w korporacji – idź w **Rancher Desktop**. Unikniesz faktur, a zachowasz wygodę aplikacji okienkowej.