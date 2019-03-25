# Introducion

This is a Telegram bot capable of processing audio and text inputs to request a simple REST API 
and determine matches between entries and trending topics on Twitter. 

To process an audio it is necessary to contain the word Twitter at the beginning. 
To have a text processed you need to use the /twitter command. 
To find out the tendencies of Brazil type /tts or send your location to determine your regional trends

# Installing

You can install sdpos using::

    $ pip3 install -r requirements.txt
    $ Insert the keys into env.sh
    $ Load the system variables using: source ./env.sh
    $ python3 trends_bot.py
    
Video with TrendsBot installation guide available on Youtube::
    $ https://youtu.be/jEgaV5YqABk
    
# How to use this software?
Video with TrendsBot usage guide available on Youtube::
    $ https://youtu.be/HYEYfvtTbzQ

# Dependencies

* This project uses version 3 of Python.
* To use it is necessary to create a key Google-Cloud-Speech and the key of the application of the robot Telegram.
* The requisitions are directed to another part of the project [TrendsBotGoLang](https://github.com/wellisonraul/TrendsBotGoLang).
