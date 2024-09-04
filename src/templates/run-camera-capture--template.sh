#!/bin/bash

token='$token'
fingerprint='$fingerprint'
rotation=$rotation
temp_dir='/tmp/prusa-connect-camera'
temp_cam_snapshot_filename='cam_snapshot.jpg'
curl_log_filename='curl.log'
ffmpeg_log_filename='ffmpeg.log'
rpicam_log_filename='rpicam.log'
temp_cam_snapshot_filepath="$$temp_dir/$$temp_cam_snapshot_filename"
curl_log_filepath="$$temp_dir/$$curl_log_filename"
ffmpeg_log_filepath="$$temp_dir/$$ffmpeg_log_filename"
rpicam_log_filepath="$$temp_dir/$$rpicam_log_filename"

if [ ! -d "$$temp_dir" ]; then
    echo "Creating a directory '$$temp_dir' to mount virtual memory (ramfs) into it..."
    mkdir -p $$temp_dir
else
    echo "Temp '$$temp_dir' directory exist, no need to create."
fi

if mountpoint -q "$$temp_dir" ; then
    echo "Temp directory '$$temp_dir' already mounted"
else
    echo "Mounting virtual memory (ramfs) into directory '$$temp_dir'..."
    mount -t ramfs -o size=20m ramfs $$temp_dir
fi

errored="false"
errored_ffmpeg="false"

while true; do
    rpicam-still -v 0 --immediate --width 2274 --height 1280 -q 80 -o $$temp_cam_snapshot_filepath &> $$rpicam_log_filepath
    if [ $$? -eq 0 ]; then
        if [ $$rotation != "0" ]; then
            ffmpeg -y -i $$temp_cam_snapshot_filepath -vf "rotate=$$rotation*PI/180" -update true $$temp_cam_snapshot_filepath &> $$ffmpeg_log_filepath
        fi
        if [ $$? != 0 ]; then
            if [ $$errored_ffmpeg == "false" ]; then
                errored_ffmpeg="true"
                echo "ffmpeg returned an error, image might not be correctly rotated. Please consult logs at path: '$$ffmpeg_log_filepath'"
            fi
        else
            errored_ffmpeg="false"
        fi

        curl -X PUT "https://connect.prusa3d.com/c/snapshot" \
          -H "accept: */*" \
          -H "content-type: image/jpg" \
          -H "fingerprint: $$fingerprint" \
          -H "token: $$token" \
          --data-binary "@$$temp_cam_snapshot_filepath" \
          --no-progress-meter \
          -v \
          --fail-with-body \
          --compressed &> $$curl_log_filepath

        if [ $$? -eq 0 ]; then
            errored="false"
            sleep 10
            continue
        fi
    fi

    logfiles="$$rpicam_log_filepath, $$curl_log_filepath"
    if [ $$rotation != "0" ]; then
        logfiles="$$ffmpeg_log_filepath, $$logfiles"
    fi
    if [ $$errored == "false" ]; then
        errored="true"
        echo "rpicam-still returned an error, retrying after 60s... You might want to check log files: '$$logfiles'. You might want to search for a solution on GitHub https://github.com/koprivajakub/prusa-rpicam-py-connect/issues (feel free to create an Issue if you aren't able to find the answer for your problem). Also you might want to check comments at https://www.printables.com/en/model/989624 and seek help there."
    fi
    sleep 60
done
