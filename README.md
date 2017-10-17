# SpellmanUSB

A python library for controlling a Spellman high voltage power supply with Python over USB using 'cython-hidapi' (https://github.com/gbishop/cython-hidapi), a cython wrapper for the hidapi c-library.  

This library has been tested with a Spellman uX series power supply (https://www.spellmanhv.com/en/Products/uX).  The spellman communicates using a human interface device (HID) USB protocol.  Using the hidapi library makes communications straightforward, and the only task that remains is programming the various commands with their command numbers, and taking care of the checksum.  These were done using the spellman manual.
(last checked downloadable 10/16/17:https://www.spellmanhv.com/-/media/en/Technical-Resources/Manuals/uXMAN.pdf)

This may be compatible with Spellman series other than the uX (like the uXHP for example), that rely on the same communications board, but they have not been tested.  The only modifications needed in that case would be the scalefactors set in the configuration dictionaries (see __init__.py).

Some user specific scripts have been written for our application in the userscripts.py file, while the main code in __init__.py has been kept generalized.
