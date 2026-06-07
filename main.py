import streamlit as st
import pandas as pd
import pydeck as pdk
import json
import numpy as np
import calc
import data_storage as ds
from itertools import chain
import graph
import pprint
import plotly.express as px



st.set_page_config(layout="wide")

# 先にpoiデータ読み込み
with open("data/AkitaUniv_geofences.json", "r", encoding="utf-8") as f:
    poi_data = json.load(f)
poi = poi_data["geofences"]
poi_name_list, poi_lat_list, poi_lon_list, radius_list = ds.poi_storage(poi)



# ==========================================================
# 操作ボタン配置
# ==========================================================

st.title("Data Visualization")
selected_mode = st.selectbox("モード", ["グラフ", "ヒートマップ", "Temporal IoU", "全体軌跡", "撮影軌跡"])
person = ["i1114", "h1114", "i1127", "k1114", "n1127", "m1219", "t1219", "h1210", "i1024", "s1125", "t1127"]

# グラフモード
if selected_mode == "グラフ":
    selected_person = st.selectbox("撮影者", person + ["全て"])
    target_id = 0
    selected_attention_poi = "全て"

# ヒートマップモード
if selected_mode == "ヒートマップ":
    selected_attention_poi = st.selectbox("注目するPOI", ["POI ID", "全て"])
    selected_person = "全て"
    if selected_attention_poi == "POI ID":
        poi = [0, 1, 2, 3, 4, 5]
        target_id = st.selectbox("temp", poi, label_visibility="collapsed")
    else:
        target_id = 0

# Temporal IoUモード
elif selected_mode == "Temporal IoU":
    selected_person = st.selectbox("撮影者", person + ["全て"])
    target_id = 0
    selected_attention_poi = "全て"
    selected_radius_setting = st.selectbox("ジオフェンス半径", ["一律", "個別"])
    if selected_radius_setting == "一律":
        all_radius = st.text_input(
            label = "半径一律",
            label_visibility="collapsed",
            value = "30"
        )
    elif selected_radius_setting == "個別":
        cols = st.columns(6)
        input_radius = []
        for i, col in enumerate(cols):
            with col:
                st.caption(poi_name_list[i])
                radius = st.text_input(
                    label=f"半径 {i+1}",
                    label_visibility="collapsed",
                    key=f"text_input_{i}",
                    value = "30"
                )
                input_radius.append(radius)
    selected_threshold = st.text_input(
        label="視野角",
        label_visibility="collapsed",
        value = "40"
    )

# 全体軌跡モード
elif selected_mode == "全体軌跡":
    selected_person = st.selectbox("撮影者", person)

# 撮影軌跡モード
else:
    selected_person = st.selectbox("撮影者", person)
    selected_attention_poi = st.selectbox("注目するPOI", ["POI ID", "撮影順", "全て"])
    if selected_attention_poi == "POI ID":
        poi = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 98, 99]
        target_id = st.selectbox("temp", poi, label_visibility="collapsed")
    elif selected_attention_poi == "撮影順":
        count = st.number_input(
            label="temp", 
            value=1,     
            min_value=1,
            max_value=20,
            step=1,
            label_visibility="collapsed"
        )
        target_id = count



# ==========================================================
# jsonファイル読み込み
# ==========================================================

# gpsデータ・方向データ読み込み
if selected_person == "全て":
    gps_data_list = []
    heading_data_list = []
    for name in person:
        with open("data/gps_trajectory/" + name + "-gps.json", "r", encoding="utf-8") as f:
            gps_data = json.load(f)
        with open("data/heading/" + name + "-heading_updates.json", "r", encoding="utf-8") as f:
            heading_data = json.load(f)
        gps_data_list.append(gps_data)
        heading_data_list.append(heading_data)
elif selected_mode == "撮影軌跡" or "グラフ" :
    with open("data/gps_trajectory/" + selected_person + "-gps.json", "r", encoding="utf-8") as f:
        gps_data = json.load(f)
    with open("data/heading/" + selected_person + "-heading_updates.json", "r", encoding="utf-8") as f:
        heading_data = json.load(f)
