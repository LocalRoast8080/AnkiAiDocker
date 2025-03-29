FROM lsiobase/kasmvnc:ubuntujammy

ARG ANKI_VERSION=23.12.1

RUN \
  apt-get update && \
  apt-get install -y anki wget zstd xdg-utils libxcb-xinerama0 libxcb-cursor0 curl python3-pip && \
  dpkg --remove anki && \
  wget https://github.com/ankitects/anki/releases/download/${ANKI_VERSION}/anki-${ANKI_VERSION}-linux-qt6.tar.zst && \
  tar --use-compress-program=unzstd -xvf anki-${ANKI_VERSION}-linux-qt6.tar.zst && \
  cd anki-${ANKI_VERSION}-linux-qt6 && ./install.sh &&  cd .. && \
  rm -rf anki-${ANKI_VERSION}-linux-qt6 anki-${ANKI_VERSION}-linux-qt6.tar.zst && \
  apt-get clean && \
  mkdir -p /config/.local/share && \
  ln -s /config/app/Anki  /config/.local/share/Anki  && \
  ln -s /config/app/Anki2 /config/.local/share/Anki2

# Create AnkiConnect config
RUN mkdir -p /config/app/Anki2/addons21/2055492159 && \
    echo '{\n\
    "apiKey": null,\n\
    "apiLogPath": null,\n\
    "ignoreOriginList": [],\n\
    "webBindAddress": "0.0.0.0",\n\
    "webBindPort": 8765,\n\
    "webCorsOrigin": "*",\n\
    "webCorsOriginList": [\n\
        "*"\n\
    ]\n\
}' > /config/app/Anki2/addons21/2055492159/config.json

VOLUME "/config/app"

COPY ./root /
