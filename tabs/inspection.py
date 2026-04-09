# tab_inspection.py
from dash import dash_table, dcc, html
from dash.dcc import Loading


def make_marks(start: int, end: int, step: int):
    return {i: str(i) for i in range(start, end + 1, step)}


def gt_duplicate_tab_layout():
    """GT 중복 검사 탭 레이아웃 (image-preview 재사용 구조)"""

    return html.Div(
        [
            # =========================
            # 1. 타이틀
            # =========================
            html.H4("GT 중복 바운딩박스 검사", style={"marginBottom": "20px"}),
            # =========================
            # 2. 옵션 영역
            # =========================
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("중복 유형 필터:", style={"fontWeight": "bold"}),
                            dcc.Checklist(
                                id="dup-type-filter",
                                options=[
                                    {"label": "같은 클래스", "value": "same"},
                                    {"label": "다른 클래스", "value": "diff"},
                                ],
                                value=["same", "diff"],
                                labelStyle={
                                    "display": "inline-block",
                                    "marginRight": "15px",
                                },
                            ),
                        ],
                        style={"marginBottom": "15px"},
                    ),
                    html.Div(
                        [
                            html.Label("좌표 임계값(px):", style={"fontWeight": "bold"}),
                            dcc.RangeSlider(
                                id="dup-threshold",
                                min=0,
                                max=50,
                                step=1,
                                value=[0, 5],
                                marks=make_marks(0, 50, 5),
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                            html.Div(
                                id="dup-threshold-display",
                                style={"marginTop": "10px", "fontWeight": "bold"},
                            ),
                        ],
                        style={"width": "420px"},
                    ),
                    html.Button(
                        "중복 검사 시작",
                        id="btn-duplicate-check",
                        n_clicks=0,
                        style={"marginTop": "15px"},
                    ),
                ],
                style={"marginBottom": "30px"},
            ),
            # =========================
            # 3. 중복 결과 테이블
            # =========================
            Loading(
                id="loading-duplicate-table",
                type="cube",
                children=dash_table.DataTable(
                    id="duplicate-table",
                    columns=[
                        {"name": "No", "id": "index"},
                        {"name": "이미지명", "id": "filename"},
                        {"name": "Line A", "id": "line_a"},
                        {"name": "Line B", "id": "line_b"},
                        {"name": "클래스", "id": "class_name"},
                        {"name": "비고", "id": "note"},
                        {"name": "총 좌표 차이(px)", "id": "diff_px"},
                    ],
                    data=[],
                    page_size=7,
                    page_current=0,
                    #row_selectable="single",
                    style_cell={"textAlign": "center"},
                    style_header={"fontWeight": "bold"},
                    style_table={"overflowX": "auto", "width": "100%"},
                    style_data_conditional=[
                        {
                            "if": {"state": "selected"},
                            "backgroundColor": "#D2F3FF",
                            "border": "1px solid #0074D9",
                        }
                    ],
                ),
            ),
            # 다운로드 버튼
            html.Div(
                [
                    html.Button("중복 결과 다운로드", id="btn-download-duplicate", n_clicks=0),
                    dcc.Download(id="download-duplicate-csv"),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "flex-end",
                    "marginTop": "10px",
                },
            ),
            # =========================
            # 4. 이미지 미리보기 (공용)
            # =========================
            html.Hr(style={"marginTop": "30px", "marginBottom": "20px"}),
            html.H4(
                "선택된 이미지 미리보기", style={"textAlign": "center", "marginBottom": "15px"}
            ),
            Loading(
                #id="loading-image-preview",
                id="loading-duplicate-image-preview",
                type="cube",
                children=html.Div(
                    dcc.Graph(
                        #id="image-preview",
                        id="duplicate-image-preview",
                        figure={},
                        config={
                            "displayModeBar": True,
                            "scrollZoom": True,
                            "doubleClick": False,
                            "displaylogo": False,
                        },
                        style={"height": "70vh", "width": "100%"},
                    ),
                    style={
                        "width": "100%",
                        "overflow": "hidden",
                        "boxSizing": "border-box",
                    },
                ),
            ),
        ],
        style={"padding": "20px", "boxSizing": "border-box", "width": "100%"},
    )


