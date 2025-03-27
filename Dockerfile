FROM lsiobase/kasmvnc:ubuntujammy

ARG ANKI_VERSION=23.12.1

RUN \
  apt-get update && \
  apt-get install -y anki wget zstd xdg-utils libxcb-xinerama0 libxcb-cursor0 && \
  dpkg --remove anki && \
  wget https://github.com/ankitects/anki/releases/download/${ANKI_VERSION}/anki-${ANKI_VERSION}-linux-qt6.tar.zst && \
  tar --use-compress-program=unzstd -xvf anki-${ANKI_VERSION}-linux-qt6.tar.zst && \
  cd anki-${ANKI_VERSION}-linux-qt6 && ./install.sh &&  cd .. && \
  rm -rf anki-${ANKI_VERSION}-linux-qt6 anki-${ANKI_VERSION}-linux-qt6.tar.zst && \
  apt-get clean && \
  mkdir -p /config/.local/share && \
  ln -s /config/app/Anki  /config/.local/share/Anki  && \
  ln -s /config/app/Anki2 /config/.local/share/Anki2 && \
  mkdir -p /config/app/Anki2/addons21/2055492159

COPY ankiConnectConfig.json /config/app/Anki2/addons21/2055492159/config.json
VOLUME "/config/app" 

COPY ./root /

# Create addon directory and copy config
RUN mkdir -p /config/app/Anki2/addons21/2055492159
COPY ./config/anki/ankiConnectConfig.json /config/app/Anki2/addons21/2055492159/config.json.orig

# Create a script to ensure AnkiConnect config is always correct
RUN echo '#!/bin/bash\n\
mkdir -p /config/app/Anki2/addons21/2055492159\n\
if [ -f "/config/app/Anki2/addons21/2055492159/config.json" ]; then\n\
    cp /config/app/Anki2/addons21/2055492159/config.json /config/app/Anki2/addons21/2055492159/config.json.bak\n\
fi\n\
cp /config/app/Anki2/addons21/2055492159/config.json.orig /config/app/Anki2/addons21/2055492159/config.json\n\
' > /config/app/Anki2/addons21/2055492159/update_config.sh && \
chmod +x /config/app/Anki2/addons21/2055492159/update_config.sh
