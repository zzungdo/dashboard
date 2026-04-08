# utils.py
import base64
import glob
import os
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

import cv2
import imagehash
import numpy as np
import pandas as pd
import plotly.express as px
from annoy import AnnoyIndex
from tqdm import tqdm

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
def get_random_color() -> Tuple[int, int, int]:
    return (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))


# *클래스명이랑 색상 매칭 함수
def get_class_color(classname: str) -> Tuple[int, int, int]:
    if classname in FIXED_CLASS_COLORS:
        return FIXED_CLASS_COLORS[classname]
    if classname not in class_color_map:
        class_color_map[classname] = get_random_color()
    return class_color_map[classname]


# *썸네일 이미지 생성 함수
def get_image_thumbnail(
    filename: str, img_folder: str, thumb_size: Tuple[int, int] = (120, 90)
) -> str:
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
def imread_unicode(path: str) -> Optional[np.ndarray]:
    # * 경로에 한글,특수문자 있는지 판단 함수
    def is_unicode_path(p: str) -> bool:
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


# *GT 로딩 및 정규화
def load_all_gt(gt_folder: str, img_folder: str) -> pd.DataFrame:

    gt_folder = str(gt_folder).strip().strip('"').replace('r"', "").replace("r'", "")
    img_folder = str(img_folder).strip().strip('"').replace('r"', "").replace("r'", "")

    gt_folder = os.path.normpath(gt_folder)
    img_folder = os.path.normpath(img_folder)

    if not os.path.exists(gt_folder):
        print(f"[경고] GT 경로를 찾을 수 없습니다: {gt_folder}")
        return pd.DataFrame()
    if not os.path.exists(img_folder):
        print(f"[경고] 이미지 경로를 찾을 수 없습니다: {img_folder}")
        return pd.DataFrame()

    rows = []

    for label_path in glob.glob(os.path.join(gt_folder, "*.txt")):
        file = os.path.basename(label_path)

        if not file.lower().endswith(".txt"):
            continue
        label_path = os.path.join(gt_folder, file)
        image_name = os.path.splitext(file)[0] + ".jpg"
        image_path = os.path.join(img_folder, image_name)
        image_exists = os.path.exists(image_path)

        if image_exists:
            img = imread_unicode(image_path)
            if img is None:
                continue
            H, W = img.shape[:2]
        else:
            H, W = None, None

        try:
            df = pd.read_csv(
                label_path,
                header=None,
                names=["class", "xmin", "ymin", "xmax", "ymax"],
                sep=r"[,\s]+",
                engine="python",
            )
        except Exception:
            continue

        # 숫자 변환 + 유효박스 필터
        for col in ["xmin", "ymin", "xmax", "ymax"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["xmin", "ymin", "xmax", "ymax"])
        df = df[(df["xmax"] > df["xmin"]) & (df["ymax"] > df["ymin"])]
        # bbox 필터 이후, if image_exists 분기 전에
        df["filename"] = image_name
        df["image_exists"] = image_exists

        if image_exists:
            df["xmin"] = df["xmin"].clip(0, W - 1)
            df["xmax"] = df["xmax"].clip(0, W - 1)
            df["ymin"] = df["ymin"].clip(0, H - 1)
            df["ymax"] = df["ymax"].clip(0, H - 1)

            df["bbox_width"] = df["xmax"] - df["xmin"]
            df["bbox_height"] = df["ymax"] - df["ymin"]
            df["center_x"] = (df["xmin"] + df["xmax"]) / 2
            df["center_y"] = (df["ymin"] + df["ymax"]) / 2

            df["area"] = df["bbox_width"] * df["bbox_height"]

            df["center_x_norm"] = df["center_x"] / W
            df["center_y_norm"] = df["center_y"] / H
            df["xmin_norm"] = df["xmin"] / W
            df["xmax_norm"] = df["xmax"] / W
            df["ymin_norm"] = df["ymin"] / H
            df["ymax_norm"] = df["ymax"] / H
            df["area_norm"] = df["area"] / (W * H)
        else:
            df["bbox_width"] = np.nan
            df["bbox_height"] = np.nan
            df["center_x"] = np.nan
            df["center_y"] = np.nan
            df["area"] = np.nan

            df["center_x_norm"] = np.nan
            df["center_y_norm"] = np.nan
            df["xmin_norm"] = np.nan
            df["xmax_norm"] = np.nan
            df["ymin_norm"] = np.nan
            df["ymax_norm"] = np.nan
            df["area_norm"] = np.nan

        rows.append(df)

    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


# *이미지별 요약 생성 함수
def compute_image_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("filename")
        .agg(
            bbox_count=("class", "count"),  # *bbox 총 개수
            unique_classes=("class", pd.Series.nunique),  # *클래스 개수
            included_classes=("class", lambda x: ", ".join(sorted(set(x)))),
        )
        .reset_index()
    )


# *히트맵 관련 함수
def compute_heatmap_data(df: pd.DataFrame, grid_size: int = 5) -> pd.DataFrame:
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


