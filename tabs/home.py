from dash import html, dcc
from dash.dcc import Loading


def home_tab_layout(current_paths=None, reset_mode=False):
    """홈 탭 레이아웃 — 경로 입력 및 재설정 모드 지원"""
    gt_value = current_paths.get('gt') if current_paths else ""
    img_value = current_paths.get('img') if current_paths else ""

    # 이미 경로 설정되어 있고, 아직 재설정 모드 아님 → “재설정하시겠습니까?” 안내
    #if gt_value and img_value and not reset_mode:
    if img_value and not reset_mode:
        return html.Div([
            html.H2("현재 설정된 경로", style={'textAlign': 'center', 'marginTop': '40px'}),
            html.Div([
                html.P(f"📁 GT: {gt_value}", style={'fontWeight': 'bold', 'color': '#2c3e50'}),
                html.P(f"🖼 IMAGE: {img_value}", style={'fontWeight': 'bold', 'color': '#2c3e50'}),
            ], style={
                'width': '70%',
                'margin': '20px auto',
                'padding': '20px',
                'backgroundColor': '#f4f4f4',
                'borderRadius': '10px',
                'boxShadow': '0 2px 6px rgba(0,0,0,0.1)',
                'textAlign': 'left'
            }),

            html.P("경로를 재설정하시겠습니까?",
                   style={'textAlign': 'center', 'marginTop': '15px', 'color': '#555'}),

            html.Button("재설정", id='btn-reset-paths', n_clicks=0, style={
                'backgroundColor': '#e67e22',
                'color': 'white',
                'border': 'none',
                'padding': '10px 20px',
                'borderRadius': '6px',
                'cursor': 'pointer',
                'fontSize': '15px',
                'display': 'block',
                'margin': '10px auto'
            })
        ])

    # 재설정 모드이거나 처음 실행일 때 — 입력창 표시
    return html.Div([
        html.H2("데이터 경로 설정", style={'textAlign': 'center', 'marginTop': '40px'}),
        html.P("아래에 GT와 IMAGE 폴더 경로를 입력한 뒤 RUN을 눌러주세요.",
               style={'textAlign': 'center', 'color': '#555', 'marginBottom': '30px'}),

        html.Div([
            html.Label("GT 폴더 경로", style={'fontWeight': 'bold'}),
            dcc.Input(id='main-gt-path', type='text', value=gt_value,
                      placeholder='예: D:\\DATASET\\gt',
                      style={'width': '100%', 'padding': '8px',
                             'borderRadius': '4px', 'border': '1px solid #ccc',
                             'marginBottom': '15px'}),

            html.Label("IMAGE 폴더 경로", style={'fontWeight': 'bold'}),
            dcc.Input(id='main-img-path', type='text', value=img_value,
                      placeholder='예: D:\\DATASET\\images',
                      style={'width': '100%', 'padding': '8px',
                             'borderRadius': '4px', 'border': '1px solid #ccc',
                             'marginBottom': '20px'}),

            html.Button("RUN", id='main-run', n_clicks=0, style={
                'width': '200px', 'padding': '10px', 'backgroundColor': '#0074D9',
                'color': 'white', 'border': 'none', 'borderRadius': '6px',
                'cursor': 'pointer', 'fontSize': '15px', 'display': 'block',
                'margin': '0 auto'
            })
        ], style={
            'width': '50%', 'margin': '0 auto', 'padding': '30px 40px',
            'backgroundColor': '#f9f9f9', 'borderRadius': '10px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'
        }),

        Loading(id='loading-home-run', type='cube',
                children=html.Div(id='home-run-status',
                                  style={'textAlign': 'center', 'marginTop': '20px', 'color': '#555'}))
    ])
