FROM python:3.11-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    espeak \
    sox \
    alsa-utils \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN chmod +x /app/stts /app/scripts/generate_samples.sh /app/tests/docker_test.sh

CMD ["/app/tests/docker_test.sh"]
