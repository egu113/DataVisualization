import calc
import itertools



# ==========================================================
# gpsデータ格納
# ==========================================================

def locations_storage(locations, mode):
    # 全ての軌跡
    lat_list = []
    lon_list = []

    # 水平精度による色分け軌跡
    path_list = []
    path_color_list = []
    # 軌跡を区分けするための一時変数
    current_path = []

    # 撮影時のみの軌跡
    path_not_color_list = []
    # 軌跡を区分けするための一時変数
    current_path_not_color = []

    # 水平精度リスト
    accuracy_list = []
    # 時間リスト
    time_list = []

    for d in locations:
        # 全体モード
        if mode == "全体軌跡":
            if current_path:        # pathの第2点以降である
                if horizontal_judge(accuracy_list[-1]) and not horizontal_judge(d["horizontalAccuracy"]):     # 黒から赤
                    path_color_list.append([0,0,0])
                    current_path.append([d["longitude"], d["latitude"]])
                    path_list.append(current_path)  # 水平精度の区切り
                    current_path = []
                elif not horizontal_judge(accuracy_list[-1]) and horizontal_judge(d["horizontalAccuracy"]):   # 赤から黒
                    path_color_list.append([255,0,0])
                    current_path.append([d["longitude"], d["latitude"]])
                    path_list.append(current_path)  # 水平精度の区切り
                    current_path = []
            lat_list.append(d["latitude"])
            lon_list.append(d["longitude"])
            accuracy_list.append(d["horizontalAccuracy"])
            current_path.append([d["longitude"], d["latitude"]])
            time_list.append(d["time"])
            continue
        # 撮影モード
        if d["isCmaeraActiove"]:    # カメラはONである
            if current_path:        # カメラがONかつ、pathの第2点以降である
                if horizontal_judge(accuracy_list[-1]) and not horizontal_judge(d["horizontalAccuracy"]):     # 黒から赤
                    path_color_list.append([0,0,0])
                    current_path.append([d["longitude"], d["latitude"]])
                    path_list.append(current_path)  # 水平精度の区切り
                    current_path = []
                elif not horizontal_judge(accuracy_list[-1]) and horizontal_judge(d["horizontalAccuracy"]):   # 赤から黒
                    path_color_list.append([255,0,0])
                    current_path.append([d["longitude"], d["latitude"]])
                    path_list.append(current_path)  # 水平精度の区切り
                    current_path = []
            lat_list.append(d["latitude"])
            lon_list.append(d["longitude"])
            accuracy_list.append(d["horizontalAccuracy"])
            current_path.append([d["longitude"], d["latitude"]])
            current_path_not_color.append([d["longitude"], d["latitude"]])
            time_list.append(d["time"])
        else:                       # カメラOFFである
            if current_path:
                if horizontal_judge(accuracy_list[-1]):
                    path_color_list.append([0,0,0])
                else:
                    path_color_list.append([255,0,0])
                path_list.append(current_path)      # pathの区切り
                current_path = []
            if current_path_not_color:
                path_not_color_list.append(current_path_not_color)
                current_path_not_color = []
    if current_path:
        if horizontal_judge(accuracy_list[-1]):
            path_color_list.append([0,0,0])
        else:
            path_color_list.append([255,0,0])
        path_list.append(current_path)      # pathの区切り
        current_path = []
    if current_path_not_color:
        path_not_color_list.append(current_path_not_color)
        current_path_not_color = []

    color_list = point_color(accuracy_list)
    return lat_list, lon_list, color_list, path_list, path_color_list, time_list, path_not_color_list



# ==========================================================
# 方向データ格納
# ==========================================================

def headings_storage(headings, times):
    poi_id_list = [d["poi_id"] for d in headings]
    order_list = [d["order"] for d in headings]
    value = [d["value"] for d in headings]
    heading_list = [[item["heading"] for item in sub_list] for sub_list in value]
    heading_pieces_list = [d["heading"] for sub_list in value for d in sub_list]
    time_list = [d["time"] for sub_list in value for d in sub_list]
    new_heading_pieces_list = []
    list_idx = []
    for n in times:
        idx,_ = find_nearest(n, time_list)
        new_heading_pieces_list.append(heading_pieces_list[idx])
        list_idx.append(idx)
    new_heading_list = filter_nested_list_by_global_indices(heading_list, list_idx)
    return new_heading_pieces_list, new_heading_list, poi_id_list



