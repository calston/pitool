# PiTool

PiTool is a web interface for doing GPIO diagnostics stuff on the Raspberry Pi.

## Installation

```
$ git clone https://github.com/calston/pitool.git
$ apt-get install python-virtualenv libyaml-dev
$ virtualenv ve
$ . ./ve/bin/activate
(ve)$ cd pitool
(ve)$ pip install -e .
(ve)$ twistd -n pitool
```

This will be made better eventually. When done head to http://raspberrypi:8081
(you might need to go directly to the IP if your Pi if your network has no 
DHCP hostname resolution)

## Pics or it didn't happen

### Dashboard
![screen2](https://i.imgur.com/sMpmqob.png)

### Analyzer
![screen1](https://i.imgur.com/i4LVGks.png)
