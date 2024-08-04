#!/bin/bash

while true; do
    libcamera-still -v 0 --immediate --width 2274 --height 1280 --rotate $rotation -q 80 -o cam_snapshot.jpg

    if [ $$? -eq 0 ]; then
        curl -X PUT "https://connect.prusa3d.com/c/snapshot" \
            -H "accept: */*" \
            -H "content-type: image/jpg" \
            -H "fingerprint: $fingerprint" \
            -H "token: $prusa_api_key" \
            --data-binary "@cam_snapshot.jpg" \
            --no-progress-meter \
            --compressed

        sleep 10
    else
        echo "libcamera-still returned an error, retrying after 60s..."

        sleep 60
    fi
done