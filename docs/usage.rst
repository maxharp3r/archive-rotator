=====
Usage
=====

Command Line
------------

Say we wish to rotate `/files/website-backup.zip` daily.
Let's use the tower of hanoi algorithm, to balance recency and longevity.
We do this::

    archive-rotator -v --hanoi -n 8 --ext ".zip" /files/website-backup.zip


For documentation of command-line parameters, run `archive-rotator -h`::

    usage: archive-rotator [-h] [-n NUM_ROTATION_SLOTS] [-v] [--ext EXT]
                           [-d DESTINATION_DIR] [--ignore-missing] [--simple]
                           [--hanoi] [--tiered]
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
      -d DESTINATION_DIR, --destination-dir DESTINATION_DIR
                            Put the rotated archive in this directory.Use if the
                            rotated archives live in a different directory from
                            the source file.
      --ignore-missing      If the input file is missing, log and exit normally
                            rather than exiting with an error
      --simple              Use the first-in-first-out rotation pattern (default)
      --hanoi               Use the Tower of Hanoi rotation pattern
      --tiered              Use the tiered rotation pattern


Programmatic
------------

You can rotate files from python. Example::

    from archive_rotator import rotator
    from archive_rotator.algorithms import SimpleRotator

    rotator.rotate(SimpleRotator(5), "/my/path/foo.tar.gz", ".tar.gz", verbose=True)

