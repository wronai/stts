# stts (python)

Voice shell wrapper (STT+TTS) w Pythonie.

Zobacz też:

- [stt_providers.md](../docs/stt_providers.md)
- [tts_providers.md](../docs/tts_providers.md)

## Uruchomienie

```bash
./stts
./stts --setup
./stts --init whisper_cpp:tiny
./stts make build
```

### Nadpisanie STT z linii poleceń

Możesz nadpisać providera/model STT bez zmiany `.env`:

```bash
./stts --stt-provider whisper_cpp --stt-file samples/cmd_ls.wav --stt-only
./stts --stt-provider vosk --stt-model small-pl --stt-file samples/cmd_ls.wav --stt-only
./stts --stt-provider faster_whisper --stt-model base --stt-file samples/cmd_ls.wav --stt-only
STTS_FASTER_WHISPER_DEVICE=cpu STTS_FASTER_WHISPER_COMPUTE_TYPE=int8 \
  ./stts --stt-provider faster_whisper --stt-model base --stt-file samples/cmd_ls.wav --stt-only
./stts --stt-provider deepgram --stt-file samples/cmd_ls.wav --stt-only
```

## Benchmark: porównanie STT/TTS (latency + precyzja)

Pomiary z `./examples/benchmark.sh`.

Uwaga o precyzji (accuracy): próbki w `python/samples/*.wav` są generowane przez TTS (np. `espeak`) i następnie rozpoznawane przez STT.
To jest dobre jako test regresji i pipeline, ale **nie jest miarą jakości rozpoznawania z mikrofonu**.

Metryki:

- **avg/p95**: średnie i 95-percentyl czasu.
- **WER**: word error rate (0.0 = idealnie, 1.0 = źle).

### STT (Speech-to-Text)

| Provider | Model | avg latency (s) | p95 latency (s) | WER (avg) | Notes |
|---|---:|---:|---:|---:|---|
| `whisper_cpp` | `default` | 0.7076 | 0.7511 | 1.0000 | szybki, ale syntetyczne próbki mogą być rozpoznawane jako `[MUZYKA]` |
| `vosk` | `small-pl` | 1.1679 | 1.2912 | 1.0000 | stabilny offline, ale accuracy zależy od jakości próbek |

### TTS (Text-to-Speech)

Pomiary TTS w benchmarku są wykonywane z `STTS_TTS_NO_PLAY=1` (bez odtwarzania audio), aby mierzyć samą syntezę.

| Provider | Voice | avg latency (s) | p95 latency (s) | Notes |
|---|---:|---:|---:|---|
| `piper` | `pl` (alias → `pl_PL-gosia-medium`) | 0.4827 | 0.5345 | neural, najlepsza jakość |
| `espeak` | `pl` | 0.1246 | 0.1258 | najszybszy, ale gorsza jakość |

### Pipeline STT→TTS (round-robin, na przemian)

Benchmark testuje kombinacje STT×TTS w trybie „na przemian” (round-robin) z warmup i N iteracji, podając avg/p95.

| STT | TTS | avg total (s) | p95 total (s) |
|---|---|---:|---:|
| `whisper_cpp` | `piper` | 1.1912 | 1.3164 |
| `whisper_cpp` | `espeak` | 0.9137 | 1.0259 |
| `vosk` | `piper` | 1.6684 | 1.8509 |
| `vosk` | `espeak` | 1.3947 | 1.5817 |

### Jak odtworzyć benchmark

Uruchom z root repo:

```bash
STTS_BENCH_WARMUP=1 STTS_BENCH_ITERS=3 ./examples/benchmark.sh
```

Wyniki CSV są zapisywane w `/tmp/stts_benchmark_*/results.csv`.

## .env (konfiguracja)

Skrypt automatycznie wczytuje `.env` (z katalogu uruchomienia, `python/` albo root repo).
Szablon: `python/.env.example`.

 Przykład:
 
 ```bash
 cp .env.example .env
 ```

 ### Setup: Vosk (STT) + Piper (TTS) — komendy
 
 ```bash
 sudo apt update
 sudo apt install -y curl unzip pulseaudio-utils alsa-utils sox
 
 cd python
 cp .env.example .env
 
 make stt-vosk-pl
 make tts-setup-piper
 
 ./stts --tts-provider piper --tts-voice pl_PL-gosia-medium --tts-test "Cześć, to działa."
 ./stts --stt-provider vosk --stt-model small-pl --stt-file samples/cmd_ls.wav --stt-only
 ```
 
 Wpis do `.env` (przykład):
 
 ```bash
 STTS_STT_PROVIDER=vosk
 STTS_STT_MODEL=small-pl
 STTS_TTS_PROVIDER=piper
 STTS_TTS_VOICE=pl_PL-gosia-medium
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
- `STTS_TTS_NO_PLAY=1` - nie odtwarzaj audio (przydatne w CI/Docker)
- `STTS_WHISPER_MAX_LEN=...` - whisper.cpp: `-ml` (opcjonalnie)
- `STTS_WHISPER_WORD_THOLD=...` - whisper.cpp: `-wt` (opcjonalnie)
- `STTS_WHISPER_NO_SPEECH_THOLD=...` - whisper.cpp: `-nth` (opcjonalnie)
- `STTS_WHISPER_ENTROPY_THOLD=...` - whisper.cpp: `-et` (opcjonalnie)
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
STTS_NLP2CMD_ENABLED=1 STTS_NLP2CMD_PARALLEL=1 ./stts nlp2cmd -r --query "{STT}" --auto-confirm
```

Jeśli zobaczysz błąd typu `Error: No such command '...` (nlp2cmd potraktował pierwsze słowo jako subkomendę), użyj `--dry-run` żeby sprawdzić quoting:

```bash
STTS_NLP2CMD_ENABLED=1 ./stts --dry-run nlp2cmd -r --query "{STT}" --auto-confirm
```

Alternatywa (zawsze odporna na quoting): STT → stdout → `nlp2cmd stdin`:

```bash
./stts --stt-once | nlp2cmd -r stdin --auto-confirm
```

`{STT_STREAM}` jest aliasem `{STT}` (MVP).

### Voice-driven REPL (placeholder shell)

Tryb `--stt-stream-shell` działa jak mini-shell: w pętli nasłuchuje audio, robi STT (VAD stop), podstawia `{STT}` i uruchamia komendę-szablon.

```bash
./stts --stt-stream-shell --cmd 'nlp2cmd -r --query "{STT}" --auto-confirm'
```

W CI/Docker możesz zrobić one-shot przez `--stt-file`:

```bash
STTS_MOCK_STT=1 ./stts --stt-file samples/cmd_ls.wav \
  --stt-stream-shell --cmd 'echo "{STT}"' --dry-run
```

### Pipeline (jednorazowe STT → stdout)

Tryb `--stt-once` wypisuje sam transkrypt na stdout (logi idą na stderr), więc nadaje się do pipe:

```bash
./stts --stt-once | xargs -I{} nlp2cmd -r "{}"
```

Alternatywnie, bezpośrednio przez `stts` (stdin → nlp2cmd):

```bash
./stts --stt-once | ./stts nlp2cmd -r stdin --auto-confirm
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
./stts --list-stt                     # lista providerów STT
./stts --list-tts                     # lista providerów TTS

./stts --stt-provider vosk --stt-model small-pl --stt-file samples/cmd_ls.wav --stt-only
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