else:
    with open("data/gps_trajectory/" + selected_person + "-gps.json", "r", encoding="utf-8") as f:
        gps_data = json.load(f)



# ==========================================================
# データ整理・グラフ作成
# ==========================================================

# グラフモード
if selected_mode == "グラフ":
    if selected_person == "全て":
        union_dict = {}
        for gps_data, heading_data, name in zip(gps_data_list, heading_data_list, person):
            # gpsデータ分解
            location = gps_data["location"]
            _, _, _, _, _, time_list, path_not_color_list = ds.locations_storage(location, selected_mode)
            # 方向データ分解
            heading = heading_data["direction"]
            _, division_heading_list, poi_id_list = ds.headings_storage(heading, time_list)
            direction_difference_dict, _ = ds.difference_direction_between_user_and_poi(path_not_color_list, division_heading_list, poi_id_list, poi_lat_list, poi_lon_list, "dict")
            
            # 撮影者一人のデータを全体データと合流
            for key, lines in direction_difference_dict.items():
                formatted_lines = [{"name": name, "data": line} for line in lines]
                union_dict.setdefault(key, []).extend(formatted_lines)
        
        # 複折れ線グラフの作成
        graph.create_multiple_lines_graph(union_dict, poi_name_list)
    else:
        # gpsデータ分解
        location = gps_data["location"]
        _, _, _, _, _, time_list, path_not_color_list = ds.locations_storage(location, selected_mode)
        # 方向データ分解
        heading = heading_data["direction"]
        _, division_heading_list, poi_id_list = ds.headings_storage(heading, time_list)
        direction_difference_list, _ = ds.difference_direction_between_user_and_poi(path_not_color_list, division_heading_list, poi_id_list, poi_lat_list, poi_lon_list, "list")

        #折れ線グラフの作成
        for difference in direction_difference_list:
            graph.create_line_graph(difference, poi_name_list, unique_key=f"graph_mode_line_{i}")



# ヒートマップモード
if selected_mode == "ヒートマップ":
    union_dict = {}
    for gps_data, heading_data, name in zip(gps_data_list, heading_data_list, person):
        # gpsデータ分解
        location = gps_data["location"]
        lat_list, lon_list, color_list, path_list, path_color_list, time_list, path_not_color_list = ds.locations_storage(location, selected_mode)
        # 方向データ分解
        heading = heading_data["direction"]
        _, division_heading_list, poi_id_list = ds.headings_storage(heading, time_list)

        # 移動座標をpoiごとに区分け
        lat_iter = iter(lat_list)
        lon_iter = iter(lon_list)
        division_lat_list = [[next(lat_iter) for _ in sub_list] for sub_list in division_heading_list]
        division_lon_list = [[next(lon_iter) for _ in sub_list] for sub_list in division_heading_list]

        coor_dict = {}

        for i, (lat, lon, poi_id) in enumerate(zip(division_lat_list, division_lon_list, poi_id_list)):
            if poi_id < 6:  # 今のところ、事前に設定したpoi以外はスキップ
                coor_list = [list(coord) for coord in zip(lat, lon)]
                coor_dict.setdefault(poi_id, []).append(coor_list)
            
        
        # 撮影者一人のデータを全体データと合流
        for poi_id, sub_lists in coor_dict.items():
            union_dict.setdefault(poi_id, [])
            for coor_list in sub_lists:
                union_dict[poi_id].extend(coor_list)
    
    heatmap_layer, heat_avg_lat, heat_avg_lon = graph.create_heatmap(union_dict, selected_attention_poi, target_id)
    lat_list = [heat_avg_lat] if heat_avg_lat else []
    lon_list = [heat_avg_lon] if heat_avg_lon else []

        

