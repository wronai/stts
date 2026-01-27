# stts (nodejs)

Voice shell wrapper (STT+TTS) w Node.js (ESM).

Zobacz też:

- `../docs/stt_providers.md`
- `../docs/tts_providers.md`

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

W tej implementacji:

- STT: `whisper_cpp`
- TTS: `espeak`, `piper`, `spd-say`, `flite`, `say` (macOS)

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
- `STTS_NLP2CMD_PARALLEL=1` - prewarm `nlp2cmd` w tle (worker Pythona, mniejsze opóźnienie po STT)
- `STTS_STREAM=1` - strumieniuj output komend (bez buforowania)
- `STTS_FAST_START=1` - szybszy start (mniej detekcji sprzętu)
- `STTS_STT_GPU_LAYERS=35` - whisper.cpp: liczba warstw na GPU (`-ngl`, wymaga build GPU)
- `STTS_STT_PROMPT=...` - whisper.cpp: prompt (jeśli binarka wspiera `--prompt` / `-p`)
- `STTS_GPU_ENABLED=1` - wymuś budowę whisper.cpp z CUDA przy instalacji

## Przydatne opcje CLI

```bash
./stts.mjs --stream "make build"          # output na żywo
./stts.mjs --fast-start                   # szybszy start (domyślnie)
./stts.mjs --full-start                   # pełna detekcja sprzętu
./stts.mjs --list-tts                     # lista providerów TTS
./stts.mjs --tts-provider spd-say --tts-voice pl
./stts.mjs --stt-gpu-layers 35
```

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

### NLP2CMD jako usługa (HTTP) + one-liner

Jeśli uruchomisz `nlp2cmd` w trybie usługi, możesz wysyłać tekst po HTTP:

```bash
nlp2cmd service --host 127.0.0.1 --port 8000
```

One-liner: STT → HTTP service → wypisz samą komendę (wymaga `jq`):

```bash
./stts.mjs --stt-file samples/cmd_ls.wav --stt-only | \
  jq -Rs '{query: ., dsl: "auto"}' | \
  curl -sS http://127.0.0.1:8000/query \
    -H 'Content-Type: application/json' \
    -d @- | \
  jq -r '.command'
```

### Prewarm / tryb równoległy (mniejsze opóźnienie)

`nlp2cmd` jest pakietem Pythona i potrafi mieć zauważalny koszt startu.
Gdy ustawisz `STTS_NLP2CMD_PARALLEL=1`, `stts.mjs` odpala w tle proces Pythona z załadowanym pipeline i dokarmia go tekstem po STT.

### `{STT}` + nlp2cmd (fast-path)

Jeśli chcesz używać dokładnie składni jak w wersji Python (placeholder), możesz uruchomić:

```bash
STTS_NLP2CMD_ENABLED=1 STTS_NLP2CMD_PARALLEL=1 ./stts.mjs nlp2cmd -r --query "{STT}" --auto-confirm
```

Uwaga:

- Tryb `--stt-stream-shell` oraz placeholder `{STT_STREAM}` są na ten moment dostępne tylko w wersji Python (`./stts`).
- `STTS_TTS_NO_PLAY=1` (wyłączenie odtwarzania audio) jest na ten moment Python-only.

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
