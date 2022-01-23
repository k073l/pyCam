# pyCam
Use a IP Webcam as webcam in MS Teams, Discord, etc. **Added bonus - it might look bad on purpose.**

### Usage

#### IP Webcam
Run `main.py`, tweak the `options.yml` file.

```yml
mac: ff:ff:ff:ff:ff:ff # enter your ip webcam's mac address or...
ip: 127.0.0.1 # enter your ip webcam's ip address (use one or the other)
# MAC address is recommended if you're using DHCP
user: user # username you set in your webcam's settings
pass: password # password you set in your webcam's settings
port: 8080 # port on which your webcam is running
framedrop_chance: 30 # chance as percent to drop frame when using "BadWebcam"

```

Run `main.py` again, select IP Webcam from dropdown menu and select which webcam you want to use:

 - GoodWebcam - just a webcam, maximum quality
 - BadWebcam - intentionally garbage

#### In-build webcam/USB
Run `main.py`, from the options file you might want to change the `framedrop_chance` only (see above for details).

Run `main.py` again, select your webcam from the dropdown (if you only have 1, it's likely 0).
Then select BadWebcam to get the hideous output you were looking for (since you have a normal webcam, the `GoodWebcam` seems functionality unnecessary for you).

### Requirements
`pip install -r requirements.txt`

[IP Webcam](https://play.google.com/store/apps/details?id=com.pas.webcam) the script has been tested for. Others will likely work as well.

You will also need a [virtual camera](https://github.com/letmaik/pyvirtualcam#supported-virtual-cameras) in order for script to work.
It's really just an over-engineered `pyvirtualcam` wrapper.
#### Useful notice
OBS virtual camera seems to not like changing it. Select it first, then run the script to make it work and use it.

Also it likely doesn't work on ARM (`pyvirtualcam` has no support for it (I think)).