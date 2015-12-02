========
Usage
========

Run `archive-rotator -h` for documentation of command-line parameters:
::

    usage: archive-rotator [-h] [-n NUM_ROTATION_SLOTS] [-v] [--ext EXT]
                       [--ignore-missing] [--simple] [--hanoi] [--tiered]
                       path

    Move a file into a rotation of backup archives.

    positional arguments:
      path                  Path of input file to rotate

    optional arguments:
      -h, --help            show this help message and exit
      -n NUM_ROTATION_SLOTS, --num NUM_ROTATION_SLOTS
                            Max number of files in the rotation
      -v, --verbose         Print info messages to stdout
      --ext EXT             Look for and preserve the named file extension
      --ignore-missing      If the input file is missing, log and exit normally
                            rather than exiting with an error
      --simple              Use the first-in-first-out rotation pattern (default)
      --hanoi               Use the Tower of Hanoi rotation pattern
      --tiered              Use the tiered rotation pattern
