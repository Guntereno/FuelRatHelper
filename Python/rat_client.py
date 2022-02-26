import requests
import time

_server_url = 'http://localhost:8000'


def send_case_data(data):
    try:
        r = requests.post(
            _server_url + '/case', json=data)
        print(r.text)
    except:
        print("Failed to post case!")

def delete_case(data):
    try:
        r = requests.delete(
            _server_url + f'/case', json=data)
        print(r.text)
    except:
        print("Failed to delete case!")

def update_case(data):
    try:
        r = requests.patch(
            _server_url + f'/case', json=data)
        print(r.text)
    except:
        print("Failed to patch case!")

def add_note_to_case(data):
    try:
        r = requests.post(
            _server_url + f'/note', json=data)
        print(r.text)
    except:
        print("Failed to post note!")

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
    send_case_data(case)


if __name__ == "__main__":
    main()
