# TODO (stts)

## Priorytet: szybkość + gotowość po starcie

- [ ] Ujednolicić "fast start" jako domyślną ścieżkę w obu implementacjach (Python/Node) i ograniczyć kosztowne wykrywanie sprzętu do trybu `--full-start`.
- [ ] Dodać opcjonalny `--prewarm`:
  - weryfikacja obecności binarek/providerów
  - weryfikacja modelu STT (pobranie jeśli brak)
  - opcjonalny krótki "warm-up" whisper.cpp (np. 1s ciszy) dla pierwszego zapytania
- [ ] Dodać profilowanie startu (prosty log z czasami etapów: config, detect, init STT/TTS, gotowość promptu).

## Normalizacja / korekta tekstu z STT (refaktoryzacja plan)

Cel: poprawić niezawodność wykonywania komend, gdy STT zwraca tekst z błędami (fonetyka, interpunkcja, diakrytyki, wtrącenia).

- [ ] Zdefiniować jednolity kontrakt: `normalize_stt(text, context)` gdzie `context` to np.:
  - `command` (tekst używany do uruchomienia komendy)
  - `dictation` (tekst do cytowania/wstawienia w argument)
  - `nlp2cmd` (tekst do translacji)
- [ ] Dodać konfigurację (CLI/env/config):
  - `stt_normalize` (bool)
  - `stt_normalize_context` (`command`/`dictation`)
  - `stt_normalize_language` (domyślnie `language`)
  - `stt_normalize_aggressive` (bool) – czy robić "odważniejsze" podmiany
- [ ] Ujednolicić implementacje:
  - Python: obecny `TextNormalizer` przenieść do wydzielonego modułu albo przynajmniej wydzielonej sekcji API (bez mieszania z STT providerem).
  - Node: obecne `normalizeSTTText` i słowniki (`SHELL_CORRECTIONS`, `PHONETIC_EN_CORRECTIONS`, `REGEX_FIXES`) ujednolicić strukturą z Pythonem.
- [ ] Zapewnić "bezpieczne" reguły bazowe (zawsze):
  - trim
  - usuwanie końcowej interpunkcji
  - normalizacja spacji
  - usuwanie typowych "wtrąceń" (np. "kropka", "przecinek") w kontekście `command`
- [ ] Rozszerzyć reguły w trybie `command`:
  - mały słownik poleceń shell (np. `ls`, `cd`, `git`, `kubectl`) i najczęstszych błędów fonetycznych
  - mapowanie "literowane" (np. "g i t" → `git`) oraz "spacje w skrótach"
- [ ] Dodać tryb "strict" (domyślny) vs "aggressive":
  - strict: tylko poprawki o wysokiej pewności
  - aggressive: dodatkowe heurystyki (np. usuwanie polskich znaków, jeśli brak dopasowania)
- [ ] Testy:
  - zestaw fixture: wejście WAV + oczekiwany tekst (już jest `STTS_MOCK_STT`)
  - osobne testy: `normalize_stt` na tabeli przypadków (PL/EN)
  - przypadki bezpieczeństwa: upewnić się, że normalizacja nie tworzy niebezpiecznych komend (współpraca z `safe_mode`/denylist)

## GPU (STT / whisper.cpp)

- [x] Dodać konfigurację `--stt-gpu-layers` oraz `STTS_STT_GPU_LAYERS`.
- [x] Dodać `STTS_GPU_ENABLED=1` do wymuszenia budowy whisper.cpp z CUDA (jeśli dostępne).
- [ ] Dodać jasne komunikaty diagnostyczne, jeśli użytkownik ustawi `stt_gpu_layers>0`, ale build GPU nie jest dostępny.

## Dokumentacja + stabilność

- [ ] Utrzymać spójny opis opcji CLI i `.env` w root + w `python/` i `nodejs/`.
- [ ] Dopisać krótkie "FAQ" o: streaming output, fast-start, GPU layers, wybór TTS providerów.
