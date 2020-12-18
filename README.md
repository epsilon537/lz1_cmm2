LZ1 LZ77 encoder/decoder 
------------------------
Authors
-------
Original C implementation by Rich Geldreich. 
MMBasic and Python ports by Epsilon.

Current Version
---------------
0.1

ChangeLog
---------
0.1: Initial version.

Description
-----------
lz1 performs LZ77 compression/decompression of a given input file.
Two compatible versions exist: lz1.bas for CMM2 and lz1.py for a Windows/MacOSX/Linux host.

The source code for the original C implementation can be found here:

https://gist.github.com/fogus/5401265

Usage
-----
CMM2:
*lz1 e <file> : encodes <file> into <file>.lz1
*lz1 d <file>.lz1 : decodes <file>.lz1 to <file>

Host:
python lz1 e <file> : encodes <file> into <file>.lz1
python lz1 d <file>.lz1 : decodes <file>.lz1 to <file>

Required CMM2 firmware version
------------------------------
V5.06.00

Required Python version
-----------------------
3.x

GitHub
------
https://github.com/epsilon537/lz1_cmm2