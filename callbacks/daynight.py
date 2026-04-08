# callbacks/daynight.py

import io
import os
import zipfile

import numpy as np
import pandas as pd
import plotly.express as px
import torch
import torch.nn.functional as F
from dash import Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate
from PIL import Image
from utils import get_image_thumbnail, scan_image_files

import clip

DAYNIGHT_CKPT = (
    r"D:\code\My_Dash\dashboard_v1.0.1\weight\best_openclip_scene_classifier.pt"
)


def load_daynight_clip_classifier(path):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    ckpt = torch.load(path, map_location=device)

    # 1️⃣ 모델명 매핑
    MODEL_NAME_MAP = {
        "ViT-L-14": "ViT-L/14",
        "ViT-L-14@336px": "ViT-L/14@336px",
        "ViT-B-32": "ViT-B/32",
        "ViT-B-16": "ViT-B/16",
    }

    raw_name = ckpt["model_name"]
    if raw_name not in MODEL_NAME_MAP:
        raise ValueError(f"Unsupported CLIP model name: {raw_name}")

    model_name = MODEL_NAME_MAP[raw_name]

    # 2️⃣ CLIP pretrained 로드 (🔥 state_dict 로드 안 함)
    model, preprocess = clip.load(model_name, device=device)
    model.eval()

    # 3️⃣ ckpt에서 필요한 정보만 사용
    class_to_idx = ckpt["class_to_idx"]
    class_prompts = ckpt["class_prompts"]

    return model, preprocess, class_to_idx, class_prompts, device


(
    dn_model,
    dn_preprocess,
    dn_class_to_idx,
    dn_class_prompts,
    dn_device,
) = load_daynight_clip_classifier(DAYNIGHT_CKPT)


def register_daynight_callbacks(app):

    # ! Day/Night 분류 결과 표시 콜백
    @app.callback(
        Output("daynight-scatter", "figure"),
        Input("btn-daynight-run", "n_clicks"),
        State("store-paths", "data"),
        prevent_initial_call=True,
    )
    def update_daynight_scatter(n_clicks, store_paths):

        if not store_paths:
            return px.scatter(title="경로가 설정되지 않았습니다")

        img_folder = store_paths.get("img")
        if not img_folder or not os.path.isdir(img_folder):
            return px.scatter(title="유효한 이미지 경로가 아닙니다")

        image_files = scan_image_files(img_folder)

        data = []
        for path in image_files:
            filename = os.path.basename(path)
            try:
                day_score, night_score = predict_daynight_clip(path)
                data.append(
                    {
                        "filename": filename,
                        "day_score": round(day_score, 3),
                        "night_score": round(night_score, 3),
                    }
                )
            except Exception as e:
                print(f"[ERROR] {filename}: {e}")

        if not data:
            return px.scatter(title="분류 가능한 이미지가 없습니다")

        df = pd.DataFrame(data)

        df["confidence"] = df["day_score"] - df["night_score"]
        df["strength"] = df[["day_score", "night_score"]].abs().max(axis=1)

        df["type"] = np.where(df["confidence"] > 0, "Day", "Night")

        # 시각화
        fig = px.scatter(
            df,
            x="confidence",
            y="strength",
            color="type",
            color_discrete_map={"Day": "#f1c40f", "Night": "#34495e"},
            custom_data=["filename"],
            hover_data={
                "filename": True,
                "type": True,
                "day_score": ":.3f",
                "night_score": ":.3f",
                "confidence": ":.3f",
            },
            title="Day / Night CLIP Similarity (confidence view)",
        )

        # day / night 경계
        fig.add_vline(x=0, line_dash="dash", line_color="gray")

        # 애매한 영역 (선택)
        fig.add_vrect(x0=-0.05, x1=0.05, fillcolor="gray", opacity=0.15, layer="below")

        fig.update_layout(
            # title={
            #     "text": "Day / Night CLIP Similarity (confidence view)",
            #     "x": 0.5,
            #     "xanchor": "center"
            # },
            title=None,
            xaxis_title="Confidence (day − night cosine similarity)",
            yaxis_title="Similarity strength",
            dragmode="select",
            clickmode="event+select",
            # 🔑 핵심
            margin=dict(l=40, r=20, t=50, b=40),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            autosize=True,
        )

        return fig

    @app.callback(
        Output("daynight-thumbnails", "children"),
        Output("daynight-selected-files", "data"),
        Input("daynight-scatter", "selectedData"),  # 다중 선택
        Input("daynight-scatter", "clickData"),  # 단일 선택
        State("store-paths", "data"),
        prevent_initial_call=True,
    )
    def show_daynight_thumbnails(selectedData, clickData, store_paths):
        if not store_paths:
            raise PreventUpdate

        img_folder = store_paths.get("img")
        if not img_folder:
            raise PreventUpdate

        filenames = []

        # ✅ 1순위: 다중 선택 (박스 / 라쏘)
        if selectedData and selectedData.get("points"):
            filenames = [
                p["customdata"][0] for p in selectedData["points"] if "customdata" in p
            ]

        # ✅ 2순위: 단일 클릭
        elif clickData and clickData.get("points"):
            filenames = [clickData["points"][0]["customdata"][0]]

        else:
            raise PreventUpdate

        if not filenames:
            return [], []

        thumbs = []
        for fn in filenames:
            thumbs.append(
                html.Img(
                    src=get_image_thumbnail(fn, img_folder),
                    id={"type": "daynight-thumb", "index": fn},
                    n_clicks=0,
                    style={
                        "width": "120px",
                        "height": "120px",
                        "margin": "4px",
                        "cursor": "pointer",
                        "borderRadius": "4px",
                    },
                )
            )

        return thumbs, filenames

    def predict_daynight_clip(image_path):
        img = (
            dn_preprocess(Image.open(image_path).convert("RGB"))
            .unsqueeze(0)
            .to(dn_device)
        )

        with torch.no_grad():
            img_feat = dn_model.encode_image(img)
            img_feat = F.normalize(img_feat, dim=-1)

            text_tokens = clip.tokenize(dn_class_prompts).to(dn_device)
            text_feat = dn_model.encode_text(text_tokens)
            text_feat = F.normalize(text_feat, dim=-1)

            sims = (img_feat @ text_feat.T).cpu().numpy()[0]

        day_score = float(sims[dn_class_to_idx["day"]])
        night_score = float(sims[dn_class_to_idx["night"]])

        return day_score, night_score

    @app.callback(
        Output("download-daynight-zip", "data"),
        Input("btn-daynight-download", "n_clicks"),
        State("daynight-selected-files", "data"),
        State("store-paths", "data"),
        prevent_initial_call=True,
    )
    def download_selected_daynight_files(n_clicks, filenames, store_paths):

        if not filenames or not store_paths:
            raise PreventUpdate

        img_folder = store_paths.get("img")
        if not img_folder:
            raise PreventUpdate

        # 🔹 zip 파일 메모리 생성
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for fn in filenames:
                full_path = os.path.join(img_folder, fn)
                if os.path.isfile(full_path):
                    zf.write(full_path, arcname=fn)

        zip_buffer.seek(0)

        return dcc.send_bytes(
            zip_buffer.read(), filename="daynight_selected_images.zip"
        )
