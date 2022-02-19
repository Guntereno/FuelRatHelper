import hexchat
import json
import os
import sys
import threading
import winsound
from tkinter import Tk

# The script folder isn't necessarily in the search path when running through HexChat
# So we need to add it to include our own modules below.
path = os.path.join(hexchat.get_info("configdir"), "addons")
if path not in sys.path:
    sys.path.append(path)

import rat_config
import rat_client
import rat_lib


__module_name__ = "fuelrat_helper_hexchat"
__module_version__ = "1.1"
__module_description__ = "Fuel Rat Helper"

fr_log_usage = " /fr_log <'true'/'false'>: Enable or disable FuelRat helper logging."
fr_clip_usage = " /fr_clip <'format'>: Specify format of clipped string (none to disable)\nc=casenum, s=systemname, n=clientname"
fr_platform_usage = " /fr_platform <'ALL'/'PC'/'XB'/'PS4'>: Set platform for alerts."
fr_sound_usage = " /fr_sound <path>: Set the file to use as an alert tone."
fr_game_version_usage = " /fr_game_version <'ALL'/'HORIZONS'/'ODYSSEY'>: Set which version in which cases should trigger alerts."

config_logging_enabled = 'logging_enabled'
config_clipping_format = 'clipping_format'
config_platform = 'platform'
config_game_version = 'game_version'
config_alert_sound = 'alert_sound'

_separator = "|"


def copy_to_clipboard(line):
    r = Tk()
    r.withdraw()
    r.clipboard_clear()
    r.clipboard_append(line)
    r.update()
    r.destroy()


def play_alert():
    alert_sound = rat_config.get(config_alert_sound)
    if alert_sound:
        winsound.PlaySound(
            alert_sound, winsound.SND_FILENAME ^ winsound.SND_ASYNC)


def handle_privmsg(word, word_eol, userdata):
    try:
        sender = word[0]
        recipient = word[2]
        message = word_eol[3]

        if ("MechaSqueak[BOT]" in sender):
            # Dump json to the logs
            event_json = json.dumps(
                {"sender": sender, "recipient": recipient, "message": message})
            rat_lib.append_to_log(event_json)

            # Parse a case data from the message
            case_data = rat_lib.parse_ratsignal(message)

            # Handle if found, and it's for our platform
            if case_data:
                trigger_alert(case_data)

                # Send to server
                rat_client.send_case_data(case_data)

    except Exception as e:
        error_str = "EXCEPTION: " + e
        hexchat.prnt(error_str)
        rat_lib.append_to_log(error_str)

    return hexchat.EAT_NONE


def trigger_alert(case_data):
    platform = rat_config.get(config_platform)
    if (platform != "ALL") and (case_data["platform"] != platform):
        return

    game_version = rat_config.get(config_game_version)
    if (game_version != "ALL"):
        case_game_version = "ODYSSEY" if case_data["odyssey"] else "HORIZONS"
        if (case_game_version != game_version):
            return

    play_alert()

    clipping_format = rat_config.get(config_clipping_format)
    if clipping_format is not None:
        copy_to_clipboard(rat_lib.build_clip_string(
            clipping_format, _separator, case_data))


def parse_bool(word):
    uword = word.upper()
    if(uword == "TRUE"):
        val = True
    elif(uword == "FALSE"):
        val = False
    else:
        raise Exception()
    return val


def set_logging_enabled(val):
    val = rat_lib.set_logging_enabled(val)
    rat_config.set(config_logging_enabled, val)
    if(val):
        hexchat.prnt("Logging to '" + rat_lib.log_path())
    else:
        hexchat.prnt("Logging disabled")


def handle_fr_log(word, word_eol, userdata):
    try:
        if len(word) < 2:
            raise Exception()
        val = parse_bool(word[1])
        set_logging_enabled(val)

    except:
        print(
            f"Usage: {fr_log_usage} (Current: '{rat_lib.get_logging_enabled()}')")


def handle_fr_clip(word, word_eol, userdata):
    try:
        if len(word) < 2:
            raise Exception()
        new_format = word[1]
        for ch in new_format:
            if not ch in rat_lib.formatters:
                hexchat.prnt("Invalid format string! Character '" +
                             ch + "' is not valid!")
                raise Exception()
        rat_config.set(config_clipping_format, new_format)
        hexchat.prnt("Clipping format '" + new_format + "'")

    except:
        print(
            f"Usage: {fr_clip_usage} (Current: '{rat_config.get(config_clipping_format)}')")


def handle_fr_platform(word, word_eol, userdata):
    try:
        if len(word) < 2:
            raise Exception()
        platform = word[1].upper()
        if platform in ["ALL", "PC", "XP", "PS4"]:
            rat_config('platform', platform)
            hexchat.prnt("Platform now " + platform)
        else:
            hexchat.prnt("Invalid platform '" + platform + "'")
            raise Exception()

    except:
        print(
            f"Usage: {fr_platform_usage} (Current: '{rat_config.get(config_platform)}')")


def handle_fr_sound(word, word_eol, userdata):
    try:
        if len(word) < 2:
            raise Exception()
        path = word[1]
        if os.path.isfile(path):
            rat_config.set(config_alert_sound, path)
            hexchat.prnt("Sound set to '" + path + "'")
        else:
            hexchat.prnt("Can't find file at path '" + path + "'")

    except:
        print(
            f"Usage: {fr_sound_usage}  (Current: '{rat_config.get(config_alert_sound)}')")


def handle_fr_game_version(word, word_eol, userdata):
    try:
        if len(word) < 2:
            raise Exception()
        game_version = word[1].upper()
        if game_version in ["ALL", "HORIZONS", "ODYSSEY"]:
            rat_config.set(config_game_version, game_version)
            hexchat.prnt("Game version now " + game_version)
        else:
            hexchat.prnt("Invalid game version '" + game_version + "'")
            raise Exception()

    except:
        print(
            f"Usage: {fr_game_version_usage} (Current: '{rat_config.get(config_game_version)}')")


def main_thread():
    pass


def init():
    rat_config.init(default={
        config_logging_enabled: False,
        config_clipping_format: 's',
        config_platform: 'PC',
        config_game_version: 'ALL',
        config_alert_sound: os.path.join(path, "alert.wav")
    })

    set_logging_enabled(rat_config.get(config_logging_enabled))

    hexchat.hook_server("PRIVMSG", handle_privmsg)
    hexchat.hook_command("FR_LOG", handle_fr_log, help=fr_log_usage)
    hexchat.hook_command("FR_CLIP", handle_fr_clip, help=fr_clip_usage)
    hexchat.hook_command("FR_PLATFORM", handle_fr_platform, help=fr_platform_usage)
    hexchat.hook_command("FR_SOUND", handle_fr_sound, help=fr_sound_usage)
    hexchat.hook_command(
        "FR_GAME_VERSION", handle_fr_game_version, help=fr_game_version_usage)

    # thread = threading.Thread(target=main_thread)
    # thread.start()

init()