# Temporal IoUモード
if selected_mode == "Temporal IoU":
    
    if selected_person == "全て":
        st.caption("POIごとの平均スコア")
        
        poi_scores = {poi_id: {p: {"f1": [], "iou": [], "prec": [], "rec": []} for p in person} for poi_id in range(6)}
        
        for gps_data, heading_data, name in zip(gps_data_list, heading_data_list, person):
            location = gps_data["location"]
            lat_list, lon_list, _, _, _, time_list, path_not_color_list = ds.locations_storage(location, selected_mode)
            heading = heading_data["direction"]
            _, division_heading_list, poi_id_list = ds.headings_storage(heading, time_list)
            
            lat_iter = iter(lat_list)
            lon_iter = iter(lon_list)
            division_lat_list = [[next(lat_iter) for _ in sub_list] for sub_list in division_heading_list]
            division_lon_list = [[next(lon_iter) for _ in sub_list] for sub_list in division_heading_list]

            geofence_inside_outside_mask = []
            not_filtered_heading_list = []
            not_filtered_lat_list = []
            not_filtered_lon_list = []
            filtered_poi_list = []

            for inner_lat_list, inner_lon_list, inner_heading_list, poi_id in zip(division_lat_list, division_lon_list, division_heading_list, poi_id_list):
                if poi_id < 6:
                    center_lat, center_lon = poi_lat_list[poi_id], poi_lon_list[poi_id]
                    radius = all_radius if selected_radius_setting == "一律" else input_radius[poi_id]
                    
                    results = []
                    for lon, lat in zip(inner_lon_list, inner_lat_list):
                        is_inside = calc.geofence_inside_outside_determination(center_lat, center_lon, radius, lat, lon)
                        results.append(is_inside)
                    
                    geofence_inside_outside_mask.append(results)
                    not_filtered_heading_list.append(inner_heading_list)
                    not_filtered_lat_list.append(inner_lat_list)
                    not_filtered_lon_list.append(inner_lon_list)
                    filtered_poi_list.append(poi_id)

            not_filtered_direction_difference = []
            for lat, lon, heading, poi_id in zip(not_filtered_lat_list, not_filtered_lon_list, not_filtered_heading_list, filtered_poi_list):
                poi_dir = ds.direction_user_to_poi(lat, lon, poi_lat_list[poi_id], poi_lon_list[poi_id])
                difference = calc.angle_difference_calc(heading, poi_dir)
                not_filtered_direction_difference.append(difference)
            
            filtered_direction_difference = [
                [{"value": val, "status": "inside" if is_inside else "outside"} for val, is_inside in zip(sub_data, sub_mask)]
                for sub_data, sub_mask in zip(not_filtered_direction_difference, geofence_inside_outside_mask)
            ]

            double_filtered_direction_difference = [
                [{"value": d["value"], "status": (d["status"], "flame_in" if abs(d["value"]) <= float(selected_threshold) else "flame_out")} for d in sub_list]
                for sub_list in filtered_direction_difference
            ]

            with open("data/flame_in_time/" + name + "-flame_in_time.json", "r", encoding="utf-8") as f:
                timeline_data = json.load(f)
            flame_in_list = timeline_data["flame_in"]

            for i, (nested_list, poi_id) in enumerate(zip(double_filtered_direction_difference, filtered_poi_list)):
                current_flame_timeline = flame_in_list[i]["flame_in"]
                metrics = calc.calculate_timeline_metrics(nested_list, current_flame_timeline)
                
                poi_scores[poi_id][name]["f1"].append(metrics["F1_Score"])
                poi_scores[poi_id][name]["iou"].append(metrics["Temporal_IoU"])
                poi_scores[poi_id][name]["prec"].append(metrics["Precision"])
                poi_scores[poi_id][name]["rec"].append(metrics["Recall"])

        avg_scores_data = []
        for poi_id in range(6):
            person_f1 = [np.mean(poi_scores[poi_id][p]["f1"]) for p in person if poi_scores[poi_id][p]["f1"]]
            person_iou = [np.mean(poi_scores[poi_id][p]["iou"]) for p in person if poi_scores[poi_id][p]["iou"]]
            person_prec = [np.mean(poi_scores[poi_id][p]["prec"]) for p in person if poi_scores[poi_id][p]["prec"]]
            person_rec = [np.mean(poi_scores[poi_id][p]["rec"]) for p in person if poi_scores[poi_id][p]["rec"]]
            
            if person_f1:
                avg_scores_data.append({
                    "POI名": poi_name_list[poi_id],
                    "F1 Score": round(np.mean(person_f1), 3),
                    "Temporal IoU": round(np.mean(person_iou), 3),
                    "Precision": round(np.mean(person_prec), 3),
                    "Recall": round(np.mean(person_rec), 3),
                    "参加者数": len(person_f1)
                })
        
        if avg_scores_data:
            df_avg = pd.DataFrame(avg_scores_data)
            st.dataframe(df_avg, width='stretch')
            
            fig = px.bar(
                df_avg, 
                x="POI名", 
                y=["F1 Score", "Temporal IoU"], 
                barmode="group", 
                title="POI別 全員平均スコア比較",
                height=400
            )
            st.plotly_chart(fig, width='stretch', key="avg_score_bar_chart")
            
        path_list = []
        path_color_list = []
        heading_line_list = []
        lat_list, lon_list, color_list = [], [], []
        geofence_inside_outside_mask = []

    else:
        location = gps_data["location"]
        lat_list, lon_list, _, _, _, time_list, path_not_color_list = ds.locations_storage(location, selected_mode)
        heading = heading_data["direction"]
        _, division_heading_list, poi_id_list = ds.headings_storage(heading, time_list)
        direction_difference_list, _ = ds.difference_direction_between_user_and_poi(path_not_color_list, division_heading_list, poi_id_list, poi_lat_list, poi_lon_list, "list")

        lat_iter = iter(lat_list)
        lon_iter = iter(lon_list)
        division_lat_list = [[next(lat_iter) for _ in sub_list] for sub_list in division_heading_list]
        division_lon_list = [[next(lon_iter) for _ in sub_list] for sub_list in division_heading_list]
        _, view_lat_list, view_lon_list = ds.extend_line(division_lat_list, division_lon_list, division_heading_list, poi_id_list)

        lat_list = []
        lon_list = []

        not_filtered_heading_list = []
        not_filtered_lat_list = []
        not_filtered_lon_list = []
        filtered_poi_list = []
        geofence_inside_outside_mask = []

        for inner_lat_list, inner_lon_list, inner_heading_list, poi_id in zip(division_lat_list, division_lon_list, division_heading_list, poi_id_list):
            if poi_id < 6:
                center_lat, center_lon = poi_lat_list[poi_id], poi_lon_list[poi_id]
                if selected_radius_setting == "一律":
                    radius = all_radius
                elif selected_radius_setting == "個別":
                    radius = input_radius[poi_id]

                results = []
                not_filtered_inner_heading_list = []
                not_filtered_inner_lat_list = []
                not_filtered_inner_lon_list = []

                for lon, lat, heading in zip(inner_lon_list, inner_lat_list, inner_heading_list):
                    is_inside = calc.geofence_inside_outside_determination(center_lat, center_lon, radius, lat, lon)
                    results.append(is_inside)
                    
                    lat_list.append(lat)
                    lon_list.append(lon)   
                    not_filtered_inner_heading_list.append(heading) 
                    not_filtered_inner_lat_list.append(lat)
                    not_filtered_inner_lon_list.append(lon)  
                    
                geofence_inside_outside_mask.append(results)
                not_filtered_heading_list.append(not_filtered_inner_heading_list)
                not_filtered_lat_list.append(not_filtered_inner_lat_list)
                not_filtered_lon_list.append(not_filtered_inner_lon_list)
                filtered_poi_list.append(poi_id)
        
        color_list = ds.color_change_by_geofence(geofence_inside_outside_mask)

        not_filtered_direction_difference = []
        for lat, lon, heading, poi_id in zip(not_filtered_lat_list, not_filtered_lon_list, not_filtered_heading_list, filtered_poi_list):
            poi_dir = ds.direction_user_to_poi(lat, lon, poi_lat_list[poi_id], poi_lon_list[poi_id])
            difference = calc.angle_difference_calc(heading, poi_dir)
            not_filtered_direction_difference.append(difference)
        
        filtered_direction_difference = [
            [
                {"value": val, "status": "inside" if is_inside else "outside"}
                for val, is_inside in zip(sub_data, sub_mask)
            ]
            for sub_data, sub_mask in zip(not_filtered_direction_difference, geofence_inside_outside_mask)
        ]

        double_filtered_direction_difference = [
            [
                {
                    "value": d["value"], 
                    "status": (
                        d["status"], 
                        "flame_in" if abs(d["value"]) <= float(selected_threshold) else "flame_out"
                    )
                }
                for d in sub_list
            ]
            for sub_list in filtered_direction_difference
        ]

        with open("data/flame_in_time/" + selected_person + "-flame_in_time.json", "r", encoding="utf-8") as f:
            timeline_data = json.load(f)
        flame_in_list = timeline_data["flame_in"]

        for i, (nested_list, poi_id) in enumerate(zip(double_filtered_direction_difference, filtered_poi_list)):
            current_flame_timeline = flame_in_list[i]["flame_in"]
            metrics = calc.calculate_timeline_metrics(nested_list, current_flame_timeline)

            print(f"--- [POI:{poi_name_list[poi_id]}] 撮影者:{selected_person} ---")
            print(f"TP: {metrics.get('TP', 0)} | FP: {metrics.get('FP', 0)} | FN: {metrics.get('FN', 0)}")
            
            st.write(f"### {poi_name_list[poi_id]}")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("F1 Score", f"{metrics['F1_Score']:.3f}")
            col2.metric("Temporal IoU", f"{metrics['Temporal_IoU']:.3f}")
            col3.metric("Precision", f"{metrics['Precision']:.3f}")
            col4.metric("Recall", f"{metrics['Recall']:.3f}")
            
            graph.create_timeline_graph(nested_list, flame_in_list, i, timeline_data, poi_id, poi_name_list)
            
            old_style_list = [
                poi_id,
                [d["value"] for d in nested_list]
            ]
            graph.create_line_graph(old_style_list, poi_name_list, caption=False, unique_key=f"iou_mode_line_{poi_id}_{i}")
            st.markdown("***")

        path_list = []
        path_color_list = []
        heading_line_list = list(chain.from_iterable(filtered_direction_difference))
            




