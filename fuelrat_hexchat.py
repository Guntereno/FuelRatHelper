import datetime
from pydoc import doc
import hexchat
import json
import os
import sys
import threading
import winsound
from tkinter import Tk
import requests
import FuelRatHelper.rat_client as rat_client

__module_name__ = "fuelrat_helper_hexchat"
__module_version__ = "1.0"
__module_description__ = "Fuel Rat Helper"

# The script folder isn't necessarily in the search path when running through HexChat
path = os.path.join(hexchat.get_info("configdir"), "addons")
if path not in sys.path:
	sys.path.append(path)

__alert_sound = os.path.join(path, "alert.wav")

import rat_lib

_clipping_format = "nsc"
_separator = "|"
_platform = "PC"

_server_url = 'http://localhost:8000'

def copy_to_clipboard(line):
	if _clipping_format is not None:
		r = Tk()
		r.withdraw()
		r.clipboard_clear()
		r.clipboard_append(line)
		r.update()
		r.destroy()

def play_alert():
	if __alert_sound:
		winsound.PlaySound(__alert_sound, winsound.SND_FILENAME ^ winsound.SND_ASYNC)

def handle_privmsg(word, word_eol, userdata):
	try:
		sender = word[0]
		recipient = word[2]
		message = word_eol[3]

		if (recipient == "#fuelrats") and ("MechaSqueak[BOT]" in sender):
			# Dump json to the logs
			event_json = json.dumps({"sender": sender, "recipient": recipient, "message": message})
			rat_lib.append_to_log(event_json)

			# Parse a case data from the message
			case_data = rat_lib.parse_ratsignal(message)

			# Handle if found, and it's for our platform
			if case_data:
				if (case_data["platform"] == _platform):
					play_alert()
					copy_to_clipboard(rat_lib.build_clip_string(_clipping_format, _separator, case_data))

				# Send to server
				rat_client.send_case_data(case_data)

	except Exception as e:
		error_str = "EXCEPTION: " + e
		hexchat.prnt(error_str)
		rat_lib.append_to_log(error_str)

	return hexchat.EAT_NONE

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
		print("Usage: /fr_log <'true'/'false'> (Current: '" + str(rat_lib.get_logging_enabled()) + "')")

def handle_fr_clip(word, word_eol, userdata):
	try:
		global _clipping_format
		if len(word) < 2:
			raise Exception()
		new_format = word[1]
		for ch in format:
			if not ch in rat_lib.formatters:
				hexchat.prnt("Invalid format string! Character '" + ch + "' is not valid!")
				raise Exception()
		_clipping_format = new_format
		hexchat.prnt("Clipping format '" + _clipping_format + "'")

	except:
		print("Usage: /fr_clip <format string> (Current: '" + _clipping_format + "')")

def handle_fr_platform(word, word_eol, userdata):
	try:
		global _platform
		if len(word) < 2:
			raise Exception()
		platform = word[1]
		if platform in ["PC", "XP", "PS4"]:
			_platform = platform
			hexchat.prnt("Platform now " + _platform)
		else:
			hexchat.prnt("Invalid platform '" + platform + "'")
			raise Exception()

	except:
		print("Usage: /fr_platform <'PC'/'XB'/'PS4'> (Current: '" + _platform + "')")

def handle_fr_sound(word, word_eol, userdata):
	try:
		global __alert_sound
		if len(word) < 2:
			raise Exception()
		path = word[1]
		if os.path.isfile(path):
			__alert_sound = path
			hexchat.prnt("Sound set to '" + __alert_sound + "'")
		else:
			hexchat.prnt("Can't find file at path '" + path + "'")

	except:
		print("Usage: /fr_sound <'path'> (Current: '" + str(__alert_sound) + "')")

hexchat.hook_server("PRIVMSG", handle_privmsg)
hexchat.hook_command("FR_LOG", handle_fr_log, help=" /fr_log <'true'/'false'>: Enable or disable FuelRat helper logging.")
hexchat.hook_command("FR_CLIP", handle_fr_clip, help=" /fr_clip <'format'>: Specify format of clipped string (none to disable)\nc=casenum, s=systemname, n=clientname")
hexchat.hook_command("FR_PLATFORM", handle_fr_platform, help=" /fr_platform <'PC'/'XB'/'PS4'>: Set platform for alerts.")
hexchat.hook_command("FR_SOUND", handle_fr_sound, help=" /fr_sound <path>: Set the file to use as an alert tone.")

#set_logging_enabled(True)

def main_thread():
	pass

thread = threading.Thread(target=main_thread)
thread.start()

