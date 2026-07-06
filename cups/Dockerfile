FROM debian:trixie-slim

RUN apt-get update && apt-get install -y \
    cups avahi-daemon dbus wget \
    && dpkg --add-architecture i386 \
    && apt-get update \
    && apt-get install -y libc6-i386 lib32gcc-s1 lib32stdc++6 \
    && rm -rf /var/lib/apt/lists/*

COPY dcpt300lpr-3.0.2-0.i386.deb dcpt300cupswrapper-3.0.2-0.i386.deb /tmp/
RUN dpkg -i --force-all /tmp/dcpt300lpr-3.0.2-0.i386.deb || true \
    && dpkg -i --force-all /tmp/dcpt300cupswrapper-3.0.2-0.i386.deb || true

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 631
ENTRYPOINT ["/entrypoint.sh"]
