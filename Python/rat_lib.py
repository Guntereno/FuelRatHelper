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
# :\u0002\u000300,07RATSIGNAL\u0003\u0002 Case\u0002 #3\u0002 \u0002\u000303Xbox\u0003\u0002 \u2013 \u0002CMDR\u0002 Ghost ZO\u000309 (In game, location hidden)\u0003 \u2013 \u0002System:\u0002 \"HYADES SECTOR KN-Z A1-4\"\u001d (Brown dwarf 134.5 LY from Maia)\u001d \u2013 \u0002Language:\u0002 English (United States) (en-US) \u2013 \u0002Nick:\u0002 Ghost_ZO (XB_SIGNAL)
# :\u0002\u000300,07RATSIGNAL\u0003\u0002 Case\u0002 #5\u0002 \u0002\u000306PC\u0003\u0002 (\u000304Code Red\u0003) (\u000307Odyssey\u0003) \u2013 \u0002CMDR\u0002 JHAFERLAND \u2013 \u0002System:\u0002 \"COL 285 SECTOR QA-K B23-9\"\u001d (Brown dwarf 140.1 LY from Fuelum)\u001d \u2013 \u0002Language:\u0002 Spanish (Mexico) (es-MX) (PC_SIGNAL)
# :\u0002\u000300,07RATSIGNAL\u0003\u0002 Case\u0002 #7\u0002 \u0002\u000306PC\u0003\u0002 \u000311HOR\u0003 (\u000304Code Red\u0003) \u2013 \u0002CMDR\u0002 Kerr1x \u2013 \u0002System:\u0002 \"APOYOTA\"\u001d (\u0002M\u0002 Red dwarf 70.1 LY from Sol)\u001d \u2013 \u0002Language:\u0002 Ukrainian (Ukraine) (uk-UA) (HOR_SIGNAL)
# :\u0002\u000300,07RATSIGNAL\u0003\u0002 Case\u0002 #3\u0002 \u0002\u000306PC\u0003\u0002 \u000307ODY\u0003 \u2013 \u0002CMDR\u0002 Jack Lambert \u2013 \u0002System:\u0002 \"HIP 25376\"\u001d (\u0002F\u0002 Yellow-white star 139.5 LY from Fuelum)\u001d \u2013 \u0002Language:\u0002 German (Germany) (de-DE) \u2013 \u0002Nick:\u0002 Jack_Lambert (ODY_SIGNAL)
# :\u0002\u000300,07RATSIGNAL\u0003\u0002 Case\u0002 #1\u0002 \u0002\u000306PC\u0003\u0002 \u000311HOR\u0003 (\u000304Code Red\u0003) \u2013 \u0002CMDR\u0002 Drochila354 \u2013 \u0002System:\u0002 \"ALRAI SECTOR LC-V B2-4\"\u001d (\u0002M\u0002 Red dwarf 79.5 LY from Sol)\u001d \u2013 \u0002Language:\u0002 Russian (Russia) (ru-RU) (HOR_SIGNAL)
# :\u0002\u000300,07RATSIGNAL\u0003\u0002 Case\u0002 #1\u0002 \u0002\u000306PC\u0003\u0002 \u000313LEG\u0003 (\u000304Code Red\u0003) \u2013 \u0002CMDR\u0002 czarmulak \u2013 \u0002System:\u0002 \"EARTH EXPEDITIONARY FLEET\"\u001d (\u0002F\u0002 Yellow-white star 55 LY from Rodentia)\u001d \u2013 \u0002Language:\u0002 Polish (Poland) (pl-PL) (LEG_SIGNAL)
# :\u0002\u000300,07RATSIGNAL\u0003\u0002 Case\u0002 #1\u0002 \u0002\u000306PC\u0003\u0002 \u000313LEG\u0003 \u2013 \u0002CMDR\u0002 expertcheat \u2013 \u0002System:\u0002 \"JEIDENANNSA\"\u001d (\u0002F\u0002 Yellow-white star 182.1 LY from Sol)\u001d \u2013 \u0002Language:\u0002 Russian (ru) (LEG_SIGNAL)
# :\u0002\u000300,07RATSIGNAL\u0003\u0002 Case\u0002 #9\u0002 \u0002\u000306PC\u0003\u0002 \u000307ODY\u0003 \u2013 \u0002CMDR\u0002 DARKANGEL4645 \u2013 \u0002System:\u0002 \"HIP 19934\" \u26a0\ufe0f\u001d (\u0002K\u0002 Orange dwarf 171 LY from Sol)\u001d \u2013 \u0002Language:\u0002 English (South Africa) (en-ZA) (ODY_SIGNAL)
# :\u0002\u000300,07RATSIGNAL\u0003\u0002 Case\u0002 #5\u0002 \u0002\u000306PC\u0003\u0002 \u000307ODY\u0003 \u2013 \u0002CMDR\u0002 Santa Madredetarasse \u2013 \u0002System:\u0002 \"NN 3281\" \u26a0\ufe0f\u001d (\u0002M\u0002 Red dwarf 171.7 LY from Sol)\u001d \u2013 \u0002Language:\u0002 French (France) (fr-FR) \u2013 \u0002Nick:\u0002 Santa_Madredetarasse (ODY_SIGNAL)
_regex_standard = re.compile(
    u"""^:\u0002\u000300,07RATSIGNAL\u0003\u0002 """
    u"""Case\u0002 #(.+?)\u0002 """                         # Case number
    u"""\u0002\u0003\d\d(.+?)\u0003\u0002 """               # Platform
    u"""(?:\u0003\d\d(\w{3})\u0003 )?"""                    # Version
    u"""(\(\u000304Code Red\u0003\) )?"""                   # Code Red (optional)
    u"""\u2013 \u0002CMDR\u0002 (.+?)\u2013 """             # CMDR name
    u"""\u0002System:\u0002 \"(.+?)\""""                    # System name
    u"""( \u26a0\ufe0f)?"""                                 # Caution
    u"""\u001d """                                          # Data Separator
    u"""\((.+?)\)\u001d """                                 # System desc
    u"""(?:\u000307\((.+?)\)\u0003 )?"""                    # Permit (optional)
    u"""\u2013 \u0002Language:\u0002 (.+?(?: \(.+?\))?) """ # Language
    u"""\((.+?)\) """                                       # Locale
    u"""(?:\u2013 \u0002Nick:\u0002 (.*?) )?"""             # Nick (optional)
    u"""\((.*?)\)$"""                                       # Signal
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
    result["version"] = match.group(3)
    result["code_red"] = match.group(4) is not None
    result["cmdr"] = match.group(5)
    result["system"] = match.group(6).upper()
    result["caution"] = match.group(7) is not None
    result["desc"] = match.group(8)
    result["permit"] = match.group(9)
    result["language"] = match.group(10)
    result["locale"] = match.group(11)
    result["nick"] = match.group(12)
    result["signal"] = match.group(13)

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


# Example of note deletion
# ":Deleted line 8 of case #2"

_regex_case_note_deleted = re.compile(
    u"""^:Deleted line (\d+?) of case #(\d+?)$""")

def parse_case_note_deleted(message):
    match = re.search(_regex_case_note_deleted, message)
    if match is None:
        return None
    
    result = {}
    result['case'] = int(match.group(2))
    result['line'] = int(match.group(1))

    return result


# Example of note modification
# ":Updated line 2 of case #9 with \"in between C star and a gas giant, might be C6\"."

_regex_case_note_modified = re.compile(
    u""":Updated line (\d+?) of case #(\d+?) with \\"(.+?)\\".""")

def parse_case_note_modified(message):
    match = re.search(_regex_case_note_modified, message)
    if match is None:
        return None
    
    result = {}
    result['case'] = int(match.group(2))
    result['line'] = int(match.group(1))
    result['note'] = match.group(3)

    return result


def main():
    num_signals = 0
    num_detected = 0

    log_file = log_path()
    print(f"Opening '{log_file}'")

    if not os.path.exists(log_file):
        print("Log file doesn't exist. Exiting.")
        return

    with open(log_file) as fp:
        lines = fp.readlines()
        for line in lines:
            try:
                irc_message = json.loads(line)
            except json.JSONDecodeError:
                # Do nothing
                continue

            message = irc_message["message"]

            if u"RATSIGNAL" in message:
                print(message)
                num_signals += 1

                case_data = parse_ratsignal(message)
                if case_data:
                    print(case_data)
                    num_detected += 1
                else:
                    print(f"Failed to parse '{message}'")

                print()



    print(f"Detected {num_detected}/{num_signals}")


if __name__ == "__main__":
    main()
