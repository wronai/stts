# stts (python)

Voice shell wrapper (STT+TTS) w Pythonie.

## Uruchomienie

```bash
./stts
./stts --setup
./stts --init whisper_cpp:tiny
./stts make build
```

## .env (konfiguracja)

Skrypt automatycznie wczytuje `.env` (z katalogu uruchomienia, `python/` albo root repo).
Szablon: `python/.env.example`.

Przykład:

```bash
cp .env.example .env
```

Najważniejsze zmienne:

- `STTS_CONFIG_DIR` - gdzie trzymać modele i config (przydatne dla Docker cache)
- `STTS_TIMEOUT` - czas nagrywania STT (sekundy), domyślnie `5`
- `STTS_NLP2CMD_ENABLED=1` - włącza NL → komenda przez `nlp2cmd`
- `STTS_NLP2CMD_PARALLEL=1` - prewarm `nlp2cmd` w tle (mniejsze opóźnienie po STT)
- `STTS_TTS_VOICE` - głos TTS (np. `pl` dla espeak, `pl_PL-gosia-medium` dla piper)
- `STTS_NLP2CMD_CONFIRM=1` - zawsze pytaj o potwierdzenie
- `STTS_STREAM=1` - strumieniuj output komend (bez buforowania)
- `STTS_FAST_START=1` - szybszy start (mniej detekcji sprzętu)
- `STTS_STT_GPU_LAYERS=35` - whisper.cpp: liczba warstw na GPU (`-ngl`, wymaga build GPU)
- `STTS_STT_PROMPT=...` - whisper.cpp: prompt (jeśli binarka wspiera `--prompt` / `-p`)
- `STTS_GPU_ENABLED=1` - wymuś budowę whisper.cpp z CUDA przy instalacji

### Deepgram (online STT)

Możesz użyć Deepgram jako providera STT (transkrypcja WAV przez REST API).

Wymaga ustawienia klucza API:

- `STTS_STT_PROVIDER=deepgram`
- `STTS_DEEPGRAM_KEY=...`
- (opcjonalnie) `STTS_DEEPGRAM_MODEL=nova-2`

Przykład:

```bash
STTS_STT_PROVIDER=deepgram \
STTS_DEEPGRAM_KEY="sk_..." \
STTS_LANGUAGE=pl \
./stts --stt-file samples/cmd_make_build.wav --stt-only
```

## TTS: szybki setup + autodiagnostyka

Jeśli "TTS nie działa" (cisza), najczęstsze przyczyny:

- brak binarki providera (`espeak` / `piper`)
- dla `piper`: brak modelu `*.onnx` **i** `*.onnx.json`
- brak odtwarzacza audio (`paplay` / `aplay` / `play`) dla `piper`

### Test TTS (bez STT)

```bash
./stts --tts-test "Test syntezatora mowy"
```

### Setup: espeak (Linux)

```bash
make tts-setup-espeak
```

### Setup: piper (Linux, auto-download)

```bash
make tts-setup-piper
```

### Piper: automatyczny install + auto-download w runtime

Wersja Python potrafi automatycznie:

- pobrać binarkę `piper` do `~/.config/stts-python/bin/`
- pobrać model i config głosu do `~/.config/stts-python/models/piper/`

Sterowanie przez `.env`:

```bash
STTS_PIPER_AUTO_INSTALL=1
STTS_PIPER_AUTO_DOWNLOAD=1
STTS_PIPER_RELEASE_TAG=2023.11.14-2
STTS_PIPER_VOICE_VERSION=v1.0.0
```

Ręcznie (CLI):

```bash
./stts --install-piper
./stts --download-piper-voice pl_PL-gosia-medium
./stts --tts-provider piper --tts-voice pl_PL-gosia-medium
./stts --tts-test "Cześć, to działa."
```

Uwaga: logi STT mają timestampy i czasy trwania (nagrywanie / rozpoznawanie), co ułatwia mierzenie opóźnień.

## NLP2CMD (Natural Language → komendy)

Instalacja:

```bash
make pip-nlp2cmd
```

Użycie w shellu stts:

- wpisz: `nlp Pokaż użytkowników`
- albo: ENTER (STT) → powiedz tekst → stts wywoła `nlp2cmd` i zapyta o potwierdzenie

Przykłady:

```bash
nlp2cmd -r "Pokaż użytkowników"

nlp2cmd -r "otwórz https://www.prototypowanie.pl/kontakt/ i wypelnij formularz i wyslij"
```

### NLP2CMD jako usługa (HTTP) + one-liner ze `stts`

`nlp2cmd` ma tryb usługi (`nlp2cmd service`) – to jest wygodne, bo proces jest uruchomiony cały czas i nie płacisz kosztu startu przy każdym wywołaniu.

