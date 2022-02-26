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


# Examples of the standard ratsignal, fired after RatMama introduces a client via the website:
# :\u0002\u000300,07RATSIGNAL\u0003\u0002 Case\u0002 #0\u0002 \u0002\u000306PC\u0003\u0002 \u2013 \u0002CMDR\u0002 KcalbDemon \u2013 \u0002System:\u0002 \"HEIDUMANI\"\u001d (\u0002M\u0002 Red dwarf 76 LY from Fuelum)\u001d \u2013 \u0002Language:\u0002 Italian (it) (PC_SIGNAL)
# :\u0002\u000300,07RATSIGNAL\u0003\u0002 Case\u0002 #9\u0002 \u0002\u000306PC\u0003\u0002 (\u000307Odyssey\u0003) \u2013 \u0002CMDR\u0002 Towelie #0420 \u2013 \u0002System:\u0002 \"VELLI\"\u001d (\u0002M\u0002 Red dwarf 125.7 LY from Fuelum)\u001d \u2013 \u0002Language:\u0002 English (United Kingdom) (en-GB) \u2013 \u0002Nick:\u0002 Towelie_0420 (PC_SIGNAL)
# :\u0002\u000300,07RATSIGNAL\u0003\u0002 Case\u0002 #7\u0002 \u0002\u000306PC\u0003\u0002 \u2013 \u0002CMDR\u0002 ADIllustration \u2013 \u0002System:\u0002 \"OTEGINE\"\u001d (Brown dwarf 33.7 LY from Fuelum)\u001d \u000307(Pilots' Federation District Permit Required)\u0003 \u2013 \u0002Language:\u0002 English (United States) (en-US) (PC_SIGNAL)
# :\u0002\u000300,07RATSIGNAL\u0003\u0002 Case\u0002 #3\u0002 \u0002\u000303Xbox\u0003\u0002 \u2013 \u0002CMDR\u0002 Ghost ZO\u000309 (In game, location hidden)\u0003 \u2013 \u0002System:\u0002 \"HYADES SECTOR KN-Z A1-4\"\u001d (Brown dwarf 134.5 LY from Maia)\u001d \u2013 \u0002Language:\u0002 English (United States) (en-US) \u2013 \u0002Nick:\u0002 Ghost_ZO (XB_SIGNAL)
# :\u0002\u000300,07RATSIGNAL\u0003\u0002 Case\u0002 #5\u0002 \u0002\u000306PC\u0003\u0002 (\u000304Code Red\u0003) (\u000307Odyssey\u0003) \u2013 \u0002CMDR\u0002 JHAFERLAND \u2013 \u0002System:\u0002 \"COL 285 SECTOR QA-K B23-9\"\u001d (Brown dwarf 140.1 LY from Fuelum)\u001d \u2013 \u0002Language:\u0002 Spanish (Mexico) (es-MX) (PC_SIGNAL)
_regex_standard = re.compile(
    u"""^:\u0002\u000300,07RATSIGNAL\u0003\u0002 """
    u"""Case\u0002 #(.+?)\u0002 """							# Case number
    u"""\u0002\u0003\d\d(.+?)\u0003\u0002 """				# Platform
    u"""(\(\u000304Code Red\u0003\) )?"""					# Code Red (optional)
    u"""(\(\u000307Odyssey\u0003\) )?"""					# Odyssey (optional)
    u"""\u2013 \u0002CMDR\u0002 (.+?)\u2013 """				# CMDR name
    u"""\u0002System:\u0002 \"(.+?)\"\u001d """				# System name
    u"""\((.+?)\)\u001d """									# System desc
    u"""(?:\u000307\((.+?)\)\u0003 )?"""					# Permit (optional)
    u"""\u2013 \u0002Language:\u0002 (.+?(?: \(.+?\))?) """	# Language
    u"""\((.+?)\) """										# Locale
    u"""(?:\u2013 \u0002Nick:\u0002 (.*?) )?"""				# Nick (optional)
    u"""\((.*?)\)$"""										# Signal
)


