import pyvirtualcam
import numpy as np
import cv2
from tkinter import Tk, Label, Button, Toplevel, StringVar, OptionMenu
from yaml import load, dump, FullLoader
import random
import threading
from PIL import Image, ImageTk
import os

root = Tk()

# Load settings
try:
    with open('options.yml') as f:
        options = load(f, Loader=FullLoader)

except FileNotFoundError:
    with open('options.yml', 'w') as f:
        dump({
            'mac': "",
            'ip': "",
            'user': "",
            'pass': "",
            'port': 0000,
            'framedrop_chance': 0,
        }, f, sort_keys=False)

    raise SystemExit("options.yml created")


class ImageManipulation:
    @staticmethod
    def gamma_function(channel, gamma):
        inv_gamma = 1 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255
                          for i in np.arange(0, 256)]).astype("uint8")
        channel = cv2.LUT(channel, table)
        return channel

    @staticmethod
    def kernel_correction(img):
        sharpenKernel = np.array(([[0, -1, 0], [-1, 9, -1], [0, -1, 0]]), np.float32) / 10
        meanBlurKernel = np.ones((3, 3), np.float32) / 9

        img[:, :, 0] = ImageManipulation.gamma_function(img[:, :, 0], 1.25)
        img[:, :, 2] = ImageManipulation.gamma_function(img[:, :, 2], 0.75)
        out = cv2.filter2D(src=cv2.filter2D(src=img, kernel=meanBlurKernel, ddepth=-1), kernel=sharpenKernel, ddepth=-1)
        return out

    @staticmethod
    def saturation_and_brightness(img, saturation: float = None, brightness: float = None):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        if saturation:
            hsv[..., 1] = hsv[..., 1] * saturation
        if brightness:
            hsv[..., 2] = hsv[..., 2] * brightness
        hsv[:, :, 1] = ImageManipulation.gamma_function(hsv[:, :, 1], 0.8)
        out = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        return out

    @staticmethod
    def jpeg_compression(img, quality: int = 40):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        im_pil = Image.fromarray(img)
        im_pil.save('tmp.jpg', quality=quality)
        pil_image = Image.open('tmp.jpg').convert('RGB')
        out = np.array(pil_image)
        out = out[:, :, ::-1].copy()  # Convert RGB to BGR
        os.remove('tmp.jpg')
        return out

    @staticmethod
    def bad_quality(img):
        out = ImageManipulation.saturation_and_brightness(img, 0.8, 0.6)
        out = ImageManipulation.kernel_correction(out)
        out = ImageManipulation.jpeg_compression(out, 40)
        return out


