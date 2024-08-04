# This is a sample Python script.
import os
import pathlib
import shutil
import uuid
from string import Template


# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

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
            'Where on the image is the edge/side that should be normally on the bottom?\n [Left / Right / Up / Down] > ')
        if answer.lower() in ["l", "left"]:
            return 270  # -90
        elif answer.lower() in ["r", "right"]:
            return 90
        elif answer.lower() in ["u", "up"]:
            return 180
        elif answer.lower() in ["d", "down"]:
            return 180
        else:
            print("Please respond with 'l'/'left' or 'r'/'right' or 'u'/'up'/ or 'd'/'down'")


def send_image(rotation: int) -> None:
    print("Image sent")


def create_autorun_script(api_key: str, camera_fingerprint: str, camera_rotation: int) -> str:
    template_values = {
        'rotation': camera_rotation,
        'fingerprint': camera_fingerprint,
        'prusa_api_key': api_key
    }

    with open('run-camera-capture--template.sh', 'r') as template_file:
        template = Template(template_file.read())
        file_content_result = template.substitute(template_values)
        script_file = open("run-camera-capture.sh", "w")
        script_file.write(file_content_result)
        script_file.close()
    template_file.close()

    return os.path.realpath(script_file.name)


def check_camera_orientation(rotation: int) -> int:
    while not ask_confirmation("Is the image orientation as expected? Bottom side is on the bottom?"):
        rotation = ask_orientation()
        send_image(rotation)
    return rotation


if __name__ == '__main__':
    token = input('Please insert your "Prusa Connect API Key" \n > ')
    fingerprint = uuid.uuid4().hex
    cam_rotation = 0

    print("I will try to create the connection now by capturing an image from the RPi camera and send it to the Prusa "
          "Connect. Make sure the printer is turned on and ONLINE in the Prusa Connect.")
    if ask_confirmation("Are you ready to test the connection?"):
        try:
            send_image(cam_rotation)
            if ask_confirmation("Is the image visible in Prusa Connect? (If the image is incorrectly rotated, "
                                "don't worry we will fix that later)"):
                print("Congratulations. The connection works as expected.")
                cam_rotation = check_camera_orientation(cam_rotation)
                autorun_script_path = create_autorun_script(token, fingerprint, cam_rotation)

                if ask_confirmation(
                        "Image is correctly rotated and we are ready to create autorun script. This script will be "
                        "registered to run on start of the RPi OS and will capture image every 10 seconds that will "
                        "be sent to the Prusa Connect. Do you want to continue?"
                ):
                    print("Creating autorun script...")
                    shell_final_path = "/usr/local/bin/prusa-connect-camera.sh"
                    shutil.copy(autorun_script_path, shell_final_path)
                    service_file_name = 'prusa-connect-camera.service'
                    with open('prusa-connect-camera--template.service', 'r') as service_template_file:
                        service_template = Template(service_template_file.read())
                        service_file_content = service_template.substitute({'shell_script_path': shell_final_path})
                        service_file = open(service_file_name, "w")
                        service_file.write(service_file_content)
                        service_file.close()

                    service_template_file.close()
                    service_file_src_path = os.path.realpath(service_file.name)
                    service_file_dst_path = f'/etc/systemd/system/{service_file_name}';
                    shutil.copy(service_file_src_path, service_file_dst_path)

                    print("Starting the service daemon...")
                    exec(f'sudo systemctl start {service_file_name}')
                    exec(f'sudo systemctl enable {service_file_name}')
                else:
                    print(
                        "There is nothing much I can help with here as my main purpose is to install the script "
                        "mentioned in the question above. Please re-run the installer if you change your mind.\n\n"
                        "I have created a shell script that you can run on your own. The script will capture a "
                        "snapshot image from the camera and send to the Prusa Connect. You can find it in: "
                        f"{autorun_script_path}")
                    exit(0)
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
        exit(0)
