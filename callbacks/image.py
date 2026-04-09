# callbacks/image.py

import os
import math
import pandas as pd

import cv2
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import ALL, Input, Output, State, ctx, html
from dash.exceptions import PreventUpdate
from PIL import Image
from utils.gt_utils import compute_image_summary, extract_keywords_from_filename
from utils.image_utils import (
    get_image_thumbnail,
    draw_boxes,
    draw_boxes_duplicate,
    get_image_base64,
    imread_unicode,
)
from utils.common import dict_to_df, empty_figure, validate_paths


def register_image_callbacks(app):

    # !  완전 중복 테이블 클릭 시 이미지 표시 콜백
    @app.callback(
        Output("imgblend-display", "figure", allow_duplicate=True),
        Output("imgblend-selected-filenames", "children", allow_duplicate=True),
        Input("image-exact-table", "active_cell"),
        State("image-exact-table", "data"),
        # State('input-img-path', 'value'),
        State("store-paths", "data"),
        prevent_initial_call=True,
    )
    def show_exact_duplicate_images(active_cell, table_data, store_paths):

        if not active_cell or not table_data or not store_paths:
            raise PreventUpdate

        img_folder = store_paths.get("img")
        if not img_folder:
            raise PreventUpdate

        row = table_data[active_cell["row"]]
        path_a = os.path.join(img_folder, row["image_a"])
        path_b = os.path.join(img_folder, row["image_b"])

        def safe_load(path):
            if os.path.exists(path):
                try:
                    img = Image.open(path).convert("RGB")
                    return np.array(img)
                except:
                    return np.zeros((100, 100, 3), dtype=np.uint8)
            return np.zeros((100, 100, 3), dtype=np.uint8)

        img_a, img_b = safe_load(path_a), safe_load(path_b)
        gap = 80
        h, w = (
            max(img_a.shape[0], img_b.shape[0]),
            img_a.shape[1] + gap + img_b.shape[1],
        )

        canvas = np.ones((h, w, 3), dtype=np.uint8) * 255
        canvas[: img_a.shape[0], : img_a.shape[1]] = img_a
        canvas[
            : img_b.shape[0],
            img_a.shape[1] + gap : img_a.shape[1] + gap + img_b.shape[1],
        ] = img_b

        fig = px.imshow(canvas)
        fig.update_layout(
            title="완전 중복 이미지 비교",
            title_x=0.5,
            height=700,
            margin=dict(l=0, r=0, t=60, b=0),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig, f"A: {row['image_a']}  |  B: {row['image_b']}"

    # ! 이미지 완전 중복탭에서 블렌딩 버튼 눌렀을 때 ---
    @app.callback(
        Output("imgblend-display", "figure", allow_duplicate=True),
        Output("btn-show-blend", "children"),
        Output("store-blend-mode", "data"),
        Input("btn-show-blend", "n_clicks"),
        State("store-blend-mode", "data"),
        State("image-exact-table", "active_cell"),
        State("image-exact-table", "data"),
        State("store-paths", "data"),
        prevent_initial_call=True,
    )
    def toggle_blend_mode(n_clicks, blend_mode, active_cell, table_data, store_paths):

        if not store_paths:
            raise PreventUpdate

        img_folder = store_paths.get("img")

        row = table_data[active_cell["row"]]
        path_a = os.path.join(img_folder, row["image_a"])
        path_b = os.path.join(img_folder, row["image_b"])

        if not (os.path.exists(path_a) and os.path.exists(path_b)):
            raise PreventUpdate

        imgA = np.array(Image.open(path_a).convert("RGB"))
        imgB = np.array(Image.open(path_b).convert("RGB"))
        h = min(imgA.shape[0], imgB.shape[0])
        w = min(imgA.shape[1], imgB.shape[1])
        imgA = cv2.resize(imgA, (w, h))
        imgB = cv2.resize(imgB, (w, h))

        # --- 토글 로직 ---
        if not blend_mode:
            # 블렌딩 보기
            blended = cv2.addWeighted(imgA, 0.5, imgB, 0.5, 0)
            fig = px.imshow(blended)
            fig.update_layout(
                title="이미지 블렌딩 (A/B 50:50)",
                title_x=0.5,
                margin=dict(l=0, r=0, t=50, b=0),
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
            )
            return fig, "블렌딩 취소", True
        else:
            # 블렌딩 취소 → 원본 비교로 복귀
            gap = 80
            h2 = max(imgA.shape[0], imgB.shape[0])
            w2 = imgA.shape[1] + gap + imgB.shape[1]
            canvas = np.ones((h2, w2, 3), dtype=np.uint8) * 255
            canvas[: imgA.shape[0], : imgA.shape[1]] = imgA
            canvas[
                : imgB.shape[0],
                imgA.shape[1] + gap : imgA.shape[1] + gap + imgB.shape[1],
            ] = imgB

            fig = px.imshow(canvas)
            fig.update_layout(
                title="완전 중복 이미지 비교",
                title_x=0.5,
                margin=dict(l=0, r=0, t=50, b=0),
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
            )
            return fig, "블렌딩 보기", False

    @app.callback(
        Output("daynight-full-image", "children"),
        Input({"type": "daynight-thumb", "index": ALL}, "n_clicks"),
        State({"type": "daynight-thumb", "index": ALL}, "id"),
        State("store-paths", "data"),
        prevent_initial_call=True,
    )
    def show_daynight_full_image(n_clicks, ids, store_paths):
        if not ctx.triggered or not store_paths:
            raise PreventUpdate

        trigger = ctx.triggered_id
        if not isinstance(trigger, dict):
            raise PreventUpdate

        filename = trigger.get("index")
        if not filename:
            raise PreventUpdate

        img_folder = store_paths.get("img")
        if not img_folder:
            raise PreventUpdate

        return html.Div(
            [
                html.Div(
                    html.Img(
                        src=get_image_base64(filename, img_folder),
                        style={
                            "maxWidth": "100%",
                            "maxHeight": "100%",
                            "objectFit": "contain",
                        },
                    ),
                    style={
                        "width": "100%",
                        "flex": "1",
                        "display": "flex",
                        "alignItems": "flex-start",  # center
                        "justifyContent": "flex-start",  # center
                        "border": "1px solid #ddd",
                    },
                ),
                html.H5(filename, style={"textAlign": "center", "fontSize": "14px"}),
            ],
            style={
                "display": "flex",
                "flexDirection": "column",
                "height": "100%",  # 부모 기준
            },
        )

    @app.callback(
        #Output("image-preview", "figure", allow_duplicate=True),
        Output("duplicate-image-preview", "figure", allow_duplicate=True),
        Input("duplicate-table", "active_cell"),
        State("duplicate-table", "data"),
        State("store-paths", "data"),
        State("store-df-all", "data"),
        prevent_initial_call=True,
    )
    def show_gt_duplicate_preview(active_cell, table_data, store_paths, df_all_dict):

        if not active_cell or not table_data:
            raise PreventUpdate

        row = table_data[active_cell["row"]]
        filename = row["filename"]
        line_a = row["line_a"] - 1
        line_b = row["line_b"] - 1

        gt_folder, img_folder = validate_paths(store_paths)
        if gt_folder is None or img_folder is None:
            return empty_figure()

        df_all = dict_to_df(df_all_dict)
        df_img = df_all[df_all["filename"] == filename].reset_index(drop=True)

        if line_a >= len(df_img) or line_b >= len(df_img):
            return empty_figure()

        # 중복된 두 GT만 전달
        matched = df_img.loc[[line_a, line_b]]

        if "image_exists" in matched.columns and not matched.iloc[0]["image_exists"]:
            return empty_figure()

        encoded_img = draw_boxes_duplicate(filename, gt_folder, img_folder, matched)

        image = imread_unicode(os.path.join(img_folder, filename))
        if image is None:
            return empty_figure()
        img_h, img_w = image.shape[:2]

        fig = go.Figure()
        fig.add_layout_image(
            dict(
                source=encoded_img,
                xref="x",
                yref="y",
                x=0,
                y=img_h,
                sizex=img_w,
                sizey=img_h,
                xanchor="left",
                yanchor="top",
                layer="below",
            )
        )

        fig.update_layout(
            title=f"{filename} — 중복 GT 비교",
            xaxis=dict(
                visible=False,
                range=[0, img_w],
                constrain="domain",
                scaleanchor="y",
                scaleratio=1,
            ),
            yaxis=dict(visible=False, range=[0, img_h], autorange="reversed"),
            dragmode="pan",
            margin=dict(l=0, r=0, t=40, b=0),
            autosize=True,
        )

        return fig

    # ! GT 분석
    @app.callback(
        Output("summary-table", "data"),
        Input("store-paths", "data"),
        Input("store-df-all", "data"),
    )
    def update_summary_table(store, df_all_dict):

        gt_folder, img_folder = validate_paths(store)
        if gt_folder is None or img_folder is None:
            return []

        # 전체 GT 불러오기
        df_all = dict_to_df(df_all_dict)

        # 이미지별 요약 생성
        df_summary = compute_image_summary(df_all)
        df_summary["_idx"] = range(1, len(df_summary) + 1)
        # DataTable에 들어갈 dict 리스트로 변환
        return df_summary.to_dict("records")

    # ! 통계 요약탭에서 사용하는 콜백
    @app.callback(
        Output("keyword-count-display", "children"),
        Input("btn-keyword-search", "n_clicks"),
        State("keyword-dropdown", "value"),
        State("store-df-all", "data"),
        prevent_initial_call=True,
    )
    def update_keyword_count(n_clicks, keyword, df_all_dict):
        if not keyword or not df_all_dict:
            return ""
        df = pd.DataFrame(df_all_dict)
        files = df["filename"].unique()
        matched = [
            fn for fn in files if keyword.lower() in extract_keywords_from_filename(fn)
        ]
        return f"'{keyword}' 키워드 포함 이미지: {len(matched)} 장"

    # ! 통계 요약탭에서 키워드 드롭다운으로 표시 콜백
    @app.callback(Output("keyword-dropdown", "options"), Input("store-df-all", "data"))
    def update_keyword_options(df_all_dict):
        if not df_all_dict:
            return []
        df = pd.DataFrame(df_all_dict)
        all_files = df["filename"].unique()
        keywords = set()
        for fn in all_files:
            keywords.update(extract_keywords_from_filename(fn))
        # label 은 대문자, value 는 원본 소문자
        return [{"label": kw.upper(), "value": kw} for kw in sorted(keywords)]



    # ! 통계 요약탭에서 검색 기능 구현한 콜백
    @app.callback(
        Output("keyword-matched", "data"),
        Output("keyword-page", "data"),
        Output("keyword-thumbnail-gallery", "children"),
        Output("keyword-prev", "disabled"),
        Output("keyword-next", "disabled"),
        Output("keyword-page-display", "children"),
        Input("btn-keyword-search", "n_clicks"),
        Input("keyword-prev", "n_clicks"),
        Input("keyword-next", "n_clicks"),
        State("keyword-dropdown", "value"),
        State("store-paths", "data"),
        State("store-df-all", "data"),
        State("keyword-matched", "data"),
        State("keyword-page", "data"),
        prevent_initial_call=True,
    )
    def on_keyword_control(
        search_click, prev_click, next_click, keyword, store, df_all_dict, matched, page
    ):
        ctx_id = ctx.triggered_id

        gt_folder, img_folder = validate_paths(store)
        if gt_folder is None or img_folder is None or not keyword:
            return [], 0, [], True, True, ""

        # 2) 검색 버튼 눌렀을 때: 매칭 리스트 재생성
        if ctx_id == "btn-keyword-search":
            df = pd.DataFrame(df_all_dict)
            files = df["filename"].unique()
            matched = [
                fn
                for fn in files
                if keyword.lower() in extract_keywords_from_filename(fn)
            ]
            page = 0

        # 3) 페이지 이동 버튼 눌렀을 때
        elif ctx_id == "keyword-prev" and page > 0:
            page -= 1
        elif ctx_id == "keyword-next":
            max_page = (len(matched) - 1) // 28
            page = min(page + 1, max_page)

        # 4) 썸네일 슬라이스
        page_size = 28
        start = page * page_size
        end = start + page_size
        slice_fns = matched[start:end]

        thumbs = []
        for fn in slice_fns:
            thumbs.append(
                html.Div(
                    html.Img(
                        src=get_image_thumbnail(fn, img_folder),
                        style={"width": "100%", "height": "100%", "display": "block"},
                    ),
                    id={"type": "thumb", "index": fn},
                    n_clicks=0,
                    style={
                        "cursor": "pointer",
                        "display": "inline-block",
                        "width": "120px",
                        "height": "120px",
                        "margin": "4px",
                        "border": "2px solid #ccc",
                        "borderRadius": "4px",
                        "overflow": "hidden",
                    },
                )
            )

        # 5) 버튼 활성/비활성, 페이지 표시
        prev_disabled = page == 0
        next_disabled = end >= len(matched)
        display = f"{page+1} / {math.ceil(len(matched)/page_size)}"

        return matched, page, thumbs, prev_disabled, next_disabled, display


    # === 이미지 View 탭 테이블 클릭 또는 키워드 썸네일 클릭 → 이미지 표시 ===
    @app.callback(
        Output("image-preview", "figure"),
        Input("summary-table", "active_cell"),
        Input({"type": "thumb", "index": ALL}, "n_clicks"),
        State("summary-table", "data"),
        State("summary-table", "page_current"),
        State("summary-table", "page_size"),
        State({"type": "thumb", "index": ALL}, "id"),
        State("store-paths", "data"),
        State("store-df-all", "data"),
        prevent_initial_call=True,
    )
    def show_image_preview_from_table_or_thumb(
        active_cell,
        thumb_clicks,
        table_data,
        page_current,
        page_size,
        thumb_ids,
        store_paths,
        df_all_dict,
    ):
        """이미지 View 탭에서 테이블 행 클릭 또는 키워드 썸네일 클릭 시 해당 이미지와 바운딩박스 표시"""
        if not ctx.triggered or not store_paths or not df_all_dict:
            raise PreventUpdate

        # === 트리거 체크 ===
        trigger = ctx.triggered_id
        filename = None

        # 1) 썸네일 클릭
        if isinstance(trigger, dict) and trigger.get("type") == "thumb":
            filename = trigger.get("index")

        # 2) 테이블 클릭
        elif trigger == "summary-table" and active_cell and table_data:
            row_idx = active_cell["row"]
            global_idx = page_current * page_size + row_idx
            if global_idx < len(table_data):
                filename = table_data[global_idx]["filename"]

        if not filename:
            raise PreventUpdate

        gt_folder, img_folder = validate_paths(store_paths)
        if gt_folder is None or img_folder is None:
            return empty_figure()

        df_all = dict_to_df(df_all_dict)
        if df_all.empty:
            return empty_figure()

        # 해당 이미지의 모든 bbox 가져오기
        boxes = df_all[df_all["filename"] == filename]

        if boxes.empty:
            return empty_figure()

        # === draw_boxes()로 bbox 포함된 이미지 base64 생성 ===
        if "image_exists" in boxes.columns and not boxes.iloc[0]["image_exists"]:
            return empty_figure()

        encoded_img = draw_boxes(filename, gt_folder, img_folder, boxes)
        if not encoded_img:
            return empty_figure()

        # 실제 이미지 크기 가져오기
        image_path = os.path.join(img_folder, filename)
        image = imread_unicode(image_path)
        if image is None:
            return empty_figure()
        img_h, img_w = image.shape[:2]

        # === base64 → Plotly 이미지 표시 ===
        fig = go.Figure()

        # 실제 픽셀 좌표 사용
        fig.add_layout_image(
            dict(
                source=encoded_img,
                xref="x",
                yref="y",
                x=0,
                y=img_h,
                sizex=img_w,
                sizey=img_h,
                xanchor="left",
                yanchor="top",
                layer="below",
            )
        )

        # === 축 및 줌 설정 ===
        fig.update_xaxes(
            visible=False,
            range=[0, img_w],
            constrain="domain",
            scaleanchor="y",
            scaleratio=1,
        )
        fig.update_yaxes(visible=False, range=[0, img_h], autorange="reversed")

        fig.update_layout(
            title=f"📸 {filename} ({len(boxes)} BBox)",
            dragmode="pan",
            margin=dict(l=0, r=0, t=40, b=0),
            autosize=True,
            coloraxis_showscale=False,
        )

        return fig