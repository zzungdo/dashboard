# callbacks/navigation.py

import dash
from callbacks.logger import send_tab_log
from dash import ctx, html
from dash.exceptions import PreventUpdate
from tabs.home import home_tab_layout
from tabs.image import image_tab_layout
from tabs.inspection import (gt_duplicate_tab_layout,
                            image_exact_duplicate_tab_layout,
                            image_feature_tab_layout)
from tabs.statistics import statistics_tab_layout
from tabs.visual import visual_tab_layout


def register_navigation_callbacks(app):
    @app.callback(
        dash.Output("main-content", "children"),
        dash.Input("btn-tab-home", "n_clicks"),
        dash.Input("btn-tab-visual-scatter", "n_clicks"),
        dash.Input("btn-tab-visual-heatmap", "n_clicks"),
        dash.Input("btn-tab-statistics", "n_clicks"),
        dash.Input("btn-tab-img", "n_clicks"),
        dash.Input("btn-tab-inspection-gt-duplicate", "n_clicks"),
        dash.Input("btn-tab-inspection-image-duplicate", "n_clicks"),
        dash.Input("btn-tab-inspection-image", "n_clicks"),
        dash.State("store-paths", "data"),
        prevent_initial_call=True,
    )
    def show_selected_tab(
        n_home,
        n_vs,
        n_vh,
        n_stat,
        n_img,
        n_insp_gt_dup,
        n_insp_img_dup,
        n_insp_img,
        store_paths,
    ):
        if not ctx.triggered:
            raise PreventUpdate

        btn_id = ctx.triggered_id

        # Home
        if btn_id == "btn-tab-home":
            send_tab_log("main", "tab-home")
            return home_tab_layout(store_paths)

        # 분석 시각화
        elif btn_id == "btn-tab-visual-scatter":
            send_tab_log("visual_sub", "subtab-scatter")
            return visual_tab_layout(default_subtab="subtab-scatter")

        elif btn_id == "btn-tab-visual-heatmap":
            send_tab_log("visual_sub", "subtab-heatmap")
            return visual_tab_layout(default_subtab="subtab-heatmap")

        # 통계 요약
        elif btn_id == "btn-tab-statistics":
            send_tab_log("main", "tab-statistics")
            return statistics_tab_layout()

        # 이미지 View
        elif btn_id == "btn-tab-img":
            send_tab_log("main", "tab-img")
            return image_tab_layout()

        # 데이터 검사
        elif btn_id == "btn-tab-inspection-gt-duplicate":
            send_tab_log("duplicate_sub", "subtab-gt-duplicate")
            return gt_duplicate_tab_layout()

        elif btn_id == "btn-tab-inspection-image-duplicate":
            send_tab_log("duplicate_sub", "subtab-image-duplicate")
            return image_exact_duplicate_tab_layout()

        elif btn_id == "btn-tab-inspection-image":
            send_tab_log("duplicate_sub", "subtab-image-feature")
            return image_feature_tab_layout()

        return html.Div(
            "왼쪽 메뉴에서 기능을 선택하세요.", style={"textAlign": "center", "marginTop": "100px"}
        )