# 撮影モード
if selected_mode == "撮影軌跡":
    # gpsデータ分解
    location = gps_data["location"]
    lat_list, lon_list, color_list, path_list, path_color_list, time_list, path_not_color_list = ds.locations_storage(location, selected_mode)
    # 方向データ分解
    heading = heading_data["direction"]
    heading_list, division_heading_list, poi_id_list = ds.headings_storage(heading, time_list)
    direction_difference_list, order_list = ds.difference_direction_between_user_and_poi(path_not_color_list, division_heading_list, poi_id_list, poi_lat_list, poi_lon_list, "list")

    # 移動座標をpoiごとに区分け(方向を示すライン描画のためのデータ整理)
    lat_iter = iter(lat_list)
    lon_iter = iter(lon_list)
    color_iter = iter(color_list)
    division_lat_list = [[next(lat_iter) for _ in sub_list] for sub_list in division_heading_list]
    division_lon_list = [[next(lon_iter) for _ in sub_list] for sub_list in division_heading_list]
    division_color_list = [[next(color_iter) for _ in sub_list] for sub_list in division_heading_list]

    if selected_attention_poi == "全て":
        heading_line_list, view_lat_list, view_lon_list = ds.extend_line(division_lat_list, division_lon_list, division_heading_list, poi_id_list)
    else:
        heading_line_list, view_lat_list, view_lon_list = ds.extend_line(division_lat_list, division_lon_list, division_heading_list, poi_id_list, target_id, selected_attention_poi)

    #折れ線グラフの作成
    if selected_attention_poi != "全て":
        for i, difference in enumerate(direction_difference_list):
            if selected_attention_poi == "POI ID" and target_id == difference[0]:
                graph.create_line_graph(difference, poi_name_list, unique_key=f"trace_mode_line_{i}")
            elif selected_attention_poi == "撮影順" and order_list[i] == target_id:
                graph.create_line_graph(difference, poi_name_list, unique_key=f"trace_mode_line_{i}")
                break

    # 描画するポイントの上書き
        lat_list = []
        lon_list = []
        color_list = []
        for i, (lat, lon, color, poi_id) in enumerate(zip(division_lat_list, division_lon_list, division_color_list, poi_id_list)):
            if selected_attention_poi == "POI ID" and poi_id == target_id:
                lat_list.extend(lat)
                lon_list.extend(lon)
                color_list.extend(color)
            elif selected_attention_poi == "撮影順" and i+1 == target_id:
                lat_list.extend(lat)
                lon_list.extend(lon)
                color_list.extend(color)