# *바운딩박스 시각화
def draw_boxes(
    filename: str,
    gt_folder: str,
    img_folder: str,
    boxes: pd.DataFrame,
    visible_classes: Optional[List[str]] = None,
    duplicate: bool = False,
) -> Optional[str]:
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


# *gt/image check
def validate_paths(store) -> Tuple[Optional[str], Optional[str]]:
    """
    store-paths에서 gt, img 경로를 검증하여 반환합니다.
    둘 중 하나라도 없으면 (None, None)을 반환합니다.
    """
    gt_folder = store.get("gt") if store else None
    img_folder = store.get("img") if store else None
    if not gt_folder or not img_folder:
        return None, None
    return gt_folder, img_folder


# *pandas converting
def dict_to_df(df_dict) -> pd.DataFrame:
    """Convert dictionary to pandas DataFrame safely."""
    import pandas as pd

    if df_dict is None:
        return pd.DataFrame()
    return pd.DataFrame(df_dict)


# *흰색 빈 이미지
def empty_figure():
    fig = px.imshow(np.ones((10, 10, 3), dtype=np.uint8) * 255)
    fig.update_layout(
        annotations=[
            dict(
                text="표시할 이미지 없음",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=20, color="gray"),
                xanchor="center",
                yanchor="middle",
            )
        ],
        xaxis=dict(visible=False, scaleanchor="y"),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_showscale=False,
    )
    return fig


def extract_keywords_from_filename(filename: str) -> List[str]:
    """
    파일명에서 _ 로 분할된 키워드를 반환.
    - 확장자 제거
    - 마지막(-1) 또는 뒤에서 두 번째(-2) 세그먼트가 순수 숫자라면 제외
    - 8자리 날짜(yyyymmdd) 제외
    - 'nc'로 시작하고 뒤에 숫자가 붙은 패턴(nc123 등) 제외
    """
    base = filename.rsplit(".", 1)[0]
    parts = base.split("_")
    keywords = []
    n = len(parts)
    for idx, p in enumerate(parts):
        pl = p.lower()
        # 1) 마지막(-1) 또는 뒤에서 두 번째(-2) 세그먼트이고 완전 숫자라면 제외
        if idx in {n - 1, n - 2} and re.fullmatch(r"\d+", pl):
            continue
        # 2) 8자리 날짜 형태라면 제외
        if re.fullmatch(r"\d{8}", pl):
            continue
        # 3) nc로 시작하고 뒤에 숫자만 있는 경우 제외
        if re.fullmatch(r"nc\d+", pl):
            continue
        # 빈 문자열 아니면 포함
        if pl:
            keywords.append(pl)
    return keywords


from PIL import Image

# CLIP 모델 로딩 및 임베딩 추출 함수
import clip


def load_clip_model():
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    model.eval()  # ← 추가
    return model, preprocess, device


def get_image_embedding(image_path, model, preprocess, device):
    import torch

    img = Image.open(image_path).convert("RGB")  # ← 색공간 고정
    image = preprocess(img).unsqueeze(0).to(device)
    with torch.no_grad():
        feats = model.encode_image(image)
    return feats.cpu().numpy().flatten()


# 이미지 검사 부분
import hashlib


def compute_md5(path: str) -> str:
    """파일의 MD5 해시 계산"""
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def process_image_md5(path: str):
    """단일 이미지 MD5 계산"""
    try:
        md5 = compute_md5(path)
        return {"filename": os.path.basename(path), "md5": md5}
    except Exception:
        return None


def parallel_md5_compute(image_folder: str, max_workers: int = 8):
    """폴더 내 이미지들의 MD5 해시 병렬 계산"""
    files = [
        f
        for f in os.listdir(image_folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        futures = {
            exe.submit(process_image_md5, os.path.join(image_folder, f)): f
            for f in files
        }
        for fut in tqdm(
            as_completed(futures), total=len(futures), desc="Computing MD5"
        ):
            result = fut.result()
            if result:
                results.append(result)
    return results


def compare_images_md5(image_folder: str):
    """MD5 기반 완전 중복 탐지"""
    data = parallel_md5_compute(image_folder)
    results = []

    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            a, b = data[i], data[j]
            if a["md5"] == b["md5"]:
                results.append(
                    {
                        "image_a": a["filename"],
                        "image_b": b["filename"],
                        "note": "완전 중복",
                    }
                )

    print(f"[INFO] 완전 중복 {len(results)}건 탐지 완료")
    return sorted(results, key=lambda x: x["image_a"])


def scan_image_files(img_folder):
    IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp")
    image_files = []
    for root, _, files in os.walk(img_folder):
        for fn in files:
            if fn.lower().endswith(IMAGE_EXTS):
                image_files.append(os.path.join(root, fn))
    return image_files


def get_image_base64(filename: str, img_folder: str) -> str:
    image_path = os.path.join(img_folder, filename)
    img = imread_unicode(image_path)
    if img is None:
        return ""

    success, buffer = cv2.imencode(".jpg", img)
    if not success:
        return ""

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
