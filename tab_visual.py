#tab_visual.py


from dash import html, dcc
from dash.dcc import Loading

def make_marks(start: int, end: int, step: int):
    return {i: str(i) for i in range(start, end + 1, step)}

def visual_tab_layout(default_subtab='subtab-scatter'):
    """분석 시각화 탭 레이아웃"""
    return html.Div([
        dcc.Tabs(
            id='visual-subtabs',
            value=default_subtab,  # 클릭한 버튼에 따라 다르게 설정
            className='hidden-tabs',
            children=[
                # === ① 산점도 탭 ===
                dcc.Tab(label='산점도', value='subtab-scatter', children=[
                    html.Div([
                        html.Label("BBox Width 범위", style={'marginRight': '10px'}),
                        dcc.RangeSlider(
                            id='scatter-width-range',
                            min=0, max=4000, step=1, value=[0, 4000],
                            marks=make_marks(0, 4000, 500),
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                        html.Br(),
                        html.Label("BBox Height 범위", style={'marginRight': '10px'}),
                        dcc.RangeSlider(
                            id='scatter-height-range',
                            min=0, max=3000, step=1, value=[0, 3000],
                            marks=make_marks(0, 3000, 500),
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                    ], style={'margin': '10px'}),

                    # === 산점도 및 미리보기 영역 ===
                    html.Div([
                        # ① 산점도
                        Loading(
                            id='loading-center-scatter',
                            type='cube',
                            children=dcc.Graph(
                                id='center-scatter',
                                figure={},
                                style={'height': '80vh', 'width': '40vw', 'marginRight': '20px'}
                            )
                        ),

                        # ② 이미지 미리보기
                        Loading(
                            id='loading-scatter-preview',
                            type='cube',
                            children=dcc.Graph(
                                id='scatter-preview',
                                figure={},
                                config={
                                    'displayModeBar': True,
                                    'scrollZoom': True,
                                    'doubleClick': False,
                                    'displayModeBar' : False,
                                    'displaylogo': False
                                },
                                style={'height': '80vh', 'width': '40vw'}
                            )
                        ),
                    ],
                    # ✅ 여기서 가로 배치 스타일 지정
                    style={
                        'display': 'flex',
                        'flexDirection': 'row',       # 가로 배치
                        'justifyContent': 'center',   # 전체 가운데 정렬
                        'alignItems': 'flex-start',   # 위쪽 기준 (필요 시 'center')
                        'width': '100%'
                    })

                ]),

                # === ② 히트맵 탭 ===
                dcc.Tab(label='히트맵', value='subtab-heatmap', children=[
                
                    # 설정 영역 (클래스 필터, 그리드 사이즈)
                    html.Div([
                        html.Label('클래스 필터:'),
                        dcc.Dropdown(
                            id='heatmap-class-filter',
                            options=[{'label': 'All', 'value': 'All'}],
                            value='All', clearable=False,
                            style={'width': '200px'}
                        ),
                        html.Br(),
                        html.Label('그리드 사이즈:'),
                        dcc.Input(
                            id='heatmap-grid-size',
                            type='number', value=5, min=1, step=1,
                            style={'width': '100px'}
                        ),
                    ], style={'margin': '10px'}),

                    # === 히트맵 + 썸네일(좌) / 미리보기(우) ===
                    html.Div([
                        # 왼쪽: 히트맵 + 썸네일
                        html.Div([
                            Loading(
                                id='loading-heatmap',
                                type='cube',
                                children=dcc.Graph(
                                    id='heatmap',
                                    figure={},
                                    style={'height': '75vh', 'width': '40vw', 'marginRight': '20px'}   # ✅ 동일한 크기 적용
                                )
                            ),
                            html.Hr(style={'margin': '10px 0'}),
                            html.Div([
                                html.H4("검출된 이미지 썸네일", style={'marginBottom': '10px'}),
                                html.Div(
                                    id='thumbnail-gallery',
                                    style={
                                        'display': 'flex',
                                        'flexWrap': 'wrap',
                                        'justifyContent': 'center',
                                        'gap': '6px',
                                        'maxWidth': '100%',
                                        'overflow': 'hidden',
                                        'marginBottom': '20px'
                                    }
                                )
                            ])
                        ], style={'flex': '1', 'padding': '10px'}),

                        # 오른쪽: 클릭 시 이미지 미리보기
                        html.Div([
                            Loading(
                                id='loading-heatmap-preview',
                                type='cube',
                                children=dcc.Graph(
                                    id='heatmap-preview',
                                    figure={},
                                        config={
                                        'displayModeBar': True,
                                        'scrollZoom': True,
                                        'doubleClick': False,   # ✅ 더블클릭 → 원본으로 복귀
                                        'displayModeBar' : False,
                                        'displaylogo': False
                                    },
                                    style={
                                        'height': '80vh',          # ✅ 동일한 높이
                                        'width': '40vw',           # ✅ 동일한 폭
                                        'display': 'flex',
                                        'justifyContent': 'center',
                                        'alignItems': 'center'
                                    }
                                )
                            )
                        ], style={'flex': '1', 'padding': '10px'}),
                    ],
                    style={
                        'display': 'flex',
                        'flexDirection': 'row',        # 가로 배치
                        'justifyContent': 'center',    # 전체 가운데 정렬
                        'alignItems': 'flex-start',
                        'width': '100%'
                    })

                ])

            ],
            style={
                'margin': '0 auto',
                'width': '100%',
                'height': 'auto',
                'padding': '10px',
                'boxSizing': 'border-box'
            }
        )
    ])
