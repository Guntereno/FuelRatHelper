from datetime import datetime
import json
import os
import re
import tempfile

_logging_enabled = False

def set_logging_enabled(val):
	global _logging_enabled
	_logging_enabled = bool(val)
	return _logging_enabled

def get_logging_enabled():
	return _logging_enabled

def log_path():
	return os.path.join(tempfile.gettempdir(), "ratirc.log")

def append_to_log(line):
	if not _logging_enabled:
		return
	logfile = open(log_path(), 'a+')
	logfile.write(line + "\n")

# This is the standard ratsignal, fired after RatMama introduces a client via the website
_regex_standard = re.compile(u"^:RATSIGNAL - CMDR \u0002(.*?)\u0002 - Reported System: \u0002(.+?)\u0002.*? - Platform: \u0002(.+?)\u0002 - O2: (.*?) - Language: (.*?) (.*)$")
_regex_in_parenthesis = re.compile(r"\((.*?)\)")
_regex_casenum = re.compile(r"Case #(\d+)")
def parse_ratsignal_standard(signal):
	# Example: ':RATSIGNAL - CMDR Xtremetrumpeter - Reported System: Tariansa (136.75 LY from Fuelum) - Platform: 03XB - O2: 04NOT OK - Language: English (en-US) (Case #7) (XB_SIGNAL)'
	match = re.search(_regex_standard, signal)
	if match is None:
		return None

	result = {}
	result["cmdr"] = match.group(1)
	result["system"] = match.group(2).upper()

	o2_str = match.group(4)
	if(o2_str.upper() == "OK"):
		has_o2 = True
	elif(o2_str.upper() == u"\u0002\u000304NOT OK\u0003\u0002"):
		has_o2 = False
	else:
		raise Exception("Unexpected signal O2 status format!: " + o2_str)
	result["o2"] = has_o2

	platform_str = match.group(3)
	if(platform_str.upper() == "PC"):
		platform = "PC"
	elif(platform_str.upper() == u"\u000312PS4\u0003"):
		platform = "PS4"
	elif(platform_str.upper() == u"\u000303XB\u0003"):
		platform = "XB"
	else:
		raise Exception("Unexpected signal platform format!: " + platform_str)
	result["platform"] = platform

	bracket_contents = re.findall(_regex_in_parenthesis, match.group(6))
	result["language"] = bracket_contents[0]

	casenum_match = re.match(_regex_casenum, bracket_contents[1])
	casenum = int(casenum_match.group(1))
	result["case"] = casenum
	
	return result

# MechaSqueak will fire this after someone enters their own ratsignal into IRC
_regex_detected = re.compile(r'^:Received R@SIGNAL from (.*?)\. Calling all available rats! \(Case (\d*), (.*?), (.*?)\)')
def parse_ratsignal_detected(signal):
	match = re.search(_regex_detected, signal)
	if match is None:
		return None

	result = {}
	result["cmdr"] = match.group(1)
	result["system"] = match.group(4).upper()
	result["platform"] = match.group(3)
	result["o2"] = None
	result["language"] = None
	result["case"] = int(match.group(2))

	return result

# This form is posted after spatch manually inject the case:
#  <RatMama[BOT]> Incoming Client: 4ertilla - System: Col 285 - Platform: PC - O2: OK - Language: Russian (ru-RU) - IRC Nickname: ertilla
#  <Numerlor> !prep ertilla
#  <MechaSqueak[BOT]> ertilla: Please drop from supercruise and come to a full stop. Disable all modules EXCEPT life support (instructions available if needed). If an emergency oxygen countdown appears at any time, let us know right away.
#  <Doctor5555> ertilla: Вы видите отсчет времени кислорода?
#  <NumberPi> !inject 4ertilla RATSIGNAL - System: Col 285 - Platform: PC - O2: OK - Language: Russian (ru-RU) - IRC Nickname: ertilla
#  <MechaSqueak[BOT]> 4ertilla's case opened with: "R@SIGNAL - System: Col 285 - Platform: PC - O2: OK - Language: Russian (ru-RU) - IRC Nickname: ertilla"  (Case 2, PC)
_regex_injected = re.compile(r'^:(.+?)\'s case opened with: "R@SIGNAL - System: (.+?) - Platform: (.+?) - O2: (.+?) - Language: .+? \((.+?)\) - IRC Nickname: (.+?)"  \(Case (\d+?), (\w+?)\)$')
def parse_ratsignal_injected(signal):
	match = re.search(_regex_injected, signal)
	if match is None:
		return None

	result = {}
	result["cmdr"] = match.group(1)
	result["system"] = match.group(2).upper()
	result["platform"] = match.group(3)
	result["o2"] = match.group(4)
	result["language"] = match.group(8)
	result["case"] = int(match.group(7))

	return result

def parse_ratsignal(signal):
	tests = [
		parse_ratsignal_standard,
		parse_ratsignal_detected,
		parse_ratsignal_injected
	]

	for test in tests:
		case = test(signal)
		if not case is None:
			return case
	
	return None
