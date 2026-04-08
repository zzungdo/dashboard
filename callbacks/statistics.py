# callbacks/statistics.py

import math
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import ALL, Input, Output, State, ctx, html
from dash.exceptions import PreventUpdate
from utils import (
    compute_image_summary,
    dict_to_df,
    draw_boxes,
    empty_figure,
    extract_keywords_from_filename,
    get_image_thumbnail,
    imread_unicode,
    scan_image_files,
    validate_paths,
)


def register_statistics_callbacks(app):

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

        fig = px.pie(
            class_count, names="class", values="count", title="전체 바운딩박스에서 클래스별 비율"
        )

        fig.update_traces(
            pull=0.01,  # 모든 슬라이스를 1% 만큼 당김
            marker=dict(line=dict(color="white", width=2)),
            textposition="outside",  # 레이블을 바깥으로
            # textinfo='label+percent',            # 레이블에 클래스명+퍼센트 표시
            texttemplate="%{label}<br>%{value}개<br>%{percent}",  # ← 원하는 형식 지정
            automargin=True,  # 바깥 레이블이 잘려 나가지 않도록
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
        from collections import Counter

        import pandas as pd
        import plotly.express as px
        from PIL import Image

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
            height=500,
            margin=dict(t=60, b=40, l=40, r=40),
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
        import os

        import pandas as pd
        import plotly.express as px

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
