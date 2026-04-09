
import os
import pandas as pd
import glob
import numpy as np
import re

from utils.image_utils import imread_unicode

# *GT 로딩 및 정규화
def load_all_gt(gt_folder: str, img_folder: str):

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
def compute_image_summary(df: pd.DataFrame):
    return (
        df.groupby("filename")
        .agg(
            bbox_count=("class", "count"),  # *bbox 총 개수
            unique_classes=("class", pd.Series.nunique),  # *클래스 개수
            included_classes=("class", lambda x: ", ".join(sorted(set(x)))),
        )
        .reset_index()
    )


def extract_keywords_from_filename(filename: str):
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