# *gt/image check

import pandas as pd
import numpy as np
import plotly.express as px

def validate_paths(store):
    """
    store-paths에서 gt, img 경로를 검증하여 반환합니다.
    둘 중 하나라도 없으면 (None, None)을 반환합니다.
    """
    gt_folder = store.get("gt") if store else None
    img_folder = store.get("img") if store else None
    if not gt_folder or not img_folder:
        return None, None
    return gt_folder, img_folder
    
# *pandas converting
def dict_to_df(df_dict):
    """Convert dictionary to pandas DataFrame safely."""

    if df_dict is None:
        return pd.DataFrame()
    return pd.DataFrame(df_dict)

# *흰색 빈 이미지
def empty_figure():
    fig = px.imshow(np.ones((10, 10, 3), dtype=np.uint8) * 255)
    fig.update_layout(
        annotations=[
            dict(
                text="표시할 이미지 없음",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=20, color="gray"),
                xanchor="center",
                yanchor="middle",
            )
        ],
        xaxis=dict(visible=False, scaleanchor="y"),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_showscale=False,
    )
    return fig