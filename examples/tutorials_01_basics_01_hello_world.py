# https://github.com/anki/cozmo-python-sdk/blob/master/examples/tutorials/01_basics/01_hello_world.py

import rx


def main(sources):
    rxcozmo = rx.of({"name": "say_text", "value": "Hello World"})
    sinks = {"Cozmo": rxcozmo}
    return sinks
