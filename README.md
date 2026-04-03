# 🚀 Pump-Oracle

> Automatyczny skaner obiecujących memecoinów na blockchainie Solana z powiadomieniami w czasie rzeczywistym przez Telegram.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![License](https://img.shields.io/badge/licencja-MIT-green)
![Tests](https://github.com/4Opm/Pump-Oracle/actions/workflows/tests.yml/badge.svg)

---

## 📌 Opis projektu

Pump-Oracle co 15 minut skanuje zdecentralizowane giełdy na blockchainie Solana w poszukiwaniu wczesnych okazji inwestycyjnych wśród memecoinów. Pobiera dane on-chain z DexScreener API, filtruje je według konfigurowalnych kryteriów i wysyła natychmiastowe alerty przez Telegram gdy znajdzie obiecujące tokeny.

**Projekt portfolio demonstrujący:**
- Integrację z REST API i budowę pipeline'ów danych
- Analizę danych on-chain z użyciem pandas
- Automatyczne systemy powiadomień
- Czystą architekturę i profesjonalny workflow z Git

---

## ⚙️ Jak to działa
```
DexScreener API → Pobierz boosted/trending tokeny
       ↓
Analizator on-chain → Filtruj wg płynności, wolumenu, wieku, zmiany ceny
       ↓
Powiadomienia Telegram → Wyślij alerty dla ciekawych tokenów
       ↓
Główna pętla → Powtarzaj co 15 minut
```

---

## 🔍 Kryteria filtrowania

Token jest oznaczany jako ciekawy gdy spełnia **wszystkie** poniższe warunki:

| Metryka | Próg |
|---|---|
| Płynność | > $5 000 |
| Wolumen 24h | > $10 000 |
| Wiek pary | < 72 godziny |
| Zmiana ceny 1h | > +5% |
| Stosunek kupna/sprzedaży (1h) | > 1.1 |

Wszystkie progi są konfigurowalne w `src/analyzers/onchain.py`.

---

## 📁 Struktura projektu
```
solana-memecoin-bot/
├── src/
│   ├── analyzers/
│   │   └── onchain.py       # Analiza i filtrowanie danych on-chain
│   ├── notifiers/
│   │   └── telegram.py      # Formatowanie i wysyłanie powiadomień Telegram
│   ├── data/
│   │   └── fetcher.py       # Integracja z DexScreener API
│   └── main.py              # Główna pętla bota
├── tests/
│   └── test_analyzer.py     # Testy jednostkowe modułu analizatora
├── conftest.py              # Konfiguracja pytest
├── requirements.txt         # Zależności projektu
└── .env.example             # Szablon zmiennych środowiskowych
```

---

## 🛠️ Stack technologiczny

| Warstwa | Technologia |
|---|---|
| Język | Python 3.11 |
| Analiza danych | pandas |
| Zapytania HTTP | requests |
| Powiadomienia | Telegram Bot API |
| Testy | pytest |
| Źródło danych | DexScreener API (bezpłatne, bez klucza) |

---

## 🚀 Uruchomienie projektu

### Wymagania
- Python 3.11+
- Konto Telegram (do powiadomień)

### Instalacja
```bash
# Sklonuj repozytorium
git clone https://github.com/Opium-js/Pump-Oracle.git
cd Pump-Oracle

# Utwórz wirtualne środowisko
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Mac/Linux

# Zainstaluj zależności
pip install -r requirements.txt
```

### Konfiguracja
```bash
# Skopiuj szablon pliku .env
cp .env.example .env
```

Uzupełnij plik `.env` swoimi danymi:
```
TELEGRAM_BOT_TOKEN=twój_token_bota
TELEGRAM_CHAT_ID=twoje_chat_id
```

Jak uzyskać dane do Telegrama:
1. Otwórz Telegram → wyszukaj **@BotFather** → `/newbot` → skopiuj token
2. Wyszukaj **@userinfobot** → `/start` → skopiuj swoje ID

### Uruchomienie bota
```bash
python -m src.main
```

### Uruchomienie testów
```bash
pytest tests/ -v
```

---

## 📊 Przykładowe działanie
```
2026-04-02 11:41:13 [INFO] Pump-Oracle uruchomiony!
2026-04-02 11:41:13 [INFO] Skan co 15 minut
2026-04-02 11:41:13 [INFO] Rozpoczynam skan...
2026-04-02 11:41:13 [INFO] Skan zakończony: 3/148 ciekawych par
2026-04-02 11:41:13 [INFO] autism/SOL     vol: $322,395 | liq: $29,131 | 1h: +207.0% | wiek: 3.0h
2026-04-02 11:41:13 [INFO] OilWhale/SOL   vol: $191,014 | liq: $38,471 | 1h: +446.0% | wiek: 0.3h
2026-04-02 11:41:13 [INFO] Indah/SOL      vol: $114,246 | liq: $8,019  | 1h:  +19.2% | wiek: 2.1h
```

---

## ⚠️ Zastrzeżenie

Ten projekt powstał **wyłącznie w celach edukacyjnych**. Memecoiny są aktywami o ekstremalnie wysokim ryzyku. Zawsze przeprowadzaj własną analizę przed podjęciem jakichkolwiek decyzji inwestycyjnych. Autor nie ponosi odpowiedzialności za ewentualne straty finansowe.

---

## 📄 Licencja

Licencja MIT — możesz swobodnie używać i modyfikować projekt na własne potrzeby.

---

## 🤖 Narzędzia i wsparcie

Projekt został zbudowany przy pomocy [Claude](https://claude.ai) — asystenta AI, który wspierał proces planowania architektury, pisania kodu oraz rozwiązywania problemów technicznych napotkanych podczas rozwoju projektu.