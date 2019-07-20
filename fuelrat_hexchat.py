import datetime
import hexchat
import json
import os
import sys
from tkinter import Tk

__module_name__ = "fuelrat_helper_hexchat"
__module_version__ = "1.0"
__module_description__ = "Fuel Rat Helper"

# The script folder isn't necessarily in the search path when running through HexChat
path = os.path.join(hexchat.get_info("configdir"), "addons")
if path not in sys.path:
    sys.path.append(path)

import rat_lib

_clipping_enabled = True

def copy_to_clipboard(line):
	global _clipping_enabled
	if _clipping_enabled:
		r = Tk()
		r.withdraw()
		r.clipboard_clear()
		r.clipboard_append(line)
		r.update()
		r.destroy()

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

			# If found, dump the data and copy system to clipboard
			if case_data:
				copy_to_clipboard(case_data["system"])

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
		global _clipping_enabled
		if len(word) < 2:
			raise Exception()
		_clipping_enabled = parse_bool(word[1])
		hexchat.prnt("Clipping " + ("enabled" if _clipping_enabled else "disabled"))

	except:
		print("Usage: /fr_clip <'true'/'false'> (Current: '" + str(_clipping_enabled) + "')")

hexchat.hook_server("PRIVMSG", handle_privmsg)
hexchat.hook_command("FR_LOG", handle_fr_log, help=" /fr_log <'true'/'false'>: Enable or disable FuelRat helper logging.")
hexchat.hook_command("FR_CLIP", handle_fr_clip, help=" /fr_clip <'true'/'false'>: Enable or disable copying system name to clipboard.")

#set_logging_enabled(True)