def image_exact_duplicate_tab_layout():
    """이미지 완전 중복 검사 탭 레이아웃"""
    return html.Div(
        [
            html.H4("이미지 완전 중복 검사 (MD5 기반)", style={"marginBottom": "15px"}),
            html.Button(
                "완전 중복 검사 시작",
                id="btn-image-exact-check",
                n_clicks=0,
                style={"marginTop": "10px"},
            ),
            html.Br(),
            html.Br(),
            Loading(
                id="loading-image-exact",
                type="cube",
                children=dash_table.DataTable(
                    id="image-exact-table",
                    columns=[
                        {"name": "No", "id": "index"},
                        {"name": "이미지 A", "id": "image_a"},
                        {"name": "이미지 B", "id": "image_b"},
                        {"name": "비고", "id": "note"},
                    ],
                    data=[],
                    page_size=7,
                    #row_selectable="single",
                    style_table={"overflowX": "auto", "width": "100%"},
                    style_cell={"textAlign": "center", "whiteSpace": "nowrap"},
                    style_header={"fontWeight": "bold"},
                    style_data_conditional=[
                        {
                            "if": {"state": "selected"},
                            "backgroundColor": "#D2F3FF",
                            "border": "1px solid #0074D9",
                        }
                    ],
                ),
            ),
            html.Div(
                [
                    html.Button(
                        "블렌딩 보기",
                        id="btn-show-blend",
                        n_clicks=0,
                        style={"marginTop": "10px", "marginRight": "10px"},
                    ),
                    html.Button(
                        "CSV 다운로드",
                        id="btn-download-image-exact",
                        n_clicks=0,
                        style={"marginTop": "10px"},
                    ),
                ],
                style={"display": "flex", "justifyContent": "flex-end"},
            ),
            dcc.Download(id="download-image-exact-csv"),
            dcc.Store(id="store-blend-mode", data=False),
            html.Hr(style={"marginTop": "30px", "marginBottom": "15px"}),
            dcc.Graph(
                id="imgblend-display",
                style={
                    "marginTop": "10px",
                    "width": "100%",
                    "height": "600px",
                    "overflow": "hidden",
                },
            ),
            html.Div(
                id="imgblend-selected-filenames",
                style={
                    "marginTop": "10px",
                    "textAlign": "center",
                    "fontWeight": "bold",
                },
            ),
        ],
        style={"padding": "20px", "boxSizing": "border-box", "width": "100%"},
    )


def image_feature_tab_layout():
    return html.Div(
        [
            html.H4("이미지 주간/야간 산점도", style={"marginBottom": "10px"}),
            html.Button(
                "주간/야간 분류 실행",
                id="btn-daynight-run",
                n_clicks=0,
                style={"marginBottom": "10px"},
            ),
            # 공통 타이틀 (여기서 기준선 통일)
            html.H5(
                "Day / Night CLIP Similarity (confidence view)",
                style={"marginBottom": "8px"},
            ),
            # 좌/우 레이아웃 (이 Div 하나만!)
            html.Div(
                [
                    # 왼쪽: 산점도
                    html.Div(
                        Loading(
                            dcc.Graph(
                                id="daynight-scatter",
                                figure={},
                                style={"height": "100%"},
                            ),
                            type="cube",
                        ),
                        style={
                            "width": "50%",
                            "height": "100%",
                            "paddingRight": "10px",
                        },
                    ),
                    # 오른쪽: 이미지
                    html.Div(
                        [
                            html.Div(
                                id="daynight-full-image",
                                style={
                                    "flex": "3",  # 메인 이미지
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                },
                            ),
                            html.Div(
                                id="daynight-thumbnails",
                                style={
                                    "flex": "1",  # 썸네일
                                    "display": "flex",
                                    "flexWrap": "wrap",
                                    "gap": "6px",
                                    "overflowY": "auto",
                                },
                            ),
                            html.Button(
                                "선택 이미지 다운로드",
                                id="btn-daynight-download",
                                n_clicks=0,
                                style={"marginTop": "8px"},
                            ),
                            dcc.Download(id="download-daynight-zip"),
                        ],
                        style={
                            "width": "50%",
                            "height": "100%",
                            "paddingLeft": "10px",
                            "display": "flex",
                            "flexDirection": "column",
                            "border": "1px solid gray",
                        },
                    ),
                ],
                style={"display": "flex", "height": "80vh"},
            ),
        ],
        style={"padding": "20px"},
    )


# 하위 호환성을 위한 기존 함수 유지 (deprecated)
def inspection_tab_layout(default_subtab="subtab-gt-duplicate"):
    """데이터 검사 탭 레이아웃 (하위 호환성 - 사용하지 않음)"""
    if default_subtab == "subtab-gt-duplicate":
        return gt_duplicate_tab_layout()
    elif default_subtab == "subtab-image-exact":
        return image_exact_duplicate_tab_layout()
    elif default_subtab == "subtab-image-feature":
        return image_feature_tab_layout()
    else:
        return gt_duplicate_tab_layout()
