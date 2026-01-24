# stts (python)

Voice shell wrapper (STT+TTS) w Pythonie.

## Uruchomienie

```bash
./stts
./stts --setup
./stts make build
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
