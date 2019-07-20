import rat_lib
import json
import os
import tempfile

log_file = os.path.join(tempfile.gettempdir(), "ratirc.log")
f = open(log_file, "r")
for line in f:
	try:
		signal = json.loads(line)
	except:
		continue
	message = signal["message"]
	case = rat_lib.parse_ratsignal(signal["message"])
	if case:
		print(json.dumps(case))

