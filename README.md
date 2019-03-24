# Introducion

This is a Telegram bot capable of processing audio and text inputs to request a simple REST API 
and determine matches between entries and trending topics on Twitter. 
In addition, the bot also queries national and regional trends based on location.

To process an audio it is necessary to contain the word Twitter at the beginning. 
To have a text processed you need to use the /twitter command. 
To find out the tendencies of Brazil type /tts or send your location to determine your regional trends

# Installing

You can install sdpos using::

    $ pip3 install -r requirements.txt

# Dependencies

* This project uses version 3 of Python.
* To use it is necessary to create a key Google-Cloud-Speech, Google Maps and the key of the application of the robot.
* The requisitions are directed to another part of the project [IN0984](https://github.com/gppeixoto/in0984).
