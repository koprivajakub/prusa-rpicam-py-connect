from sys import exit
import os
import pathlib
import re
import shutil
import subprocess
import sys
import json
import uuid
from string import Template


def print_success() -> None:
    print('')
    print('')
    print('                                             @@@@@@@@@@@@@@@                                        ')
    print('                                       @@@@@@@@@@      @@@@@@@@@                                    ')
    print('                                   @@@@@@@@@@@@@ @@  @@@@@@@@@@@@@@                                 ')
    print('                                @@@@@@@@@@            @@@  @    @@@@@                               ')
    print('                              @@@                               @@ @@@@                             ')
    print('                             @     @@@@@@@@@@@@@@@@@@@@@@@@@@@      @@@@@                           ')
    print('                            @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@     @@@@                         ')
    print('                          @@@@@@@@@@@@@               @@@@@@@@@@@@@@@@    @@                        ')
    print('                          @@@@@@@@@@                          @@@@@@@@@@@   @@                      ')
    print('                          @@@@@@@@@                              @@@@@@@@@@  @@                     ')
    print('                          @@@@@@@@@                                 @@@@@@@@@ @                     ')
    print('                          @@@@@@@@                                    @@@@@@@@ @                    ')
    print('                           @@@@@@@@                                     @@@@@@@@                    ')
    print('                           @@@@@@@@                                      @@@@@@@@                   ')
    print('                            @@@@@                                        @@@@@@@@                   ')
    print('                           @@@@@ @@@@@                                  @@ @@@@@                    ')
    print('                           @@@@@@@      @@@@@                           @@ @@@@                     ')
    print('                           @@  @@             @@                        @@  @@                      ')
    print('                           @@  @       @@       @@@@@@@   @@@@@@@@@@@   @ @@@                       ')
    print('                           @@  @       @@@@ @   @  @@              @@@@@@@@@                        ')
    print('                           @   @               @    @               @@   @                          ')
    print('                          @@    @            @@     @     @         @   @@                          ')
    print('                          @@      @@       @@       @@             @    @@                          ')
    print('                          @@         @@@@@           @@           @     @                           ')
    print('                          @                            @@@      @@      @                           ')
    print('                          @@                               @@@@        @@                           ')
    print('                          @@              @@@                          @                            ')
    print('                          @@                                          @                             ')
    print('                           @         @@                              @@                             ')
    print('                           @      @@@@@@                             @@                             ')
    print('                           @@      @@@@@@@@@@@@        @@@          @@                              ')
    print('                            @@                @@@@@@@@@@@@@         @@                              ')
    print('                            @@@                                    @@                               ')
    print('                            @@@@                                  @@                                ')
    print('                            @@@@@                              @@@@                                 ')
    print('                             @@@@@@                          @@@@@                                  ')
    print('                              @@@@@@@                      @@@@@                                    ')
    print('                               @@@@@@@@@@              @@@@@@@@                                     ')
    print('                                @@@@@@@@@@@@@@@@@@@@@@@@@@@@                                        ')
    print('                                  @@@@@@@@@@@@@@@@@@@@@@@@                                          ')
    print('                                   @@@@@@@@@@@@@@@@@@@@                                             ')
    print('                                     @@@@@@@@@@@@@@@                                                ')
    print('                                         @@@@@@@@                                                   ')
    print('                                                                                                    ')
    print('                                                                                                    ')
    print('Happy Printing')


def ask_confirmation(question: str):
    while True:
        answer = input(question + '\n [y/n] > ')
        if answer.lower() in ["y", "yes"]:
            return True
        elif answer.lower() in ["n", "no"]:
            return False
        else:
            print("Please respond with 'y'/'yes' or 'n'/'no'")


def ask_orientation() -> int:
    while True:
        answer = input(
            'Where on the image (The first image you seen, not the most recent) is the edge/side that should be '
            'normally on the bottom?\n [Left / Right / Up / Down] > ')
        if answer.lower() in ["l", "left"]:
            return 270  # -90
        elif answer.lower() in ["r", "right"]:
            return 90
        elif answer.lower() in ["u", "up"]:
            return 180
        elif answer.lower() in ["d", "down"]:
            return 0
        else:
            print("Please respond with 'l'/'left' or 'r'/'right' or 'u'/'up'/ or 'd'/'down'")


