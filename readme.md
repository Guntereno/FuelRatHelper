# Fuel Rat Helper

## HexChat Plugin

This plugin listens for ratsignals from MechaSqueak, parsing the data accordingly and
copying the system name to the clipboard. (As far as I know, this will only work on
Windows.)

The script can be configured to only trigger alerts for cases on a given platform and game
version (Horizons or Odyssey). It is possible to configure the format of the case data to be
copied to the clipboard.

### Installation

Copy the files 'rat_lib.py', 'fuelrat_hexchat.py' and 'rat_client.py into the HexChat addons folder.
(%AppData%\HexChat\addons)

### Usage

The system should be copied to the clipboard automatically whenever MechaSqeak fires
up the ratsignal. There are a couple of commands which control the behaviour of the
plugin:

```/fr_log <'true'/'false'>```: Enable or disable FuelRat helper logging.

```/fr_clip <'format'>```: Specify format of clipped string (none to disable)\nc=casenum, s=systemname, n=clientname

```/fr_platform <'ALL'/'PC'/'XB'/'PS4'>```: Set platform for alerts."

```/fr_sound <path>```: Set the file to use as an alert tone."

```/fr_game_version <'ALL'/'HORIZONS'/'ODYSSEY'>```: Set which version in which cases should trigger alerts."

#### Logging

Logging can be enabled if you want to keep records of all the lines sent by MechaSqueak. The lines will be appended
to a file at '%USERPROFILE%\AppData\Local\Temp\ratirc.log'.

#### Clipboard Formats

The ```/fr_clip``` command is used to specify the format in which the case data is copied to the system clipboard.
At present, the case number, system name, and client name can be included. The elements will be separated by a '|'
character.

For example, if the format is 's' output will only include the system name. (e.g., 'Sol'). More information may be
required by a third-party tool such as a custom VoiceAttack command. In this case, the format may combine the data.
The format 'nsc' will output the case number, system name, and client name. (e.g., '2|Sol|Guntereno'.)