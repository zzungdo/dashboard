# layout.py
from dash import dcc, html
from tab_home import home_tab_layout
from tab_image import image_tab_layout
from tab_inspection import inspection_tab_layout
from tab_statistics import statistics_tab_layout
from tab_visual import visual_tab_layout


def create_layout():
    return html.Div(
        [
            dcc.Store(id="sidebar-open", data=True),
            dcc.Store(id="daynight-selected-files"),  # day/night
            html.Button(
                "☰", id="toggle-sidebar", n_clicks=0, className="hamburger-btn"
            ),
            html.Div(
                [
                    html.H2("📊 데이터 분석 도구", className="sidebar-title"),
                    # Home
                    html.Button(
                        "Home", id="btn-tab-home", n_clicks=0, className="sidebar-btn"
                    ),
                    # 분석 시각화 (상위 그룹)
                    html.Details(
                        [
                            html.Summary("분석 시각화", className="sidebar-btn"),
                            html.Div(
                                [
                                    html.Button(
                                        "산점도",
                                        id="btn-tab-visual-scatter",
                                        n_clicks=0,
                                        className="sidebar-subbtn",
                                    ),
                                    html.Button(
                                        "히트맵",
                                        id="btn-tab-visual-heatmap",
                                        n_clicks=0,
                                        className="sidebar-subbtn",
                                    ),
                                ],
                                className="sidebar-subgroup",
                            ),
                        ],
                        open=False,
                        className="sidebar-group",
                    ),
                    # 나머지 메뉴
                    html.Button(
                        "통계 요약",
                        id="btn-tab-statistics",
                        n_clicks=0,
                        className="sidebar-btn",
                    ),
                    html.Button(
                        "이미지 View",
                        id="btn-tab-img",
                        n_clicks=0,
                        className="sidebar-btn",
                    ),
                    html.Details(
                        [
                            html.Summary("데이터 검사", className="sidebar-btn"),
                            html.Div(
                                [
                                    html.Button(
                                        "GT 중복 검사",
                                        id="btn-tab-inspection-gt-duplicate",
                                        n_clicks=0,
                                        className="sidebar-subbtn",
                                    ),
                                    html.Button(
                                        "Image 중복 검사",
                                        id="btn-tab-inspection-image-duplicate",
                                        n_clicks=0,
                                        className="sidebar-subbtn",
                                    ),
                                    html.Button(
                                        "Day/Night Classification",
                                        id="btn-tab-inspection-image",
                                        n_clicks=0,
                                        className="sidebar-subbtn",
                                    ),
                                ],
                                className="sidebar-subgroup",
                            ),
                        ],
                        open=False,
                        className="sidebar-group",
                    ),
                    html.Hr(style={"margin": "20px 0", "borderColor": "#555"}),
                ],
                id="sidebar",
                className="sidebar",
            ),
            html.Div(
                [
                    html.Div(
                        id="main-content",
                        className="content",
                        children=home_tab_layout(),
                    ),
                    dcc.Store(id="store-paths"),
                    dcc.Store(id="store-df-all"),
                    dcc.Store(id="store-image-files"),
                    dcc.Store(id="store-gt-files"),
                ],
                className="main-container",
            ),
        ]
    )
