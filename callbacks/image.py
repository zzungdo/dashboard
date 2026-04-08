# callbacks/image.py

import os

import cv2
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import ALL, Input, Output, State, ctx, html
from dash.exceptions import PreventUpdate
from PIL import Image
from utils import (
    dict_to_df,
    draw_boxes,
    draw_boxes_duplicate,
    empty_figure,
    get_image_base64,
    imread_unicode,
    validate_paths,
)


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
        Output("image-preview", "figure", allow_duplicate=True),
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
