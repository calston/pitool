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

This will be made better eventually.

## Pics or it didn't happen

### Dashboard
![screen2](https://i.imgur.com/sMpmqob.png)

### Analyzer
![screen1](https://i.imgur.com/i4LVGks.png)