def send_image(cam_rotation: int, cam_fingerprint: str, cam_token: str) -> None:
    # Make sure the output is hidden as that does not work well add some verbose option to show it
    subprocess.run(["rpicam-still", "-v", "0", "--immediate", "--width", "2274", "--height", "1280", "-q", "80", "-o",
                    "cam_snapshot.jpg"], capture_output=True)
    # Validate the image has been created if not there is an issue with the rpicam-still and we should print the
    # error output
    if cam_rotation != 0:
        subprocess.run(
            ["ffmpeg", "-y", "-i", "cam_snapshot.jpg", "-vf", f'rotate={cam_rotation}*PI/180', "cam_snapshot.jpg"],
            capture_output=True)

    curl_send_image_output = subprocess.run(['curl', '-X', 'PUT', 'https://connect.prusa3d.com/c/snapshot',
                                             '-H', 'accept: */*',
                                             '-H', 'content-type: image/jpg',
                                             '-H', f'fingerprint: {cam_fingerprint}',
                                             '-H', f'token: {cam_token}',
                                             '--data-binary', '@cam_snapshot.jpg',
                                             '--no-progress-meter',
                                             '--compressed'], capture_output=True)
    if curl_send_image_output.returncode != 0:
        print("")
        print(f'{curl_send_image_output.stdout.decode(sys.getfilesystemencoding())}')
        print(f'{curl_send_image_output.stderr.decode(sys.getfilesystemencoding())}')
        print("")
        print("Image wasn't sent, check the error above.")
        exit(512)
    raw_response = curl_send_image_output.stdout.decode(sys.getfilesystemencoding())
    data = json.loads(raw_response)
    if 'status_code' in data:
        status_code = data['status_code']
        if 200 <= status_code < 300:
            print("Image sent successfully...")
            return
    else:
        print(data)
        print('')
        print('There was an error sending the image. See details above.')


def create_autorun_script(camera_token: str, camera_fingerprint: str, camera_rotation: int) -> str:
    template_values = {
        'rotation': camera_rotation,
        'fingerprint': camera_fingerprint,
        'token': camera_token
    }

    with open(get_filepath('run-camera-capture--template.sh'), 'r') as template_file:
        template = Template(template_file.read())
        file_content_result = template.substitute(template_values)
        if camera_rotation == 0:
            file_content_result = re.sub(r'^(.*ffmpeg.*)$', r'#\1', file_content_result)

        script_file = open("run-camera-capture.sh", "w")
        script_file.write(file_content_result)
        script_file.close()
    template_file.close()

    return os.path.realpath(script_file.name)


def check_camera_orientation(rotate: int, cam_fingerprint: str, cam_token: str) -> int:
    ffmpeg_installed = None
    while not ask_confirmation("Is the image orientation as expected? Bottom side is on the bottom?"):
        if ffmpeg_installed is None:
            ffmpeg_installed = validate_ffmpeg()
        if not ffmpeg_installed:
            return 0
        rotate = ask_orientation()
        send_image(rotate, cam_fingerprint, cam_token)
    return rotate


def validate_ffmpeg() -> bool:
    try:
        ffmpeg_output = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    except Exception:
        print("ffmpeg library is not installed. Software rotation of images won't be supported. Please rotate your "
              "camera in a correct direction manually by rotating the hardware.")
        if ask_confirmation("Or you you can install the ffmpeg library? Do you want to continue and install it now?"):
            ffmpeg_install_output = subprocess.run(['sudo', 'apt', 'install', '-y', 'ffmpeg'], capture_output=False)
            if ffmpeg_install_output.returncode == 0:
                print("ffmpeg library is installed correctly.")
                return True
            else:
                print("ffmpeg library is not installed. Try to install it manually by running `sudo apt install -y"
                      "ffmpeg`")
                exit(501)
        else:
            if not ask_confirmation(
                    "You can also install ffmpeg by running this command in your terminal: `sudo apt install -y "
                    "ffmpeg` if you still prefer to rotate your image via software option. Do you want to continue "
                    "without the camera rotation."):
                exit(510)
        return False
    return True


def validate_camera_installed() -> bool:
    try:
        rpicam_version_output = subprocess.run(["rpicam-still", "--version"], capture_output=True)
    except Exception:
        if ask_confirmation("Camera libraries for Raspberry is not installed. Do you want to install it now?"):
            rpicam_install_output = subprocess.run(['sudo', 'apt', 'install', '-y', 'rpicam-apps'],
                                                   capture_output=False)
            if rpicam_install_output.returncode == 0:
                print("rpicam-apps library is installed correctly.")
                return True
            else:
                print("rpicam-apps library is not installed. Try to install it manually by running `sudo apt install -y"
                      "rpicam-apps`")
                exit(502)
        print("rpicam-still program from rpicam-apps library is required. Try to install it manually by running `sudo "
              "apt install rpicam-apps -y`")
        exit(503)
    return True


def validate_camera() -> bool:
    validate_camera_installed()
    if ask_confirmation("Let's validate the camera works. Camera feed will be visible on a screen in new window for "
                        "3s. Are you ready to continue?"):
        rpicam_hello_output = subprocess.run(["rpicam-hello", "--timeout", "3000"], capture_output=True)
        if rpicam_hello_output.returncode != 0:
            print("")
            print(f'{rpicam_hello_output.stdout.decode(sys.getfilesystemencoding())}')
            print(f'{rpicam_hello_output.stderr.decode(sys.getfilesystemencoding())}')
            print("")
            print(
                "Cannot connect and show the camera image feed. Please make sure the camera hardware is connected. Try "
                "to restart the board and re-run the script please. The error details are printed above.")
            exit(511)
        else:
            if ask_confirmation("Have you seen the camera feed in the window that has been open for 3s?"):
                return True
            else:
                print("This is unexpected. Please validate the camera hardware is still connected, try to reboot the "
                      "Raspberry Pi and re-run the script.")
                exit(504)
    else:
        print("This step is required. Please re-run the script once ready.")
        exit(505)


