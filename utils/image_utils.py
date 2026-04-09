import os
from typing import Dict, Tuple
import base64
import cv2
import numpy as np
import random

import pandas as pd
import torch

from PIL import Image

# CLIP 모델 로딩 및 임베딩 추출 함수
import clip

FIXED_CLASS_COLORS: Dict[str, Tuple[int, int, int]] = {
    "car": (0, 255, 0),
    "bus": (255, 127, 0),
    "truck": (255, 255, 0),
    "person": (255, 0, 0),
    "motorcycle": (255, 0, 255),
}


# *랜덤 색상 저장할 딕셔너리
class_color_map: Dict[str, Tuple[int, int, int]] = {}


# *랜덤 색상 지정 함수
def get_random_color():
    return (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

# *클래스명이랑 색상 매칭 함수
def get_class_color(classname):
    if classname in FIXED_CLASS_COLORS:
        return FIXED_CLASS_COLORS[classname]
    if classname not in class_color_map:
        class_color_map[classname] = get_random_color()
    return class_color_map[classname]


# *썸네일 이미지 생성 함수
def get_image_thumbnail(filename, img_folder, thumb_size = (120, 90)):
    image_path = os.path.join(img_folder, filename)
    img = imread_unicode(image_path)

    if img is None:
        return ""
    h, w = img.shape[:2]
    if h == 0 or w == 0:
        return ""
    scale = min(thumb_size[0] / w, thumb_size[1] / h)
    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
    try:
        thumb = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        success, buffer = cv2.imencode(".jpg", thumb)
        if not success:
            return ""
    except Exception:
        return ""
    # *웹에서 이미지 띄우려고 변환
    return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"


# *이상 경로에 대비한 함수
def imread_unicode(path):
    # * 경로에 한글,특수문자 있는지 판단 함수
    def is_unicode_path(p):
        try:
            p.encode("ascii")
            return False
        except UnicodeEncodeError:
            return True

    # *일반 경로일때
    if not is_unicode_path(path):
        return cv2.imread(path, cv2.IMREAD_COLOR)

    try:
        with open(path, "rb") as f:
            data = np.frombuffer(f.read(), np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"[읽기 실패] {path}")
        return None


# *바운딩박스 시각화
def draw_boxes(filename,gt_folder,img_folder,boxes,visible_classes=None,duplicate=False):
    # 1) 이미지 경로 생성
    image_path = os.path.join(img_folder, filename)
    # 2) 이미지 로드 (한글/특수문자 경로 지원)
    image = imread_unicode(image_path)
    if image is None:
        return None

    # 3) 바운딩박스 그리기
    for idx, row in boxes.iterrows():
        if visible_classes and row["class"] not in visible_classes:
            continue

        # 중복 검사 모드라면 색상 토글
        if duplicate:
            color = [(255, 0, 0), (0, 255, 0)][idx % 2]
        else:
            # color = get_class_color(row['class'])
            rgb = get_class_color(row["class"])
            color = (
                rgb[::-1] if not duplicate else [(0, 0, 255), (0, 255, 0)][idx % 2]
            )  # RGB→BGR

        pt1 = (int(row["xmin"]), int(row["ymin"]))
        pt2 = (int(row["xmax"]), int(row["ymax"]))
        label = row["class"]
        w = int(row["xmax"] - row["xmin"])
        h = int(row["ymax"] - row["ymin"])

        cv2.rectangle(image, pt1, pt2, color, 2)
        cv2.putText(
            image,
            f"{label} ({w}x{h})",
            (pt1[0], pt1[1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )

    # 4) Base64 인코딩
    success, buffer = cv2.imencode(".jpg", image)
    if not success:
        return None
    return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"


def draw_boxes_duplicate(filename, gt_folder, img_folder, matched_df):
    """
    matched_df: 중복된 두 줄만 들어온 DataFrame (line_a, line_b)
    """
    image_path = os.path.join(img_folder, filename)
    image = imread_unicode(image_path)
    if image is None:
        return None

    img = image.copy()

    # 색상 고정 (BGR)
    COLORS = [
        (0, 0, 255),  # A: 빨강
        (0, 255, 0),  # B: 초록
    ]

    for i, (_, row) in enumerate(matched_df.iterrows()):
        color = COLORS[i % 2]

        x1, y1, x2, y2 = map(int, [row["xmin"], row["ymin"], row["xmax"], row["ymax"]])

        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)

        # 라벨 표시 (A / B)
        if i == 0:  # A → 왼쪽 상단
            label = "A"
            tx = x1 + 4
        else:  # B → 오른쪽 상단
            label = "B"
            tx = x2 - 20  # 글자 폭 고려

        ty = max(15, y1 - 6)

        cv2.putText(
            img, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2, cv2.LINE_AA
        )

    success, buffer = cv2.imencode(".jpg", img)
    if not success:
        return None

    return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"

def get_image_base64(filename, img_folder):
    image_path = os.path.join(img_folder, filename)
    img = imread_unicode(image_path)
    if img is None:
        return ""

    success, buffer = cv2.imencode(".jpg", img)
    if not success:
        return ""

    return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"

def scan_image_files(img_folder):
    IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp")
    image_files = []
    for root, _, files in os.walk(img_folder):
        for fn in files:
            if fn.lower().endswith(IMAGE_EXTS):
                image_files.append(os.path.join(root, fn))
    return image_files

# *히트맵 관련 함수
def compute_heatmap_data(df, grid_size):
    df = df.dropna(subset=["xmin_norm", "xmax_norm", "ymin_norm", "ymax_norm"]).copy()
    heatmap = np.zeros((grid_size, grid_size), dtype=int)

    for _, row in df.iterrows():
        xmin_i = int(np.floor(row["xmin_norm"] * grid_size))
        xmax_i = int(np.floor(row["xmax_norm"] * grid_size))
        ymin_i = int(np.floor(row["ymin_norm"] * grid_size))
        ymax_i = int(np.floor(row["ymax_norm"] * grid_size))

        xmin_i = max(0, min(xmin_i, grid_size - 1))
        xmax_i = max(0, min(xmax_i, grid_size - 1))
        ymin_i = max(0, min(ymin_i, grid_size - 1))
        ymax_i = max(0, min(ymax_i, grid_size - 1))

        for y in range(ymin_i, ymax_i + 1):
            for x in range(xmin_i, xmax_i + 1):
                heatmap[y, x] += 1

    y, x = np.meshgrid(np.arange(grid_size), np.arange(grid_size), indexing="ij")
    df_heat = pd.DataFrame(
        {"grid_x": x.ravel(), "grid_y": y.ravel(), "box_count": heatmap.ravel()}
    )
    return df_heat[df_heat["box_count"] > 0].copy()

def load_clip_model():

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    model.eval()  # ← 추가
    return model, preprocess, device


def get_image_embedding(image_path, model, preprocess, device):

    img = Image.open(image_path).convert("RGB")  # ← 색공간 고정
    image = preprocess(img).unsqueeze(0).to(device)
    with torch.no_grad():
        feats = model.encode_image(image)
    return feats.cpu().numpy().flatten()