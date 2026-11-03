ARG BUILD_FROM
FROM ${BUILD_FROM}

# ICONA → RTSP bridge (adapted from mnestrud/comelit-man, Apache-2.0)
ENV LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /opt/icona_bridge

RUN apk add --no-cache \
        python3 \
        py3-pip \
        ffmpeg \
        libstdc++ \
    && pip3 install --no-cache-dir --break-system-packages \
        "aiohttp>=3.9,<4"

COPY rootfs/opt/icona_bridge/ /opt/icona_bridge/
COPY run.sh /run.sh
RUN chmod a+x /run.sh \
    && python3 -m compileall -q /opt/icona_bridge || true

CMD ["/run.sh"]