Start usługi:

```bash
nlp2cmd service --host 127.0.0.1 --port 8000
```

Przykładowe zapytanie (curl):

```bash
curl -sS http://127.0.0.1:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"list files","dsl":"auto"}'
```

One-liner: STT → HTTP service → wypisz samą komendę (wymaga `jq`):

```bash
./stts --stt-once | \
  xargs -I{} curl -sS http://127.0.0.1:8000/query \
    -H 'Content-Type: application/json' \
    -d '{"query":"{}","dsl":"auto"}' | \
  jq -r '.command'
```

One-liner bez `xargs` (bardziej odporny na cudzysłowy/znaki):

```bash
./stts --stt-once | \
  jq -Rs '{query: ., dsl: "auto"}' | \
  curl -sS http://127.0.0.1:8000/query \
    -H 'Content-Type: application/json' \
    -d @- | \
  jq -r '.command'
```

### `{STT}` placeholder (command wrapper)

Możesz uruchomić dowolną komendę i wstawić transkrypt z mikrofonu jako `{STT}`:

```bash
STTS_NLP2CMD_ENABLED=1 STTS_NLP2CMD_PARALLEL=1 ./stts nlp2cmd -r "{STT}" --auto-confirm
```

### Pipeline (jednorazowe STT → stdout)

Tryb `--stt-once` wypisuje sam transkrypt na stdout (logi idą na stderr), więc nadaje się do pipe:

```bash
./stts --stt-once | xargs -I{} nlp2cmd -r "{}"
```

### Pipeline (TTS na końcu)

Tryb `--tts-stdin` czyta stdin i czyta na głos ostatnią niepustą linię (przepuszczając output dalej):

```bash
... | ./stts --tts-stdin
```

Przykład: wygeneruj komendę i przeczytaj ją na głos (bez wykonania):

```bash
./stts --dry-run git commit -m "{STT}" | ./stts --tts-stdin
```

### Jednolinijkowy setup (bez interakcji)

```bash
./stts --init whisper_cpp:tiny
./stts --init whisper_cpp:base
```

### Szybkość / interaktywność

```bash
./stts --stream "make build"          # output na żywo
./stts --fast-start                   # szybszy start (domyślnie)
./stts --full-start                   # pełna detekcja sprzętu
./stts --list-tts                     # lista providerów TTS
```

### whisper.cpp + GPU (CUDA)

```bash
# build GPU podczas instalacji (setup)
STTS_GPU_ENABLED=1 ./stts --setup

# offload warstw na GPU (wymaga build GPU)
./stts --stt-gpu-layers 35
# lub przez env:
STTS_STT_GPU_LAYERS=35 ./stts
```

### TTS w jednej linijce (bez interakcji)

```bash
./stts --tts-provider espeak --tts-voice pl
```

Lepsze (neural) TTS przez `piper`:

```bash
# Provider: piper
./stts --tts-provider piper --tts-voice pl_PL-gosia-medium

# albo podaj ścieżkę do modelu .onnx
./stts --tts-provider piper --tts-voice ~/.config/stts-python/models/piper/pl_PL-gosia-medium.onnx
```

Modele `piper` możesz trzymać w `~/.config/stts-python/models/piper/` jako `*.onnx`.

Wymagania dla `piper`:

- binarka `piper` w `PATH`
- model `*.onnx` w `~/.config/stts-python/models/piper/`
- odtwarzacz audio: `paplay` lub `aplay` lub `play`

Szybki check:

```bash
command -v piper
ls ~/.config/stts-python/models/piper/*.onnx
command -v paplay || command -v aplay || command -v play
```

Konfiguracja zapisywana jest w `~/.config/stts-python/config.json`.

## Komendy interaktywne (Y/n itd.)

Jeśli masz zainstalowane `pexpect`, stts potrafi:

- wykryć że program czeka na input
- przeczytać ostatnią linijkę (TTS)
- pozwolić odpowiedzieć głosem lub klawiaturą

Instalacja przykładowych bibliotek:

```bash
make pip-extras
```

## Testowanie bez mikrofonu (symulacja w Docker/CI)

Najpierw generujesz próbkę do WAV, potem podajesz ją do STT:

```bash
espeak -v pl -s 160 -w samples/cmd_make_build.wav "make build"
./stts --stt-file samples/cmd_make_build.wav --stt-only
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
Domyślnie `CACHE_DIR=~/.config/stts-python`.

Możesz nadpisać katalog cache:

```bash
make docker-test CACHE_DIR=/tmp/stts-python-cache
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
  stts-python:latest
```