# 方向と座標からlineのための座標・方向を計算
def extend_line(lat_list, lon_list, heading_list, poi_id_list, target_id=0, attention_mode="全て"):
    heading_line = []
    view_lat_list = []
    view_lon_list = []
    count = 0
    if attention_mode == "全て":
        # 全てのPOIの方向を描画
        flat_lat_list = list(itertools.chain.from_iterable(lat_list))
        flat_lon_list = list(itertools.chain.from_iterable(lon_list))
        flat_heading_list = list(itertools.chain.from_iterable(heading_list))
        for lat, lon, heading in zip(flat_lat_list, flat_lon_list, flat_heading_list):
            end_lat, end_lon = calc.coor_calc(lat, lon, heading, 50)
            current_start = [lon, lat]
            current_goal = [end_lon, end_lat]
            heading_line.append([current_start, current_goal])
            view_lat_list.extend([lat, end_lat])
            view_lon_list.extend([lon, end_lon])
    elif attention_mode == "POI ID":
        # 特定のPOIのみ描画
        for poi_id in poi_id_list:
            if target_id == poi_id:            
                for lat, lon, heading in zip(lat_list[count], lon_list[count], heading_list[count]):
                    end_lat, end_lon = calc.coor_calc(lat, lon, heading, 50)
                    current_start = [lon, lat]
                    current_goal = [end_lon, end_lat]
                    heading_line.append([current_start, current_goal])
                    view_lat_list.extend([lat, end_lat])
                    view_lon_list.extend([lon, end_lon])
            count += 1
    else:
        # 特定の撮影順のみ描画
        if target_id <= len(lat_list):
            target_id -= 1
            for lat, lon, heading in zip(lat_list[target_id], lon_list[target_id], heading_list[target_id]):
                end_lat, end_lon = calc.coor_calc(lat, lon, heading, 50)
                current_start = [lon, lat]
                current_goal = [end_lon, end_lat]
                heading_line.append([current_start, current_goal])
                view_lat_list.extend([lat, end_lat])
                view_lon_list.extend([lon, end_lon])

    return heading_line, view_lat_list, view_lon_list



# poiデータ格納
def poi_storage(poi):
    name_list = []
    lat_list = []
    lon_list = []    
    radius_list = []
    for d in poi:
        name_list.append(d["name"])
        lon, lat = d["coordinates"][0]
        lat_list.append(lat)
        lon_list.append(lon)
        radius_list.append(d["radius"])

    return name_list, lat_list, lon_list, radius_list



# 水平精度によるpointの色分け
def point_color(list):
    color_list = []
    for d in list:
        if  d >= 10:
            color_list.append([0, 0, 0])
        else:
            color_list.append([255, 0, 0])
    return color_list



# 水平精度の基準判定
def horizontal_judge(num):
    if num >= 8:
        return True
    else:
        return False



# 配列から特定の値に最も近い値を返す
def find_nearest(value, array):
    idx, val = min(
        enumerate(array),
        key=lambda x: abs(x[1] - value)
    )
    return idx, val



# 階層構造を維持したまま、全体を通したインデックスで要素をフィルタリングする
def filter_nested_list_by_global_indices(nested_list, target_indices):
    filtered_groups = []
    global_counter = 0
    for sub_list in nested_list:
        sub_group = []
        for item in sub_list:
            count = target_indices.count(global_counter)            
            for _ in range(count):
                sub_group.append(item)                
            global_counter += 1            
        filtered_groups.append(sub_group)
        
    return filtered_groups



# poiと撮影者の座標から方向計算
def direction_user_to_poi(lat_list, lon_list, lat_poi, lon_poi):
    direction_list = []
    for lat,lon in zip(lat_list, lon_list):
        direction = calc.calculate_bearing(lat, lon, lat_poi, lon_poi)
        direction_list.append(direction)
    return direction_list



# 撮影方向とpoi方向との差を計算して整理
def difference_direction_between_user_and_poi(path_not_color_list, division_heading_list, poi_id_list, poi_lat_list, poi_lon_list, return_mode):
    graph_location_data = [
        {
            "lon": [coord[0] for coord in sub_list],
            "lat": [coord[1] for coord in sub_list]
        }
        for sub_list in path_not_color_list
    ]
    difference_dict = {}
    difference_list = []
    order_list = []
    for i, (location, heading, poi_id) in enumerate(zip(graph_location_data, division_heading_list, poi_id_list)):
        if poi_id < 6:  # 今のところ、事前に設定したpoi以外はスキップ
            lat = location["lat"]
            lon = location["lon"]
            poi_lat = poi_lat_list[poi_id]
            poi_lon = poi_lon_list[poi_id]
            poi_dir = direction_user_to_poi(lat, lon, poi_lat, poi_lon)
            difference = calc.angle_difference_calc(heading, poi_dir)
            if return_mode == "dict":
                difference_dict.setdefault(poi_id, []).append(difference)
            elif return_mode == "list":
                difference_list.append((poi_id, difference))
            order_list.append(i+1)
    
    if return_mode == "dict":
        return difference_dict, order_list
    elif return_mode == "list":
        return difference_list, order_list



def color_change_by_geofence(inside_outside_mask):
    total_index = 0
    color_list = []
    for group in inside_outside_mask:
        for is_inside in group: 
            if is_inside:
                color_list.append([0, 0, 255])
            else:
                color_list.append([255, 0, 0])
            total_index += 1
    return color_list