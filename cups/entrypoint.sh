#!/bin/bash
set -e

mkdir -p /var/run/dbus
dbus-daemon --system --fork

avahi-daemon --daemonize --no-drop-root

# Listen on all interfaces, not just localhost
sed -i 's/Listen localhost:631/Listen *:631/' /etc/cups/cupsd.conf

# Allow unauthenticated access to printer queues from local network
cat >> /etc/cups/cupsd.conf << 'EOF'

<Location /printers>
  AuthType None
  Order allow,deny
  Allow @LOCAL
</Location>
EOF

cupsd

sleep 3

cupsctl --remote-admin --remote-any --share-printers

if ! lpstat -p DCPT300 >/dev/null 2>&1; then
    URI=$(lpinfo -v | grep -i "usb.*brother" | awk '{print $2}')
    if [ -n "$URI" ]; then
        lpadmin -p DCPT300 -E -v "$URI" -P /usr/share/cups/model/Brother/brother_dcpt300_printer_en.ppd
        lpadmin -d DCPT300
        cupsenable DCPT300
        cupsaccept DCPT300
        echo "Impresora DCPT300 agregada."
    else
        echo "No se detectó la impresora Brother por USB todavía."
    fi
fi

tail -f /var/log/cups/error_log
