FROM node:20-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    espeak \
    sox \
    alsa-utils \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

ENV STTS_CONFIG_DIR=/stts-cache
VOLUME ["/stts-cache"]

RUN chmod +x /app/stts.mjs /app/scripts/generate_samples.sh /app/tests/docker_test.sh

CMD ["/app/tests/docker_test.sh"]