def validate_curl() -> bool:
    try:
        curl_version_output = subprocess.run(["curl", "--version"], capture_output=True)
    except Exception:
        if ask_confirmation("Required library `curl` not found. Do you want to continue and install it now?"):
            curl_install_output = subprocess.run(['sudo', 'apt', 'install', '-y', 'curl'], capture_output=False)
            if curl_install_output.returncode == 0:
                print("curl library is installed correctly.")
                return True
            else:
                print("curl library is not installed. Try to install it manually by running `sudo apt install "
                      "curl -y`")
                exit(506)
        print("curl library is required. Try to install it manually by running `sudo apt install curl -y`")
        exit(507)
    return True


def validate_sudo() -> None:
    if os.getuid() != 0:
        print(f"This process needs to be run as root. Please re-run as `sudo {sys.executable} {' '.join(sys.argv)}`")
        exit(510)


def validate_requirements() -> None:
    validate_sudo()
    validate_curl()
    validate_camera()


def get_filepath(name: str) -> pathlib.PurePath:
    return pathlib.Path(__file__).resolve().parent.joinpath("templates").joinpath(name)


if __name__ == '__main__':
    service_file_name = 'prusa-connect-camera.service'
    validate_requirements()
    fingerprint = f'{uuid.uuid3(uuid.NAMESPACE_URL, hex(uuid.getnode()))}'
    rotation = 0
    token = input('Please insert your "Prusa Camera Token" \n > ')

    print("")
    print("Using:")
    print(f" - Camera Fingerprint: '{fingerprint}'")
    print(f" -       Camera Token: '{token}'")
    print("")

    print("I will try to create the connection now by capturing an image from the RPi camera and send it to the Prusa "
          "Connect. Make sure the printer is turned on and ONLINE in the Prusa Connect.")
    if ask_confirmation(
            "Are you ready to test the connection? (Note: This will stop the automatic screenshot service if there is "
            "any already from previous installations.)"):
        try:
            subprocess.run(['sudo', 'systemctl', 'stop', service_file_name])
            send_image(rotation, fingerprint, token)
            if ask_confirmation(
                    "Is the image visible in Prusa Connect (refresh the page please)? If the image is incorrectly "
                    "rotated, don't worry we will fix that later."
            ):
                print("Congratulations. The connection works as expected.")
                rotation = check_camera_orientation(rotation, fingerprint, token)
                autorun_script_path = create_autorun_script(token, fingerprint, rotation)

                if ask_confirmation(
                        "Image is correctly rotated and we are ready to create autorun script. This script will be "
                        "registered to run on start of the RPi OS and will capture image every 10 seconds that will "
                        "be sent to the Prusa Connect. Do you want to continue?"
                ):
                    print("Creating autorun script...")
                    shell_final_path = "/usr/local/bin/prusa-connect-camera.sh"
                    shutil.copy(autorun_script_path, shell_final_path)
                    service_file_name = 'prusa-connect-camera.service'
                    with open(get_filepath('prusa-connect-camera--template.service'), 'r') as service_template_file:
                        service_template = Template(service_template_file.read())
                        service_file_content = service_template.substitute({'shell_script_path': shell_final_path})
                        service_file = open(service_file_name, "w")
                        service_file.write(service_file_content)
                        service_file.close()

                    service_template_file.close()
                    service_file_src_path = os.path.realpath(service_file.name)
                    service_file_dst_path = f'/etc/systemd/system/{service_file_name}'
                    shutil.copy(service_file_src_path, service_file_dst_path)

                    print("Starting the service daemon...")
                    subprocess.run(['sudo', 'chmod', '+x', shell_final_path])
                    subprocess.run(['sudo', 'systemctl', 'daemon-reload'])
                    subprocess.run(['sudo', 'systemctl', 'start', service_file_name])
                    subprocess.run(['sudo', 'systemctl', 'enable', service_file_name])
                    subprocess.run(['sudo', 'systemctl', 'status', service_file_name, '-n', '1'])
                    print('')
                    print('Congratulations. You have finished the setup.')
                    print(
                        'If the service above is marked as Enabled, Active and Running, you should see the image to '
                        'be updated every 10 sec. in the Prusa Connect.')
                    print('')
                    input('Press any key to exit the setup...')
                    print_success()
                else:
                    print(
                        "There is nothing much I can help with here as my main purpose is to install the script "
                        "mentioned in the question above. Please re-run the installer if you change your mind.\n\n"
                        "I have created a shell script that you can run on your own. The script will capture a "
                        "snapshot image from the camera and send to the Prusa Connect. You can find it in: "
                        f"{autorun_script_path}")
                    exit(508)
            else:
                print("This is very unexpected. It might be due to various issues. Please make sure the 'Prusa "
                      "Connect API Key' you provided is correct, the camera is connected to Raspberry Pi. If all is "
                      "correct I do recommend to try create an image capture from the Camera via a Shell command "
                      "`rpicam-still`.")
        except Exception as e:
            print(e)

    else:
        print("Creating a first image capture from the script is essential for the setup. If you change your mind, "
              "please run the script again. Exiting for now...")
        exit(509)
