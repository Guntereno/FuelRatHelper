# Fuel Rat Helper

Toolkit to assist The Fuel Rats in their mischief.

## HexChat Plugin

This plugin listens for ratsignals (and r@signals) from MechaSqueak, parsing the data
accordingly and copying the system name to the clipboard. (As far as I know this will
only work on Windows.)

### Installation

Copy the files 'rat_lib.py' and 'fuelrat_hexchat.py' into the HexChat addons folder.
(%AppData%\HexChat\addons)

### Usage

The system should be copied to the clipboard automatically whenever MechaSqeak fires
up the ratsignal. There are a couple of commands which control the behaviour of the
plugin:

```/fr_log <'true'/'false'>``` : Enables/disables logging of all MechaSqueak posts to
a temp file.

```/fr_clip <'true'/'false'>```: Enables/disables the copying the system name to the
clipboard when a signal is fired.

