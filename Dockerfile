FROM termux/termux-docker:x86_64

ENV PATH=/system/bin:/data/data/com.termux/files/usr/bin
ENV DIR=/data/data/com.termux/files/home/pd-compose

RUN mkdir $DIR
WORKDIR $DIR
COPY --chown=system:system . .

RUN dnsmasq -u root -g root --pid-file=/dnsmasq.pid; \
    sleep 2; \
    pidof dnsmasq >/dev/null 2>&1 || { echo "[!] dnsmasq not running" >&2; exit 1; }; \
    /system/bin/su -s /data/data/com.termux/files/usr/bin/env system -- \
        -i ANDROID_DATA=/data ANDROID_ROOT=/system \
        HOME=/data/data/com.termux/files/home LANG=en_US.UTF-8 \
        PATH=/data/data/com.termux/files/usr/bin \
        PREFIX=/data/data/com.termux/files/usr \
        TMPDIR=/data/data/com.termux/files/usr/tmp \
        TERM=xterm TZ=UTC \
        DEBIAN_FRONTEND=noninteractive \
        sh -c "apt update && apt install -y python python-pip proot && pip install --no-cache-dir -e ".[dev]""

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "pd_compose"]
