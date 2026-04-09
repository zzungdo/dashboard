# callback.py

from callbacks.daynight import register_daynight_callbacks
from callbacks.home import register_home_callbacks
from callbacks.image import register_image_callbacks
from callbacks.inspection import register_inspection_callbacks
from callbacks.navigation import register_navigation_callbacks
from callbacks.statistics import register_statistics_callbacks
from callbacks.visual import register_visual_callbacks
from dash import Input, Output, State, callback


def register_callbacks(app):

    register_navigation_callbacks(app)

    register_home_callbacks(app)

    register_visual_callbacks(app)

    register_statistics_callbacks(app)

    register_image_callbacks(app)

    register_inspection_callbacks(app)

    register_daynight_callbacks(app)

    @callback(
        Output("sidebar-open", "data"),
        Input("toggle-sidebar", "n_clicks"),
        State("sidebar-open", "data"),
        prevent_initial_call=True,
    )
    def toggle_sidebar(n, is_open):
        return not is_open

    @callback(
        Output("sidebar", "className"),
        Input("sidebar-open", "data"),
    )
    def update_sidebar_class(is_open):
        if is_open:
            return "sidebar"
        return "sidebar collapsed"
