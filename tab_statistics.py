# tab_stats.py
from dash import dash_table, dcc, html
from dash.dcc import Loading


def statistics_tab_layout():
    return html.Div(
        [
            html.Div(
                [
                    # 왼쪽: 해상도 파이차트
                    html.Div(
                        [
                            html.Div(
                                id="image-count-display",
                                style={
                                    "fontSize": "25px",
                                    "fontWeight": "600",
                                    "color": "#2c3e50",
                                    "marginBottom": "10px",
                                    "textAlign": "center",
                                    "position": "relative",
                                    "top": "-10px",
                                },
                            ),
                            Loading(
                                id="loading-resolution-pie",
                                type="cube",
                                children=dcc.Graph(
                                    id="resolution-pie",
                                    figure={},
                                    style={
                                        "width": "100%",
                                        "height": "calc(45vh - 40px)",
                                        "minHeight": "350px",
                                    },
                                    config={"responsive": True},
                                ),
                            ),
                        ],
                        style={
                            "flex": "1",
                            "padding": "10px",
                            "display": "flex",
                            "marginRight": "10px",
                            "flexDirection": "column",
                        },
                    ),
                    # 오른쪽: 클래스별 파이차트
                    html.Div(
                        [
                            Loading(
                                id="loading-pie-chart",
                                type="cube",
                                children=dcc.Graph(
                                    id="pie-chart",
                                    figure={},
                                    style={
                                        "width": "100%",
                                        "height": "calc(45vh - 40px)",
                                        "minHeight": "350px",
                                        "marginTop": "50px",
                                    },
                                    config={"responsive": True},
                                ),
                            ),
                        ],
                        style={
                            "flex": "1",
                            "padding": "10px",
                            "display": "flex",
                            "flexDirection": "column",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "center",
                    "alignItems": "stretch",
                    "flexWrap": "wrap",
                },
            ),
            html.Div(
                [
                    html.Div(
                        [
                            Loading(
                                id="loading-consistency-pie",
                                type="cube",
                                children=dcc.Graph(
                                    id="consistency-pie",
                                    figure={},
                                    style={"width": "100%", "height": "350px"},
                                    config={"responsive": True},
                                ),
                            ),
                        ],
                        style={"flex": "1", "padding": "10px"},
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "center",
                    "alignItems": "stretch",
                    "flexWrap": "wrap",
                },
            ),
            html.Br(),
            html.H4("클래스별 바운딩박스 통계표", style={"textAlign": "center"}),
            dash_table.DataTable(
                id="class-summary-table",
                columns=[
                    {"name": "클래스", "id": "class"},
                    {"name": "총 개수", "id": "count"},
                    {"name": "클래스 비율(%)", "id": "class_ratio_percent"},
                    {"name": "포함 이미지 수", "id": "image_count"},
                    {"name": "이미지당 평균 개수", "id": "avg_per_image"},
                ],
                data=[],
                page_size=10,
                sort_action="native",
                row_selectable="single",
                style_table={"width": "100%", "margin": "0 auto"},
                style_cell={"textAlign": "center"},
                style_header={"fontWeight": "bold"},
                style_data_conditional=[
                    {
                        "if": {"state": "selected"},
                        "backgroundColor": "#D2F3FF",
                        "border": "1px solid #0074D9",
                    }
                ],
            ),
        ]
    )
