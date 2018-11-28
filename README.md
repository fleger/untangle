# Untangle

untangle is a tool to extract files from DoubleFine LPAK bundle as found
in Day of the Tentacle Remastered.

## Dependencies

This program requires Python 3.7 or higher.

## Usage

List all files contained in the tenta.cle bundle:

    ./untangle.py -l tenta.cle

Extract all files starting with maniac/ from the tenta.cle bundle into
the current directory (stored paths are preserved):

    ./untangle.py -x -F 'maniac/*' tenta.cle

Get help:

    ./untangle.py --help

## Limitations

Support for Full Throttle Remastered format is not implemented.

## Acknowledgments

Algorithm ported from [DoubleFine-Explorer](https://github.com/bgbennyboy/DoubleFine-Explorer).