class Cameras:
    def __init__(self):
        if options["ip"]:
            # There is IP in settings, so just proceed with that
            self.ip = options["ip"]
        elif options["mac"]:
            # No IP in settings, but there's MAC, so find it that way
            import subprocess
            mac_cmd = options["mac"].replace(":", "-")
            if os.name == 'nt':
                cmd = f'arp -a | findstr "{mac_cmd}" '
            else:
                cmd = f'arp -a | grep "{mac_cmd}" '
            returned_output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            parse = str(returned_output).split(' ', 1)
            ip = parse[1].split(' ')
            self.ip = ip[1]
        else:
            # Neither IP nor MAC is present, so assume no IP Webcam
            self.ip = None

    @staticmethod
    def list_cameras():
        index = 0
        camera_list = []
        while True:
            cap = cv2.VideoCapture(index)
            if not cap.read()[0]:
                break
            else:
                camera_list.append(index)
            cap.release()
            index += 1
        return camera_list

    def initialize_videocapture(self, choice):
        if self.ip and (choice == "IP Webcam"):
            self._capture = cv2.VideoCapture(f"http://{options['user']}:{options['pass']}"
                                             f"@{self.ip}:{options['port']}/video")
        else:
            self._capture = cv2.VideoCapture(int(choice))
        # Get Capture's parameters
        self.width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self._capture.get(cv2.CAP_PROP_FPS))
        self.fmt = pyvirtualcam.PixelFormat.BGR

    def bad_webcam(self):
        terminate = False

        new_window = Toplevel(root)
        Label(new_window, text="Running bad webcam...").pack()
        Label(new_window, text="Click to terminate").pack()
        Button(new_window, text='Terminate', command=exit).pack()

        with pyvirtualcam.Camera(self.width, self.height, fps=15, fmt=self.fmt) as cam:
            print(f'Using virtual camera: {cam.device}')
            frame = np.zeros((cam.height, cam.width, 3), np.uint8)  # RGB
            preview_window = Toplevel(root)
            preview_window.title("Preview (Bad Webcam)")
            cont = Label(preview_window)
            cont.grid(row=0, column=0)
            while True:
                if terminate:
                    self._capture.release()
                    cv2.destroyAllWindows()
                    break
                try:
                    ret, frame = self._capture.read()
                    # Vertical flip
                    frame = cv2.flip(frame, 0)
                    if options['framedrop_chance'] or options['framedrop_chance'] != 0:
                        if random.randint(1, 100) >= options['framedrop_chance']:
                            # This will NOT execute x% of the time

                            bad_quality_frame = ImageManipulation.bad_quality(img=frame)
                            cam.send(bad_quality_frame)

                            # Update preview window
                            cv2image = cv2.cvtColor(bad_quality_frame, cv2.COLOR_BGR2RGBA)
                            img = Image.fromarray(cv2image)
                            imgtk = ImageTk.PhotoImage(image=img)
                            cont.imgtk = imgtk
                            cont.configure(image=imgtk)
                    cam.sleep_until_next_frame()
                except KeyboardInterrupt:
                    raise SystemExit

    def good_webcam(self):
        terminate = False

        new_window = Toplevel(root)
        Label(new_window, text="Running good webcam...").pack()
        Label(new_window, text="Click to terminate").pack()
        Button(new_window, text='Terminate', command=exit).pack()

        with pyvirtualcam.Camera(self.width, self.height, self.fps, fmt=self.fmt) as cam:
            print(f'Using virtual camera: {cam.device}')
            frame = np.zeros((cam.height, cam.width, 3), np.uint8)  # RGB
            preview_window = Toplevel(root)
            preview_window.title("Preview (Good Webcam)")
            cont = Label(preview_window)
            cont.grid(row=0, column=0)
            while True:
                if terminate:
                    self._capture.release()
                    cv2.destroyAllWindows()
                    break
                try:
                    ret, frame = self._capture.read()
                    # Vertical flip
                    frame = cv2.flip(frame, 0)
                    cam.send(frame)

                    # Update preview window
                    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                    img = Image.fromarray(cv2image)
                    imgtk = ImageTk.PhotoImage(image=img)
                    cont.imgtk = imgtk
                    cont.configure(image=imgtk)

                    cam.sleep_until_next_frame()
                except KeyboardInterrupt:
                    raise SystemExit


cams = Cameras()


def main():
    Label(root, text='What cam to use').pack(padx=10, pady=10)

    # Load cameras
    cameras = Cameras.list_cameras()
    default = StringVar(root)
    default.set(cameras[0])
    cameras.append("IP Webcam")
    OptionMenu(root, default, *cameras).pack(padx=10, pady=10)

    def bad_webcam_runner():
        choice = default.get()
        cams.initialize_videocapture(choice)
        thread = threading.Thread(target=cams.bad_webcam, daemon=True)
        thread.start()

    def good_webcam_runner():
        choice = default.get()
        cams.initialize_videocapture(choice)
        thread = threading.Thread(target=cams.good_webcam, daemon=True)
        thread.start()

    Label(root, text='Pick what webcam to initialize').pack(padx=10, pady=10)

    Button(root, text='bad webcam', command=bad_webcam_runner).pack(side='right', padx=10, pady=10)
    Button(root, text='good webcam', command=good_webcam_runner).pack(side='right', padx=10, pady=10)

    root.mainloop()


if __name__ == '__main__':
    main()
