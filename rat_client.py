import json
import requests
import rat_client
import time

_server_url = 'http://localhost:8000'


def send_case_data(case_data):
    try:
        content = json.dumps(case_data)
        r = requests.post(
            _server_url + '/ratsignal', json=case_data)
        print(r.text)
    except:
        print("Failed to post case to FuelRatVA server!")


def main():
    for num in range(0, 20):
        send_test_case(num)
        time.sleep(.5)


def send_test_case(num):
    case = {}
    case["case"] = num
    case["platform"] = "PC"
    case["code_red"] = True
    case["odyssey"] = True
    case["cmdr"] = f"Guntereno {num}"
    case["system"] = "Sol"
    case["desc"] = "It smells a bit"
    case["permit"] = None
    case["language"] = "English (UK)"
    case["locale"] = "en-gb"
    case["nick"] = "Reno"
    case["signal"] = "PC_SIGNAL"
    rat_client.send_case_data(case)


if __name__ == "__main__":
    main()
