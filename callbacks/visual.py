import os

import dash
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import ALL, Input, Output, State, ctx, html
from utils.common import dict_to_df, empty_figure, validate_paths
from utils.image_utils import draw_boxes, get_image_thumbnail, imread_unicode

def register_visual_callbacks(app):
    # !산점도 콜백
    @app.callback(
        Output("center-scatter", "figure"),
        Input("store-paths", "data"),
        Input("store-df-all", "data"),
        Input("scatter-width-range", "value"),
        Input("scatter-height-range", "value"),
    )
    def update_center_scatter(store, df_all_dict, width_range, height_range):

        gt_folder, img_folder = validate_paths(store)
        if gt_folder is None or img_folder is None:
            return dash.no_update

        df_all = dict_to_df(df_all_dict)
        if df_all.empty:
            return px.scatter(title="데이터 없음")

        # RangeSlider 안전 처리
        # width_range = [0, df_all["bbox_width"].max()]
        # height_range = [0, df_all["bbox_height"].max()]

        if not width_range:
            width_range = [0, float(df_all["bbox_width"].max())]
        if not height_range:
            height_range = [0, float(df_all["bbox_height"].max())]

        min_w, max_w = width_range
        min_h, max_h = height_range

        # 필터 적용
        df_filtered = df_all[
            (df_all["bbox_width"] >= min_w)
            & (df_all["bbox_width"] <= max_w)
            & (df_all["bbox_height"] >= min_h)
            & (df_all["bbox_height"] <= max_h)
        ]

        if df_filtered.empty:
            return px.scatter(
                title=f"선택한 범위 내 바운딩박스 없음 (W={width_range}, H={height_range})"
            )

        # 산점도 생성
        fig = px.scatter(
            df_filtered,
            x="bbox_width",
            y="bbox_height",
            color="class",
            hover_data=["filename", "class"],
            custom_data=["filename"],  # 반드시 추가해야 clickData에서 filename 접근 가능
            title=f"BBox Width vs Height 산점도 (W={width_range}, H={height_range})",
        )
        fig.update_traces(marker=dict(size=8), selector=dict(mode="markers"))
        fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), height=600)

        return fig

    # === 산점도 포인트 클릭 → 하단 패널에 바운딩박스 포함 이미지 표시 ===
    @app.callback(
        Output("scatter-preview", "figure"),
        Input("center-scatter", "clickData"),
        State("store-paths", "data"),
        State("store-df-all", "data"),
        prevent_initial_call=True,
    )
    def show_scatter_preview(clickData, store_paths, df_all_dict):
        """산점도 포인트 클릭 시 하단 패널에 선택된 클래스의 바운딩박스를 포함한 이미지 표시"""
        if not clickData or not store_paths or not df_all_dict:
            raise dash.exceptions.PreventUpdate

        gt_folder, img_folder = validate_paths(store_paths)
        if gt_folder is None or img_folder is None:
            return empty_figure()

        df_all = dict_to_df(df_all_dict)
        if df_all.empty:
            return empty_figure()

        try:
            fn = clickData["points"][0]["customdata"][0]
            w = clickData["points"][0]["x"]
            h = clickData["points"][0]["y"]
        except Exception:
            return empty_figure()

        # 클릭된 bbox 탐색
        matched = df_all[
            (df_all["filename"] == fn)
            & (df_all["bbox_width"] == w)
            & (df_all["bbox_height"] == h)
        ]
        if matched.empty:
            return empty_figure()

        # 선택된 bbox 하나만 시각화
        selected_class = matched.iloc[0]["class"]

        # === draw_boxes()로 bbox 포함된 이미지 base64 생성 ===
        encoded_img = draw_boxes(fn, gt_folder, img_folder, matched)

        if "image_exists" in matched.columns and not matched.iloc[0]["image_exists"]:
            return empty_figure()

        # 실제 이미지 크기 가져오기
        image_path = os.path.join(img_folder, fn)
        image = imread_unicode(image_path)
        if image is None:
            return empty_figure()
        img_h, img_w = image.shape[:2]

        # === base64 → Plotly 이미지 표시 ===
        fig = go.Figure()

        #  실제 픽셀 좌표계 사용
        fig.add_layout_image(
            dict(
                source=encoded_img,
                xref="x",  # paper → x
                yref="y",  # paper → y
                x=0,
                y=img_h,  # y축은 top에서 시작
                sizex=img_w,
                sizey=img_h,
                xanchor="left",
                yanchor="top",
                layer="below",
            )
        )

        # === 확대 가능하게 설정 ===
        fig.update_layout(
            title=f"{fn} - 클래스: {selected_class}",
            xaxis=dict(
                visible=False,
                range=[0, img_w],
                constrain="domain",
                scaleanchor="y",
                scaleratio=1,
            ),
            yaxis=dict(
                visible=False,
                range=[0, img_h],
                autorange="reversed",  #  y축 반전 (이미지 위→아래)
            ),
            dragmode="pan",  #  드래그 줌 활성화
            margin=dict(l=0, r=0, t=40, b=0),
            autosize=True,
            coloraxis_showscale=False,
        )
        return fig

    # ! 히트맵 시각화 콜백
    @app.callback(
        Output("heatmap", "figure"),
        Input("store-paths", "data"),
        Input("store-df-all", "data"),
        Input("heatmap-class-filter", "value"),
        Input("heatmap-grid-size", "value"),
    )
    def update_heatmap(store, df_all_dict, selected_class, grid_size):
        gt_folder, img_folder = validate_paths(store)
        if gt_folder is None or img_folder is None:
            return dash.no_update

        df_all = dict_to_df(df_all_dict)

        # 클래스 필터
        df = (
            df_all
            if selected_class == "All"
            else df_all[df_all["class"] == selected_class]
        )
        df = df.dropna(subset=["center_x_norm", "center_y_norm"])

        # 중심점 기준으로 그리드 인덱스 계산
        df["grid_x"] = (
            (df["center_x_norm"] * grid_size).astype(int).clip(0, grid_size - 1)
        )
        df["grid_y"] = (
            (df["center_y_norm"] * grid_size).astype(int).clip(0, grid_size - 1)
        )

        # 셀별 count
        data = df.groupby(["grid_x", "grid_y"]).size().reset_index(name="box_count")

        if data.empty:
            return px.imshow(np.zeros((10, 10)), title="히트맵 데이터 없음")

        # 퍼센트 배열 (히트맵 형태로 reshape)
        total = data["box_count"].sum()
        data["percent"] = (data["box_count"] / total * 100).round(2)

        percent_matrix = np.full((grid_size, grid_size), "", dtype=object)
        heatmap_matrix = np.zeros((grid_size, grid_size))

        for _, row in data.iterrows():
            x, y = int(row["grid_x"]), int(row["grid_y"])
            heatmap_matrix[y, x] = row["box_count"]
            percent_matrix[y, x] = f"{row['percent']}%"

        # 히트맵 생성
        fig = go.Figure(
            data=go.Heatmap(
                x=list(range(grid_size)),  #  추가
                y=list(range(grid_size)),  #  추가
                z=heatmap_matrix,
                text=percent_matrix,
                texttemplate=" %{z} (%{text})",
                textfont={"size": 12, "color": "black"},
                colorscale="RdBu",
                reversescale=True,
                colorbar=dict(title="box_count"),
                customdata=percent_matrix,
                hovertemplate=" %{z} bboxes<br> %{customdata} of total<extra></extra>",
            )
        )

        fig.update_layout(
            title=f"히트맵 (중심점 기반): {selected_class}",
            margin=dict(l=40, r=40, t=50, b=40),
            height=None,  #  고정 높이 해제
            autosize=True,  #  Plotly가 자동으로 맞춤
        )

        fig.update_xaxes(
            title="grid_x",
            range=[-0.5, grid_size - 0.5],
            constrain="domain",
            tickmode="linear",
            dtick=1,
        )
        fig.update_yaxes(
            title="grid_y",
            range=[grid_size - 0.5, -0.5],
            constrain="domain",
            tickmode="linear",
            dtick=1,
        )
        return fig

    # ! 썸네일 표시 콜백
    @app.callback(
        Output("thumbnail-gallery", "children"),
        Input("store-paths", "data"),
        Input("store-df-all", "data"),
        Input("heatmap", "clickData"),
        State("heatmap-class-filter", "value"),
        State("heatmap-grid-size", "value"),
        prevent_initial_call=True,
    )
    def show_thumbnails(store, df_all_dict, heatmapClick, sel_class, grid_size):
        """히트맵 클릭 시 해당 영역의 이미지 썸네일 표시"""
        _, img_folder = validate_paths(store)
        if not img_folder or not heatmapClick:
            return []

        df_all = dict_to_df(df_all_dict)
        gx = int(heatmapClick["points"][0]["x"])
        gy = int(heatmapClick["points"][0]["y"])
        df = df_all if sel_class == "All" else df_all[df_all["class"] == sel_class]
        x0, x1 = gx / grid_size, (gx + 1) / grid_size
        y0, y1 = gy / grid_size, (gy + 1) / grid_size

        matched = df[
            (df["center_x_norm"] >= x0)
            & (df["center_x_norm"] < x1)
            & (df["center_y_norm"] >= y0)
            & (df["center_y_norm"] < y1)
        ]["filename"].unique()

        return [
            html.Img(
                src=get_image_thumbnail(fname, img_folder),
                id={"type": "heatmap-thumb", "index": fname},
                n_clicks=0,
                style={
                    "cursor": "pointer",
                    "margin": "4px",
                    "border": "2px solid #ccc",
                    "borderRadius": "4px",
                },
            )
            for fname in matched
        ]

    # ! 히트맵 썸네일 클릭 → 하단 패널에 전체 이미지 표시
    @app.callback(
        Output("heatmap-preview", "figure"),
        Input({"type": "heatmap-thumb", "index": ALL}, "n_clicks"),
        State("store-paths", "data"),
        State("store-df-all", "data"),
        State({"type": "heatmap-thumb", "index": ALL}, "id"),
        State("heatmap", "clickData"),
        State("heatmap-class-filter", "value"),
        State("heatmap-grid-size", "value"),
        prevent_initial_call=True,
    )
    def show_heatmap_preview(
        n_clicks, store_paths, df_all_dict, ids, heatmap_click, sel_class, grid_size
    ):
        """히트맵 썸네일 클릭 시 하단 패널에 전체 이미지와 해당 영역의 바운딩박스 표시"""
        if not ctx.triggered or not store_paths or not df_all_dict:
            raise dash.exceptions.PreventUpdate

        # 클릭된 썸네일 찾기
        trigger = ctx.triggered_id
        if not isinstance(trigger, dict) or trigger.get("type") != "heatmap-thumb":
            raise dash.exceptions.PreventUpdate

        filename = trigger.get("index")
        if not filename:
            return empty_figure()

        gt_folder, img_folder = validate_paths(store_paths)
        if gt_folder is None or img_folder is None:
            return empty_figure()

        df_all = dict_to_df(df_all_dict)
        if df_all.empty:
            return empty_figure()

        # 히트맵에서 클릭된 영역의 bbox만 필터링
        if heatmap_click and "points" in heatmap_click:
            gx = int(heatmap_click["points"][0]["x"])
            gy = int(heatmap_click["points"][0]["y"])
            x0, x1 = gx / grid_size, (gx + 1) / grid_size
            y0, y1 = gy / grid_size, (gy + 1) / grid_size

            df = df_all if sel_class == "All" else df_all[df_all["class"] == sel_class]
            boxes = df[
                (df["filename"] == filename)
                & (df["center_x_norm"] >= x0)
                & (df["center_x_norm"] < x1)
                & (df["center_y_norm"] >= y0)
                & (df["center_y_norm"] < y1)
            ]
        else:
            # 히트맵 클릭 정보가 없으면 해당 이미지의 모든 bbox 표시
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

        #  실제 픽셀 좌표 사용
        fig.add_layout_image(
            dict(
                source=encoded_img,
                xref="x",  # 축 좌표 사용
                yref="y",
                x=0,
                y=img_h,  # 이미지 top
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
        fig.update_yaxes(
            visible=False, range=[0, img_h], autorange="reversed"  #  y축 반전 (이미지 위→아래)
        )

        fig.update_layout(
            title=f"📸 {filename} ({len(boxes)} BBox)",
            dragmode="pan",  #  드래그 줌 가능
            margin=dict(l=0, r=0, t=40, b=0),
            autosize=True,
            coloraxis_showscale=False,
        )

        return fig

    # !히트맵에서 드롭다운 콜백
    @app.callback(
        Output("heatmap-class-filter", "options"),
        Input("store-paths", "data"),
        Input("store-df-all", "data"),
    )
    def update_heatmap_class_options(store, df_all_dict):
        gt_folder, img_folder = validate_paths(store)
        if gt_folder is None or img_folder is None:
            return [{"label": "All", "value": "All"}]

        df_all = dict_to_df(df_all_dict)
        classes = sorted(df_all["class"].unique())
        return [{"label": "All", "value": "All"}] + [
            {"label": c, "value": c} for c in classes
        ]
