# app.py

import logging
import os
import re
import threading
from datetime import datetime

from callbacks.core import register_callbacks
from dash import Dash
from flask import jsonify, request
from layout import create_layout

active_users = set()
lock = threading.Lock()
# IGNORED_IPS = {"127.0.0.1"}  # ← 여기에 네 로컬/테스트용 IP들 넣기
IGNORED_IPS = {}  # ← 여기에 네 로컬/테스트용 IP들 넣기

# IP 주소를 저장할 딕셔너리 (key: session key, value: IP)
user_ip_map = {}


def get_client_ip(request):
    """실제 클라이언트 IP 주소를 가져옵니다 (프록시/리버스 프록시 고려)"""
    # X-Forwarded-For 헤더 확인 (프록시를 거친 경우)
    if request.headers.get("X-Forwarded-For"):
        # X-Forwarded-For는 여러 IP를 포함할 수 있으므로 첫 번째 IP 사용
        ip = request.headers.get("X-Forwarded-For").split(",")[0].strip()
        if ip:
            return ip

    # X-Real-IP 헤더 확인 (일부 프록시에서 사용)
    if request.headers.get("X-Real-IP"):
        return request.headers.get("X-Real-IP").strip()

    # 기본 remote_addr 사용
    return request.remote_addr or "unknown"


def parse_user_agent(ua: str):
    """User-Agent에서 브라우저명과 OS를 간단히 추출"""
    ua = ua or ""
    # OS
    if "Windows" in ua:
        os_name = "Windows"
    elif "Mac" in ua:
        os_name = "macOS"
    elif "Linux" in ua:
        os_name = "Linux"
    elif "Android" in ua:
        os_name = "Android"
    elif "iPhone" in ua or "iPad" in ua:
        os_name = "iOS"
    else:
        os_name = "Unknown"

    # Browser
    browser_patterns = [
        ("Chrome", r"Chrome/([\d.]+)"),
        ("Edge", r"Edg/([\d.]+)"),
        ("Firefox", r"Firefox/([\d.]+)"),
        ("Safari", r"Version/([\d.]+).*Safari"),
    ]
    browser = "Unknown"
    for name, pattern in browser_patterns:
        if re.search(pattern, ua):
            browser = name
            break

    return browser, os_name


LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def get_log_path():
    today = datetime.now()
    folder = os.path.join(LOG_DIR, today.strftime("%Y-%m"))
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"{today.strftime('%Y-%m-%d')}_log.txt")


def log_event(event_type, ip, ua):
    print("LOG PATH:", get_log_path())

    if ip in IGNORED_IPS:
        return
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    browser, os_name = parse_user_agent(ua)
    log_path = get_log_path()
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{now}] {event_type}: {ip} | {browser} | {os_name}\n")
    except (IOError, OSError) as e:
        logging.error(f"로그 파일 쓰기 실패: {log_path}, 오류: {e}")


log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)
app = Dash(__name__, suppress_callback_exceptions=True)

server = app.server
app.layout = create_layout()
app.title = "Dashboard_v1.0.1"
register_callbacks(app)


@server.before_request
def handle_entry():
    ip = get_client_ip(request)
    ua = request.headers.get("User-Agent", "")
    key = f"{ip}|{ua}"
    with lock:
        if key not in active_users:
            active_users.add(key)
            user_ip_map[key] = ip  # IP 주소 저장
            log_event("ENTER", ip, ua)


@server.route("/_logout/<token>", methods=["POST", "GET"])
def handle_manual_logout(token):  # token은 라우트에 필요하지만 현재 사용하지 않음
    ip = get_client_ip(request)
    ua = request.headers.get("User-Agent", "")
    key = f"{ip}|{ua}"
    with lock:
        if key in active_users:
            active_users.remove(key)
            user_ip_map.pop(key, None)  # IP 맵에서도 제거
            log_event("EXIT", ip, ua)
    return "ok"


@server.route("/log_tab", methods=["POST"])
def log_tab():
    # 실제 클라이언트 IP 가져오기
    ip = get_client_ip(request)

    # 세션에서 IP를 찾을 수 없는 경우, User-Agent로 매칭 시도
    if ip == "127.0.0.1" or ip == "unknown":
        ua = request.headers.get("User-Agent", "")
        with lock:
            # User-Agent로 매칭되는 세션 찾기
            for key in user_ip_map:
                if key.endswith(f"|{ua}"):
                    ip = user_ip_map[key]
                    break

    try:
        data = request.get_json()
        tab_type = data.get("tab_type", "main") if data else "main"
        tab = data.get("tab", "unknown") if data else "unknown"
    except (ValueError, TypeError, AttributeError) as e:
        logging.warning(f"log_tab JSON 파싱 실패: {e}")
        tab_type, tab = "main", "unknown"

    # 이름 매핑
    TAB_LABELS = {
        "tab-visual": "분석 시각화",
        "tab-stats": "통계 요약",
        "tab-img-display": "이미지 View",
        "tab-duplicate": "데이터 검사",
        "subtab-scatter": "산점도",
        "subtab-heatmap": "히트맵",
        "subtab-gt-duplicate": "GT 중복 검사",
        "subtab-image-feature": "이미지 특징 검사",
    }

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tab_label = TAB_LABELS.get(tab, tab)

    type_label = {
        "main": "상위탭",
        "visual_sub": "분석 시각화 하위탭",
        "duplicate_sub": "데이터 검사 하위탭",
    }.get(tab_type, tab_type)

    log_path = get_log_path()

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{now}] {type_label}: {ip} -> {tab_label} ({tab})\n")
    except (IOError, OSError) as e:
        logging.error(f"로그 파일 쓰기 실패: {log_path}, 오류: {e}")

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
    # app.run(host="0.0.0.0", port=8080, debug=False)

    # ! 127.0.0.1:port 로 웹에서 들어가면됨 
