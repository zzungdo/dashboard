# callbacks/inspection.py

import os

import pandas as pd
from dash import Input, Output, State, dcc, no_update
from dash.exceptions import PreventUpdate
from utils import compare_images_md5, dict_to_df, validate_paths


def register_inspection_callbacks(app):

    # !이미지 중복 검사 콜백
    @app.callback(
        Output("image-exact-table", "data"),
        Input("btn-image-exact-check", "n_clicks"),
        State("store-paths", "data"),
        prevent_initial_call=True,
    )
    def run_exact_duplicate_check(n_clicks, store_paths):
        if not store_paths:
            raise PreventUpdate

        img_path = store_paths.get("img")
        if not img_path or not os.path.isdir(img_path):
            raise PreventUpdate

        results = compare_images_md5(img_path)

        # ✅ 중복 이미지가 없을 때
        if not results:
            return [
                {"index": "-", "image_a": "-", "image_b": "-", "note": "완전 중복 이미지 없음"}
            ]

        for i, r in enumerate(results):
            r["index"] = i + 1

        return results

    # ! 이미지 중복검사 결과 다운로드 콜백
    @app.callback(
        Output("download-image-exact-csv", "data"),
        Input("btn-download-image-exact", "n_clicks"),
        State("image-exact-table", "data"),
        prevent_initial_call=True,
    )
    def download_image_exact_csv(n_clicks, table_data):
        if not table_data:
            raise PreventUpdate

        df = pd.DataFrame(table_data)
        return dcc.send_data_frame(df.to_csv, "image_exact_results.csv", index=False)

    # ! 중복 바운딩박스 검사
    @app.callback(
        Output("duplicate-table", "data"),
        Input("store-paths", "data"),
        Input("store-df-all", "data"),
        Input("btn-duplicate-check", "n_clicks"),
        State("dup-threshold", "value"),
        State("dup-type-filter", "value"),
        prevent_initial_call=True,
    )
    def check_duplicate_boxes(
        store, df_all_dict, n_clicks, threshold_range, type_filters
    ):

        # 전역 dict를 함수 내에서 사용하도록 선언 및 초기화
        min_thresh, max_thresh = threshold_range
        global duplicate_box_dict
        duplicate_box_dict = {}

        gt_folder, img_folder = validate_paths(store)
        if gt_folder is None or img_folder is None:
            return []

        df_all = dict_to_df(df_all_dict)
        rows = []

        # *중복 바운딩박스 검사
        for fn in sorted(df_all["filename"].unique()):
            df_img = df_all[df_all["filename"] == fn]
            indices = df_img.index.tolist()
            lines = df_img[["class", "xmin", "ymin", "xmax", "ymax"]].values.tolist()

            used_indices = set()
            checked_pairs = set()

            for i in range(len(lines)):
                if indices[i] in used_indices:
                    continue
                for j in range(i + 1, len(lines)):
                    if indices[j] in used_indices:
                        continue
                    pair = (indices[i], indices[j])
                    if pair in checked_pairs or (pair[1], pair[0]) in checked_pairs:
                        continue

                    cls1, *b1 = lines[i]
                    cls2, *b2 = lines[j]

                    # *두 좌표 차이가 임계값 이하인경우
                    if all(
                        min_thresh <= abs(a - b) <= max_thresh for a, b in zip(b1, b2)
                    ):
                        pixel_diffs = [abs(a - b) for a, b in zip(b1, b2)]
                        max_diff = round(sum(pixel_diffs), 2)

                        if cls1 == cls2 and "same" in type_filters:
                            note = "같은 클래스"
                            rows.append(
                                {
                                    "filename": fn,
                                    "line_a": (i + 1),
                                    "line_b": (j + 1),
                                    "class_name": cls1,
                                    "note": note,
                                    "diff_px": max_diff,
                                }
                            )

                        elif cls1 != cls2 and "diff" in type_filters:
                            note = "다른 클래스"
                            rows.append(
                                {
                                    "filename": fn,
                                    "line_a": (i + 1),
                                    "line_b": (j + 1),
                                    "class_name": f"{cls1} / {cls2}",
                                    "note": note,
                                    "diff_px": max_diff,
                                }
                            )
                        # *중복 bbox 기록
                        duplicate_box_dict.setdefault(fn, set()).update(
                            [indices[i], indices[j]]
                        )
                        used_indices.update([indices[i], indices[j]])
                        checked_pairs.add(pair)
                        break
        # *결과 DataFrame 생성
        df_res = pd.DataFrame(rows).reset_index(drop=True)

        # ✅ 중복이 하나도 없을 때
        if df_res.empty:
            return [
                {
                    "index": "-",
                    "filename": "-",
                    "line_a": "-",
                    "line_b": "-",
                    "class_name": "-",
                    "note": "중복 GT 없음",
                    "diff_px": "-",
                }
            ]

        df_res.insert(0, "index", df_res.index + 1)
        return df_res.to_dict("records")

    # ! GT 중복검사 탭에서 사용 콜백
    @app.callback(
        Output("dup-threshold-display", "children"), Input("dup-threshold", "value")
    )
    def update_dup_threshold_display(value):
        return f"바운딩박스 좌표 오차 범위: {value[0]} ~ {value[1]}px"

    # ! 중복결과 다운로드 콜백
    @app.callback(
        Output("download-duplicate-csv", "data"),
        Input("btn-download-duplicate", "n_clicks"),
        State("duplicate-table", "data"),
        prevent_initial_call=True,
    )
    def download_duplicate_filenames(n_clicks, table_data):
        if not table_data:
            return no_update

        # 중복된 이미지 filename만 추출
        filenames = [row["filename"] for row in table_data if "filename" in row]
        unique_filenames = sorted(set(filenames))  # 중복 제거 + 정렬

        # 문자열로 변환
        content = "\n".join(unique_filenames)

        return dict(content=content, filename="duplicate_list.txt")