def parse_ratsignal_standard(message):
    match = re.search(_regex_standard, message)
    if match is None:
        if 'RATSIGNAL' in message:
            append_to_log(f'ERROR: Failed to parse line containing RATSIGNAL!')
        return None

    result = {}
    result["case"] = int(match.group(1))
    result["platform"] = match.group(2)
    result["code_red"] = match.group(3) is not None
    result["odyssey"] = match.group(4) is not None
    result["cmdr"] = match.group(5)
    result["system"] = match.group(6).upper()
    result["desc"] = match.group(7)
    result["permit"] = match.group(8)
    result["language"] = match.group(9)
    result["locale"] = match.group(10)
    result["nick"] = match.group(11)
    result["signal"] = match.group(12)

    return result


def parse_ratsignal(signal):
    tests = [
        parse_ratsignal_standard
    ]

    for test in tests:
        case = test(signal)
        if case is not None:
            return case

    return None


def build_clip_string(format, separator, case):
    elements = []
    for ch in format:
        element = get_clip_element(ch, case)
        if element is not None:
            elements.append(element)
    return separator.join(elements)


formatters = {
    'n': "case",
    'c': "cmdr",
    's': "system"
}


def get_clip_element(format_ch, case):
    if format_ch in formatters:
        return str(case[formatters[format_ch]])
    return None


def remove_special_characters(input):
    output = ""
    for ch in input:
        if ord(ch) >= 0x20:
            output += ch
    return output


# Example of closed case message from Mecha Squeak:
# Closed case #7 (remineitor 1884) to Lev. Do the paperwork: https://t.fuelr.at/2zat
_regex_closed_case = re.compile(
    u"""^:Closed case #(\d+?) \((.+?)\) to (.+?)\. Do the paperwork: (https:\/\/t\.fuelr\.at\/.+)$""")

def parse_case_close(message):
    match = re.search(_regex_closed_case, message)
    if match is None:
        return None

    result = {}
    result["case"] = int(match.group(1))
    result["client"] = match.group(2)
    result["rat"] = match.group(3)
    result["paperwork"] = match.group(4)

    return result


# Example of system update
# ":System for case #8 (Merickder) has been changed to \"ARIETIS SECTOR WK-V A3-0\"\u001d (Brown dwarf 204.3 LY from Maia)\u001d"

_regex_case_system_updated = re.compile(
    u"""^:System for case #(\d+?) \((.+?)\) has been changed to \\"(.+?)\\"\\u001d \((.+?)\)\\u001d$""")

def parse_case_system_update(message):
    match = re.search(_regex_case_system_updated, message)
    if match is None:
        return None

    result = {}
    result["case"] = int(match.group(1))
    result["client"] = match.group(2)
    result["system"] = match.group(3)
    result["desc"] = match.group(4)

    return result


# Example of client name update
# ":Client name for case #9 (Discount Shoper) has been changed to: DiscountShopper."

_regex_case_client_updated = re.compile(
    u"""^:Client name for case #(\d+?) \((.+?)\) has been changed to: (.+?)\.$""")

def parse_case_client_update(message):
    match = re.search(_regex_case_client_updated, message)
    if match is None:
        return None

    result = {}
    result["case"] = int(match.group(1))
    result["client"] = match.group(3)

    return result

# Example of case note addition
# ":Updated case #1 with \"im at noriega port with 3 mins on the oxygen depletion timer\"."

_regex_case_note_added = re.compile(
    u"""^:Updated case #(\d+?) with \\"(.+?)\\".$""")

def parse_case_add_note(message):
    match = re.search(_regex_case_note_added, message)
    if match is None:
        return None

    result = {}
    result["case"] = int(match.group(1))
    result["note"] = match.group(2)

    return result

def main():
    num_signals = 0
    num_detected = 0

    with open(log_path()) as fp:
        lines = fp.readlines()
        for line in lines:
            wrote = False

            irc_message = json.loads(line)

            message = irc_message["message"]

            if u"RATSIGNAL" in message:
                print(message)
                wrote = True
                num_signals += 1

            case_data = parse_ratsignal(message)
            if case_data:
                print(case_data)
                wrote = True
                num_detected += 1

            if wrote:
                print()

    print(f"Detected {num_detected}/{num_signals}")


if __name__ == "__main__":
    main()
