# callbacks/statistics.py
import os
import pandas as pd
import plotly.express as px
from PIL import Image


from dash import  Input, Output
from collections import Counter

from utils.common import validate_paths
from utils.image_utils import scan_image_files


def register_statistics_callbacks(app):

    # ! 통계 요약 탭
    @app.callback(
        Output("pie-chart", "figure"),
        Output("class-summary-table", "data"),
        Input("store-paths", "data"),
        Input("store-df-all", "data"),
    )
    def update_stats(store, df_all_dict):
        gt, img = validate_paths(store)
        if gt is None or img is None:
            return {}, []
        df = pd.DataFrame(df_all_dict)

        # pie
        class_count = df["class"].value_counts().reset_index()
        class_count.columns = ["class", "count"]
        class_count = class_count.sort_values("count", ascending=True)

        fig = px.bar(
            class_count,
            x="count",
            y="class",
            orientation="h",
            title="클래스별 바운딩박스 개수",
            text="count",
        )

        fig.update_traces(
            textposition="outside",
            marker=dict(line=dict(color="white", width=1)),
        )

        fig.update_layout(
            xaxis_title="개수",
            yaxis_title="클래스",
            margin=dict(l=40, r=20, t=50, b=40),
        )

        summary = (
            df.groupby("class")
            .agg(count=("class", "count"), image_count=("filename", pd.Series.nunique))
            .reset_index()
        )
        summary["avg_per_image"] = (summary["count"] / summary["image_count"]).round(2)
        summary["class_ratio_percent"] = (summary["count"] / len(df) * 100).round(2)
        data = summary.to_dict("records")
        return fig, data

    # ! 통계 요약 탭 파이차트 콜백
    @app.callback(
        Output("image-count-display", "children"),
        Output("resolution-pie", "figure"),
        Input("store-paths", "data"),
        Input("store-df-all", "data"),  # ← 인터페이스 유지 (의존은 안 함)
    )
    def update_image_stats(store, df_all_dict):

        # 경로 검증
        gt_folder, img_folder = validate_paths(store)
        if img_folder is None:
            return "총 이미지 수: 0 장", px.scatter(title="해상도 데이터 없음")

        # 이미지 파일 목록
        image_files = scan_image_files(img_folder)
        if not image_files:
            return "총 이미지 수: 0 장", px.scatter(title="해상도 데이터 없음")

        # 이미지 수
        n_images = len(image_files)

        # 해상도 계산 (이미지 기준)
        reso_counter = Counter()
        for img_path in image_files:
            try:
                with Image.open(img_path) as im:
                    w, h = im.size
                reso_counter[f"{w}x{h}"] += 1
            except Exception:
                # 손상 이미지 등은 스킵
                continue

        if not reso_counter:
            return f"총 이미지 수: {n_images} 장", px.scatter(title="해상도 데이터 없음")

        # DataFrame 변환
        reso_count = pd.DataFrame(
            reso_counter.items(), columns=["resolution", "count"]
        ).sort_values("count", ascending=False)

        # === 파이차트 생성 ===
        fig = px.pie(reso_count, names="resolution", values="count", title="이미지 해상도 분포")

        fig.update_traces(
            pull=0.01,
            marker=dict(line=dict(color="white", width=2)),
            textposition="outside",
            texttemplate="%{label}(WxH)<br>%{value}개<br>%{percent}",
        )

        fig.update_layout(
            height=450,
            margin=dict(t=100, b=40, l=40, r=40),
            legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
        )

        return f"총 이미지 수: {n_images} 장", fig

    # ! GT / IMAGE 정합성 파이차트
    @app.callback(
        Output("consistency-pie", "figure"),
        Input("store-image-files", "data"),
        Input("store-df-all", "data"),
        Input("store-gt-files", "data"),  # ★ GT 파일 목록
    )
    def update_consistency_pie(image_names, df_all_dict, gt_files):
        
        # 1. 이미지 기준 set
        image_set = {
            os.path.splitext(os.path.basename(f))[0] for f in (image_names or [])
        }

        # 2. GT 파일 기준 set (파일 존재 여부)
        gt_file_set = {
            os.path.splitext(os.path.basename(f))[0] for f in (gt_files or [])
        }

        # 3. bbox가 1개 이상 있는 GT set
        gt_bbox_set = set()
        if df_all_dict:
            df = pd.DataFrame(df_all_dict)
            if "filename" in df.columns:
                gt_bbox_set = {
                    os.path.splitext(os.path.basename(f))[0]
                    for f in df["filename"].unique()
                }

        # ===== 4분류 카운트 =====
        normal_cnt = len(image_set & gt_bbox_set)

        gt_file_missing_cnt = len(image_set - gt_file_set)

        gt_empty_cnt = len((gt_file_set - gt_bbox_set) & image_set)

        image_missing_cnt = len(gt_file_set - image_set)

        total = normal_cnt + gt_file_missing_cnt + gt_empty_cnt + image_missing_cnt

        if total == 0:
            return px.scatter(title="정합성 데이터 없음")

        df_consistency = pd.DataFrame(
            {
                "status": ["정상 매칭", "GT 파일 없음", "GT 비어있음", "이미지 없음"],
                "count": [
                    normal_cnt,
                    gt_file_missing_cnt,
                    gt_empty_cnt,
                    image_missing_cnt,
                ],
            }
        )

        fig = px.pie(
            df_consistency, names="status", values="count", title="GT / IMAGE 정합성 분포"
        )

        fig.update_traces(
            pull=0.01,
            textposition="outside",
            texttemplate="%{label}<br>%{value}개<br>%{percent}",
            marker=dict(
                line=dict(color="white", width=2),
                colors=[
                    "#2ecc71",  # 정상
                    "#f39c12",  # GT 파일 없음
                    "#e67e22",  # GT 비어있음
                    "#e74c3c",  # 이미지 없음
                ],
            ),
        )

        fig.update_layout(height=380)
        return fig
