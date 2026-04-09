import os

import dash
import pandas as pd
from dash import Input, Output, State, html
from tabs.home import home_tab_layout
from utils.gt_utils import load_all_gt
from utils.image_utils import scan_image_files


def register_home_callbacks(app):

    # ! home(main) 화면에서 초기 세팅 콜백 => 완료
    @app.callback(
        Output("store-paths", "data"),
        Output("store-df-all", "data", allow_duplicate=True),
        Output("store-image-files", "data", allow_duplicate=True),
        Output("store-gt-files", "data", allow_duplicate=True),
        Output("main-content", "children", allow_duplicate=True),
        Input("main-run", "n_clicks"),
        State("main-gt-path", "value"),
        State("main-img-path", "value"),
        prevent_initial_call=True,
    )
    def on_run_click(n_clicks, gt_path, img_path):

        # =========================
        # IMAGE 경로 필수 체크
        # =========================
        if not img_path:
            warn = html.Div(
                "⚠ IMAGE 경로는 필수입니다.",
                style={"textAlign": "center", "color": "red", "marginTop": "20px"},
            )
            return (
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                html.Div([home_tab_layout({}), warn]),
            )

        if not os.path.exists(img_path):
            return (
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                html.Div(
                    f"❌ IMAGE 경로가 존재하지 않습니다: {img_path}",
                    style={"textAlign": "center", "color": "red", "marginTop": "100px"},
                ),
            )

        # =========================
        # IMAGE 파일 스캔 (항상)
        # =========================
        image_files = scan_image_files(img_path)
        image_names = [os.path.basename(p) for p in image_files]

        if not image_names:
            return (
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                html.Div(
                    "⚠ IMAGE 경로에 이미지 파일이 없습니다.",
                    style={"textAlign": "center", "color": "red", "marginTop": "100px"},
                ),
            )

        # =========================
        # 3️GT는 선택 사항
        # =========================
        df_all = None
        gt_files = []

        if gt_path and os.path.exists(gt_path):
            try:
                df_all = load_all_gt(gt_path, img_path)

                if isinstance(df_all, pd.DataFrame) and not df_all.empty:
                    required_cols = {
                        "filename",
                        "class",
                        "xmin",
                        "ymin",
                        "xmax",
                        "ymax",
                    }
                    if not required_cols.issubset(df_all.columns):
                        print("[WARN] GT 컬럼 누락 → GT 기능 비활성화")
                        df_all = None
                    else:
                        gt_files = [
                            os.path.splitext(f)[0]
                            for f in os.listdir(gt_path)
                            if f.lower().endswith(".txt")
                        ]
                else:
                    df_all = None

            except Exception as e:
                print(f"[WARN] GT 로딩 실패, 이미지 기능만 활성화: {e}")
                df_all = None

        # =========================
        # 4️store-paths 구성
        # =========================
        paths = {"img": img_path, "gt": gt_path}  # if df_all is not None else None

        # =========================
        # 5️안내 메시지
        # =========================
        msg_children = [
            html.H3("경로 설정 완료", style={"textAlign": "center", "color": "green"}),
            html.P(f"IMAGE: {img_path}", style={"textAlign": "center"}),
        ]

        if df_all is not None:
            msg_children.append(html.P(f"GT: {gt_path}", style={"textAlign": "center"}))
        else:
            msg_children.append(
                html.P(
                    "GT: 미설정 (이미지 기반 기능만 사용 가능)",
                    style={"textAlign": "center", "color": "#888"},
                )
            )

        msg_children.append(
            html.P(
                "왼쪽 메뉴에서 분석 탭을 선택하세요.", style={"textAlign": "center", "color": "#555"}
            )
        )

        msg = html.Div(msg_children)

        # =========================
        # 6️반환
        # =========================
        return (
            paths,
            df_all.to_dict("records") if df_all is not None else [],
            image_names,
            gt_files,
            msg,
        )

    # *home sidebar로 갈때 콜백 함수
    @app.callback(
        Output("main-content", "children", allow_duplicate=True),
        Output("store-paths", "data", allow_duplicate=True),  # 추가
        Input("btn-reset-paths", "n_clicks"),
        State("store-paths", "data"),
        prevent_initial_call=True,
    )
    def on_reset_paths(n_clicks, store_paths):
        if not n_clicks:
            raise dash.exceptions.PreventUpdate
        empty_paths = {}

        return (
            home_tab_layout(empty_paths, reset_mode=True),  # main-content
            empty_paths,  # store-paths
        )