# 全体モード
if selected_mode == "全体軌跡":
    # gpsデータ分解
    location = gps_data["location"]
    lat_list, lon_list, color_list, path_list, path_color_list, time_list, _ = ds.locations_storage(location, selected_mode)
    heading_line_list = []
    


# ==========================================================
# マップオブジェクトのためのデータ整理
# ==========================================================

if selected_mode == "全体軌跡" or selected_mode == "撮影軌跡" or selected_mode == "Temporal IoU":
    df_poi = pd.DataFrame({
        "name": poi_name_list,
        "lat": poi_lat_list,
        "lon": poi_lon_list,
        "radius": radius_list,
    })
    df_poi["icon"] = "marker"
    df_poi["tooltip_text"] = "<b>POI名:</b> " + df_poi["name"]
    # 撮影者の位置情報
    if selected_mode == "Temporal IoU":
        df_point = pd.DataFrame({
            "lat": lat_list,
            "lon": lon_list,
            "color": color_list,
            "heading": heading_line_list,
        })
        df_point["tooltip_text"] = (
            "<b>座標:</b> [" + df_point["lon"].astype(str) + ", " + df_point["lat"].astype(str) + "]<br>"
            "<b>方向:</b> " + df_point["heading"].astype(str)
        )
    elif selected_mode == "撮影軌跡" :
        df_point = pd.DataFrame({
            "lat": lat_list,
            "lon": lon_list,
            "color": color_list,
            "heading": heading_line_list,
        })
        df_point["tooltip_text"] = (
            "<b>座標:</b> [" + df_point["lon"].astype(str) + ", " + df_point["lat"].astype(str) + "]<br>"
        )
    else:
        df_point = pd.DataFrame({
            "lat": lat_list,
            "lon": lon_list,
            "color": color_list,
        })
        df_point["tooltip_text"] = "<b>座標:</b> [" + df_point["lon"].astype(str) + ", " + df_point["lat"].astype(str) + "]"
    # 撮影者の移動軌跡(全て)
    df_line = pd.DataFrame({
        "path": path_list,
        "color": path_color_list,
    })
    # 撮影者の移動軌跡(撮影時)
    df_heading_line = pd.DataFrame({
        "heading": heading_line_list
    })
    # マップへのオブジェクト配置
    point_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_point,
        get_position='[lon, lat]',
        get_radius=0.5,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
        highlight_color=[255, 255, 0]
    )
    line_layer = pdk.Layer(
        "PathLayer",
        data=df_line,
        get_path='path',
        get_color="color",
        width_scale=0.5,
        width_min_pixels=2,
        rounded=True
    )
    heading_line_layer = pdk.Layer(
        "PathLayer",
        data=df_heading_line,
        get_path='heading',
        get_color=[0, 191, 171],
        width_scale=0.25,
        width_min_pixels=1,
    )
    poi_layer = pdk.Layer(
        "IconLayer",
        data=df_poi,
        get_position='[lon, lat]',
        get_icon="icon",
        get_size=2,
        get_color=[255, 0, 0],
        size_scale=15,
        pickable=True,
        icon_atlas="assets/pin_icon.png",
        icon_mapping={
            "marker": {
                "x": 0,
                "y": 0,
                "width": 600,
                "height": 800,
                "anchorX": 300,
                "anchorY": 400,
                "mask": True
            }
        }
    )
    if selected_mode == "Temporal IoU":
        if selected_radius_setting == "一律":
            df_geofence = pd.DataFrame({
                'lat': poi_lat_list,
                'lon': poi_lon_list,
                'radius': [float(all_radius)]*6
            })
        elif selected_radius_setting == "個別":
            df_geofence = pd.DataFrame({
                'lat': poi_lat_list,
                'lon': poi_lon_list,
                'radius': [float(r) for r in input_radius]
            })
        circle_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_geofence,
            get_position="[lon, lat]",
            get_radius="radius",
            radius_units="'meters'",
            get_fill_color="[0, 191, 171, 100]", 
            get_line_color="[0, 191, 171]",
            line_width_min_pixels=2,
        )

