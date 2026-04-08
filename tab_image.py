#tab_image.py

from dash import html, dcc, dash_table
from dash.dcc import Loading

def image_tab_layout():
    """이미지 View 탭 레이아웃"""
    return html.Div([
        # Store 컴포넌트들 (최상위 레벨로 이동)
        dcc.Store(id='keyword-matched', data=[]),
        dcc.Store(id='keyword-page', data=0),
        
        # --- 이미지 요약 테이블 ---
        Loading(
            id='loading-summary-table',
            type='cube',
            children=dash_table.DataTable(
                id='summary-table',
                columns=[
                    {'name': '#', 'id': '_idx'},
                    {'name': '이미지명', 'id': 'filename'},
                    {'name': '총 바운딩박스 수', 'id': 'bbox_count'},
                    {'name': '클래스 다양성', 'id': 'unique_classes'},
                    {'name': '포함된 클래스', 'id': 'included_classes'}
                ],
                data=[],
                page_current=0,
                page_size=7,
                sort_action='native',
                style_table={'overflowX': 'auto', 'width': '100%'},
                style_cell={'textAlign': 'center', 'whiteSpace': 'nowrap'},
                style_header={'fontWeight': 'bold'},
                style_data_conditional=[
                    {'if': {'state': 'selected'},
                     'backgroundColor': '#D2F3FF',
                     'border': '1px solid #0074D9'}
                ],
                style_cell_conditional=[
                    {
                        'if': {'column_id': 'included_classes'},
                        'minWidth': '150px', 'maxWidth': '150px',
                        'whiteSpace': 'nowrap', 'overflow': 'hidden', 'textOverflow': 'ellipsis'}
                ]
            )
        ),

        html.Hr(style={'margin': '20px 0'}),
        
        # ---------------------- 좌우 분할 레이아웃 ----------------------
        html.Div([
            # ---------------------- 좌측 영역 (키워드 검색) ----------------------
            html.Div([
                html.H4('키워드 검색', style={'textAlign': 'center', 'marginBottom': '15px'}),

                html.Div([
                    dcc.Dropdown(
                        id='keyword-dropdown',
                        options=[],
                        placeholder='추천 키워드를 선택하세요',
                        multi=False,
                        searchable=True,
                        style={'width': '250px', 'fontSize': '13px', 'marginRight': '10px'}
                    ),
                    html.Button(
                        '검색',
                        id='btn-keyword-search',
                        n_clicks=0,
                        style={
                            'padding': '6px 14px',
                            'backgroundColor': '#0074D9',
                            'color': 'white',
                            'border': 'none',
                            'borderRadius': '4px',
                            'cursor': 'pointer',
                            'fontSize': '13px'
                        }
                    )
                ], style={
                    'display': 'flex',
                    'justifyContent': 'center',
                    'alignItems': 'center',
                    'margin': '10px 0'
                }),

                html.Div(
                    id='keyword-count-display',
                    style={
                        'marginTop': '10px',
                        'fontWeight': 'bold',
                        'textAlign': 'center'
                    }
                ),

                html.Div([
                    html.Button(
                        "◀",
                        id='keyword-prev',
                        n_clicks=0,
                        disabled=True,
                        style={
                            'padding': '4px 12px',
                            'margin': '0 5px',
                            'cursor': 'pointer',
                            'borderRadius': '4px',
                            'border': '1px solid #ccc'
                        }
                    ),
                    html.Span(
                        id='keyword-page-display',
                        style={'margin': '0 10px', 'fontWeight': 'bold'}
                    ),
                    html.Button(
                        "▶",
                        id='keyword-next',
                        n_clicks=0,
                        disabled=True,
                        style={
                            'padding': '4px 12px',
                            'margin': '0 5px',
                            'cursor': 'pointer',
                            'borderRadius': '4px',
                            'border': '1px solid #ccc'
                        }
                    ),
                ], style={'textAlign': 'center', 'marginTop': '10px'}),

                html.Div(
                    id='keyword-thumbnail-gallery',
                    style={
                        'display': 'flex',
                        'flexWrap': 'wrap',
                        'justifyContent': 'center',
                        'gap': '6px',
                        'overflowY': 'auto',
                        'border': '1px solid #ddd',
                        'borderRadius': '4px',
                        'minHeight': '200px',
                        'maxHeight': '60vh',
                        'padding': '10px',
                        'marginTop': '15px'
                    }
                )
            ], style={
                'flex': '1 1 0',
                'minWidth': '300px',
                'maxWidth': '30%',
                'padding': '10px',
                'borderRight': '1px solid #ddd',
                'overflow': 'hidden',
                'boxSizing': 'border-box'
            }),

            # ---------------------- 우측 영역 (이미지 미리보기) ----------------------
            html.Div([
                html.H4('선택된 이미지 미리보기', style={'textAlign': 'center', 'marginBottom': '15px'}),
                Loading(
                    id='loading-image-preview',
                    type='cube',
                    children=html.Div(
                        dcc.Graph(
                            id='image-preview',
                            figure={},
                            config={
                                'displayModeBar': True,
                                'scrollZoom': True,
                                'doubleClick': False,
                                'displaylogo': False
                            },
                            style={'height': '70vh', 'width': '100%'}
                        ),
                        style={
                            'width': '100%',
                            'overflow': 'hidden',
                            'boxSizing': 'border-box'
                        }
                    )
                )
            ], style={
                'flex': '1 1 0',
                'minWidth': '300px',
                'maxWidth': '70%',
                'padding': '10px',
                'overflow': 'hidden',
                'boxSizing': 'border-box'
            }),

        ],
        style={
            'display': 'flex',
            'flexDirection': 'row',
            'justifyContent': 'center',
            'alignItems': 'flex-start',
            'width': '100%',
            'gap': '10px',
            'boxSizing': 'border-box'
        })

    ],
    style={
        'width': '100%',
        'overflowX': 'auto',
        'boxSizing': 'border-box',
        'padding': '10px'
    })
