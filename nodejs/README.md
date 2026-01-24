# stts (nodejs)

Voice shell wrapper (STT+TTS) w Node.js (ESM).

## Wymagania

- Node.js 18+
- Linux/macOS (nagrywanie w tej wersji jest wspierane głównie na Linux; do testów używaj `--stt-file`)

## Uruchomienie

```bash
./stts.mjs
./stts.mjs --setup
./stts.mjs make build
```

Uwaga: część "rozszerzeń" CLI (np. `{STT}` placeholder, `--stt-once`, `--init`) jest dostępna tylko w wersji Python (`./stts`).

## .env (konfiguracja)

Skrypt automatycznie wczytuje `.env` (z katalogu uruchomienia, `nodejs/` albo root repo).
Szablon: `nodejs/.env.example`.

Przykład:

```bash
cp .env.example .env
```

Najważniejsze zmienne:

- `STTS_CONFIG_DIR` - gdzie trzymać modele i config (przydatne dla Docker cache)
- `STTS_NLP2CMD_ENABLED=1` - włącza NL → komenda przez `nlp2cmd` (CLI)
- `STTS_NLP2CMD_ARGS=-r` - tryb jak w przykładach ("Pokaż użytkowników")
- `STTS_NLP2CMD_CONFIRM=1` - zawsze pytaj o potwierdzenie

## NLP2CMD (Natural Language → komendy)

Node.js wersja wywołuje `nlp2cmd` jako zewnętrzną binarkę (to pakiet Pythona).

Instalacja:

```bash
make pip-nlp2cmd
```

Użycie:

- wpisz: `nlp Pokaż użytkowników`
- albo: ENTER (STT) → powiedz tekst → stts wywoła `nlp2cmd` i zapyta o potwierdzenie

Przykłady:

```bash
nlp2cmd -r "Pokaż użytkowników"
nlp2cmd -r "otwórz https://www.prototypowanie.pl/kontakt/ i wypelnij formularz i wyslij"
```

## Testowanie bez mikrofonu (symulacja w Docker/CI)

Najpierw generujesz próbkę do WAV, potem podajesz ją do STT:

```bash
espeak -v pl -s 160 -w samples/cmd_make_build.wav "make build"
./stts.mjs --stt-file samples/cmd_make_build.wav --stt-only
```

Opcje:

- `--stt-file PATH` - zamiast nagrywania użyj pliku WAV
- `--stt-only` - tylko transkrypcja (nie uruchamiaj komendy)

## Docker

```bash
make docker-build
make docker-test
```

Testy i uruchomienie interaktywne montują cache/config jako volume (żeby nie pobierać modeli za każdym razem).
Domyślnie `CACHE_DIR=~/.config/stts-nodejs`.

Możesz nadpisać katalog cache:

```bash
make docker-test CACHE_DIR=/tmp/stts-nodejs-cache
```

Jeśli chcesz uruchomić testy dla wszystkich platform (Python + Node.js), użyj w root repo:

```bash
make test-docker
```

Uruchomienie interaktywne z cache:

```bash
make docker-run
```

### Typowe problemy dźwięku w Dockerze

W Dockerze zwykle **nie ma dostępu do audio**, więc testy używają `--stt-file`.
Jeśli chcesz prawdziwe nagrywanie/odtwarzanie z kontenera (Linux):

```bash
docker run --rm -it \
  --device /dev/snd \
  -e PULSE_SERVER=unix:/tmp/pulse/native \
  -v $XDG_RUNTIME_DIR/pulse/native:/tmp/pulse/native \
  stts-nodejs:latest
```
