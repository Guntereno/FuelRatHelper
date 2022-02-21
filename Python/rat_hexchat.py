__module_name__ = "fuelrat_helper_hexchat"
__module_version__ = "1.1"
__module_description__ = "Fuel Rat Helper"


import hexchat
import os
import sys

root_path = os.path.join(hexchat.get_info('configdir'), 'addons')

# The script folder isn't necessarily in the search path when running through HexChat
# So we need to add it to include our own modules below.
sys.path.append(os.path.join(root_path, 'rat_lib'))

import rat_irc

def init():
    rat_irc.init(root_path, on_console_write)

    hexchat.hook_server("PRIVMSG", handle_privmsg)
    hexchat.hook_command(
        "FR_LOG",
        lambda word, word_eol, userdata : rat_irc.handle_fr_log(word),
        help=rat_irc.fr_log_usage)
    hexchat.hook_command(
        "FR_CLIP",
        lambda word, word_eol, userdata : rat_irc.handle_fr_clip(word),
        help=rat_irc.fr_clip_usage)
    hexchat.hook_command(
        "FR_PLATFORM",
        lambda word, word_eol, userdata : rat_irc.handle_fr_platform(word),
        help=rat_irc.fr_platform_usage)
    hexchat.hook_command(
        "FR_SOUND",
        lambda word, word_eol, userdata : rat_irc.handle_fr_sound(word),
        help=rat_irc.fr_sound_usage)
    hexchat.hook_command(
        "FR_GAME_VERSION",
        lambda word, word_eol, userdata : rat_irc.handle_fr_game_version(word),
        help=rat_irc.fr_game_version_usage)

def on_console_write(line):
    hexchat.prnt(line)

def handle_privmsg(word, word_eol, userdata):
    sender = word[0]
    recipient = word[2]
    message = word_eol[3]
    rat_irc.handle_message(sender, recipient, message)
    return hexchat.EAT_NONE

init()