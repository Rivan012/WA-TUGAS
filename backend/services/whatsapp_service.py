import requests


def send_message(to, message):
    try:
        r = requests.post(
            "http://127.0.0.1:3000/send-message",
            json={"to": to, "message": message},
            timeout=10
        )
        print(r.status_code)
        print(r.text)
        return r.status_code == 200

    except Exception as e:
        print(e)
        return False