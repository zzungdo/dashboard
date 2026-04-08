# callbacks/logger.py
import requests


def send_tab_log(tab_type, tab):
    try:
        requests.post(
            "http://127.0.0.1:8080/log_tab",
            json={"tab_type": tab_type, "tab": tab},
            timeout=0.3,
        )
    except Exception:
        pass
