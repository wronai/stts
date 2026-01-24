# stts (python)

Voice shell wrapper (STT+TTS) w Pythonie.

## Uruchomienie

```bash
./stts
./stts --setup
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
- `STTS_NLP2CMD_ENABLED=1` - włącza NL → komenda przez `nlp2cmd`
- `STTS_NLP2CMD_ARGS=-r` - tryb jak w przykładach ("Pokaż użytkowników")
- `STTS_NLP2CMD_CONFIRM=1` - zawsze pytaj o potwierdzenie

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

Uruchomienie interaktywne z cache (modele nie będą pobierane za każdym razem):

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