if selected_mode == "ヒートマップ":
    if heatmap_layer:
        view_state = pdk.ViewState(
            latitude=heat_avg_lat if heat_avg_lat else 35.0,
            longitude=heat_avg_lon if heat_avg_lon else 135.0,
            zoom=15,
            pitch=0,
            bearing=0
        )
        deck = pdk.Deck(
            layers=[heatmap_layer],
            initial_view_state=view_state,
            tooltip=True,
            map_style="light"
        )
        st.pydeck_chart(deck, width="stretch")

elif selected_mode in ["全体軌跡", "撮影軌跡", "Temporal IoU"]:
    view_state = pdk.ViewState
    if selected_mode == "全体軌跡":
        lat_mean = np.mean(lat_list)
        lon_mean = np.mean(lon_list)
        bounds = [min(lat_list), min(lon_list), max(lat_list), max(lon_list)]
        zoom = calc.calculate_zoom(bounds)
        view_state = pdk.ViewState(latitude=lat_mean, longitude=lon_mean, zoom=zoom)
    elif selected_mode == "撮影軌跡" and view_lat_list:
        lat_mean = np.mean(view_lat_list)
        lon_mean = np.mean(view_lon_list)
        bounds = [min(view_lat_list), min(view_lon_list), max(view_lat_list), max(view_lon_list)]
        zoom = calc.calculate_zoom(bounds)
        view_state = pdk.ViewState(latitude=lat_mean, longitude=lon_mean, zoom=zoom)
    elif selected_mode == "Temporal IoU":
        lat_mean = np.mean(lat_list)
        lon_mean = np.mean(lon_list)

        if lat_list and lon_list:
            bounds = [min(lat_list), min(lon_list), max(lat_list), max(lon_list)]
        else:
            bounds = [39.7, 140.0, 39.8, 140.1]

        zoom = calc.calculate_zoom(bounds)
        view_state = pdk.ViewState(latitude=lat_mean, longitude=lon_mean, zoom=zoom)
    
    if selected_mode == "Temporal IoU":
        deck = pdk.Deck(
            map_style="light",
            layers=[circle_layer, heading_line_layer, line_layer, point_layer, poi_layer],
            initial_view_state=view_state,
            tooltip={"html": "{tooltip_text}", "style": {"backgroundColor": "white", "color": "black", "fontFamily": "sans-serif"}}
        )
    else:
        deck = pdk.Deck(
            map_style="light",
            layers=[heading_line_layer, line_layer, point_layer, poi_layer],
            initial_view_state=view_state,
            tooltip={"html": "{tooltip_text}", "style": {"backgroundColor": "white", "color": "black", "fontFamily": "sans-serif"}}
        )
    st.pydeck_chart(deck, width="stretch")