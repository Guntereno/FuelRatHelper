import json
import os
import time
import tkinter
import winsound

import rat_config
import rat_client
import rat_lib


fr_log_usage = " /fr_log <'true'/'false'>: Enable or disable FuelRat helper logging."
fr_clip_usage = " /fr_clip <'format'>: Specify format of clipped string (none to disable)\nc=casenum, s=systemname, n=clientname"
fr_platform_usage = " /fr_platform <'ALL'/'PC'/'XB'/'PS4'>: Set platform for alerts."
fr_sound_usage = " /fr_sound <path>: Set the file to use as an alert tone."
fr_game_version_usage = " /fr_game_version <'ALL'/'HORIZONS'/'ODYSSEY'>: Set which version in which cases should trigger alerts."

_root_path = None
_console_write_callback = None

_config_logging_enabled = 'logging_enabled'
_config_clipping_format = 'clipping_format'
_config_platform = 'platform'
_config_game_version = 'game_version'
_config_alert_sound = 'alert_sound'

_separator = "|"


def console_write(line):
    if(_console_write_callback != None):
        _console_write_callback(line)
    rat_lib.append_to_log(line)


def copy_to_clipboard(line):
    r = tkinter.Tk()
    r.withdraw()
    r.clipboard_clear()
    r.clipboard_append(line)
    r.update()
    r.destroy()


def play_alert():
    alert_sound = rat_config.get(_config_alert_sound)
    if alert_sound:
        winsound.PlaySound(
            alert_sound, winsound.SND_FILENAME ^ winsound.SND_ASYNC)


def handle_message(sender, recipient, message):
    try:
        if ("MechaSqueak[BOT]" in sender):
            handle_spatch_message(sender, recipient, message)

    except Exception as e:
        error_str = "EXCEPTION: " + e
        console_write(error_str)
        rat_lib.append_to_log(error_str)


def handle_spatch_message(sender, recipient, message):
    event_json = json.dumps(
        {"sender": sender, "recipient": recipient, "message": message})
    rat_lib.append_to_log(event_json)

    data = rat_lib.parse_ratsignal(message)
    if data:
        trigger_alert(data)
        rat_client.send_case_data(data)
        return

    data = rat_lib.parse_case_close(message)
    if data:
        rat_client.delete_case(data)
        return

    data = rat_lib.parse_case_system_update(message)
    if data:
        rat_client.update_case(data)
        return

    data = rat_lib.parse_case_client_update(message)
    if data:
        rat_client.update_case(data)
        return


def trigger_alert(case_data):
    platform = rat_config.get(_config_platform)
    if (platform != "ALL") and (case_data["platform"] != platform):
        return

    game_version = rat_config.get(_config_game_version)
    if (game_version != "ALL"):
        case_game_version = "ODYSSEY" if case_data["odyssey"] else "HORIZONS"
        if (case_game_version != game_version):
            return

    play_alert()

    clipping_format = rat_config.get(_config_clipping_format)
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
    rat_config.set(_config_logging_enabled, val)
    if(val):
        console_write("Logging to '" + rat_lib.log_path())
    else:
        console_write("Logging disabled")


def handle_fr_log(args):
    try:
        if len(args) < 2:
            raise Exception()
        val = parse_bool(args[1])
        set_logging_enabled(val)

    except:
        print(
            f"Usage: {fr_log_usage} (Current: '{rat_lib.get_logging_enabled()}')")


def handle_fr_clip(args):
    try:
        if len(args) < 2:
            raise Exception()
        new_format = args[1]
        for ch in new_format:
            if not ch in rat_lib.formatters:
                console_write("Invalid format string! Character '" +
                             ch + "' is not valid!")
                raise Exception()
        rat_config.set(_config_clipping_format, new_format)
        console_write("Clipping format '" + new_format + "'")

    except:
        print(
            f"Usage: {fr_clip_usage} (Current: '{rat_config.get(_config_clipping_format)}')")


def handle_fr_platform(args):
    try:
        if len(args) < 2:
            raise Exception()
        platform = args[1].upper()
        if platform in ["ALL", "PC", "XP", "PS4"]:
            rat_config('platform', platform)
            console_write("Platform now " + platform)
        else:
            console_write("Invalid platform '" + platform + "'")
            raise Exception()

    except:
        print(
            f"Usage: {fr_platform_usage} (Current: '{rat_config.get(_config_platform)}')")


def handle_fr_sound(args):
    try:
        if len(args) < 2:
            raise Exception()
        path = args[1]
        if os.path.isfile(path):
            rat_config.set(_config_alert_sound, path)
            console_write("Sound set to '" + path + "'")
        else:
            console_write("Can't find file at path '" + path + "'")

    except:
        print(
            f"Usage: {fr_sound_usage}  (Current: '{rat_config.get(_config_alert_sound)}')")


def handle_fr_game_version(args):
    try:
        if len(args) < 2:
            raise Exception()
        game_version = args[1].upper()
        if game_version in ["ALL", "HORIZONS", "ODYSSEY"]:
            rat_config.set(_config_game_version, game_version)
            console_write("Game version now " + game_version)
        else:
            console_write("Invalid game version '" + game_version + "'")
            raise Exception()

    except:
        print(
            f"Usage: {fr_game_version_usage} (Current: '{rat_config.get(_config_game_version)}')")


def init(root_path, console_write_callback = None):
    global _root_path
    global _console_write_callback

    _root_path = root_path
    _console_write_callback = console_write_callback

    rat_config.init(default={
        _config_logging_enabled: False,
        _config_clipping_format: 's',
        _config_platform: 'PC',
        _config_game_version: 'ALL',
        _config_alert_sound: os.path.join(_root_path, "alert.wav")
    })

    set_logging_enabled(rat_config.get(_config_logging_enabled))


if __name__ == "__main__":
    file_path = os.path.realpath(__file__)
    init(file_path, print)

    with open(rat_lib.log_path()) as log_file:
        for line in log_file:
            try:
                msg = json.loads(line)
                if msg is not None:
                    handle_message(msg['sender'], msg['recipient'], msg['message'])
                    print(msg['message'])
                    time.sleep(0.02)
            except:
                continue
