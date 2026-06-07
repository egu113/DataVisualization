import math
from geopy.distance import geodesic

# ズーム値の計算
def calculate_zoom(bounds, map_width_px=800, map_height_px=600, padding=0.08):
    min_lat, min_lon, max_lat, max_lon = bounds
    
    # 緯度差をラジアンに変換
    lat_fraction = (mercator_y(max_lat) - mercator_y(min_lat)) / math.pi
    lon_fraction = (max_lon - min_lon) / 360.0

    # 水平方向と垂直方向のズーム
    zoom_x = math.log2(map_width_px / 256.0 / lon_fraction)
    zoom_y = math.log2(map_height_px / 256.0 / lat_fraction)

    zoom = min(zoom_x, zoom_y) * (1 - padding)
    return zoom



def mercator_y(lat):
    lat = math.radians(lat)
    return math.log(math.tan(lat/2 + math.pi/4))



# 線形補間
def interpolate_path(path, n):
    new_path = []
    for i in range(len(path) - 1):
        lon1, lat1 = path[i]
        lon2, lat2 = path[i + 1]
        for j in range(n):
            t = j / n
            new_path.append([
                lon1 + (lon2 - lon1) * t,
                lat1 + (lat2 - lat1) * t
            ])
    new_path.append(path[-1])
    return new_path



# 移動平均
def moving_average_path(path, window=3):
    smoothed = []
    for i in range(len(path)):
        start = max(0, i - window)
        end = min(len(path), i + window + 1)
        lons = [p[0] for p in path[start:end]]
        lats = [p[1] for p in path[start:end]]
        smoothed.append([sum(lons)/len(lons), sum(lats)/len(lats)])
    return smoothed



# 方向と始点から、終点の座標計算
def coor_calc(lat, lon, bearing_deg, distance_m):
    # 度 → ラジアン
    bearing = math.radians(bearing_deg)
    lat_rad = math.radians(lat)
    # メートル → 度
    d_lat = (distance_m * math.cos(bearing)) / 111320
    d_lon = (distance_m * math.sin(bearing)) / (111320 * math.cos(lat_rad))
    lat2 = lat + d_lat
    lon2 = lon + d_lon
    return lat2, lon2



# 二つの座標から方向計算
def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = (
        math.cos(lat1) * math.sin(lat2)
        - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    )

    bearing = math.atan2(x, y)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    return bearing



# 二つの方向から角度差を計算
def angle_difference_calc(dir_user_list, dir_poi_list):
    difference = []
    for dir1,dir2 in zip(dir_user_list, dir_poi_list):
        diff = dir1 - dir2
        correct_diff = (diff + 180) % 360 - 180
        difference.append(correct_diff)
    return difference



# ジオフェンスの内外判定
def geofence_inside_outside_determination(center_lat, center_lon, radius, lat, lon):
    distance = geodesic((center_lat, center_lon), (lat, lon)).meters
    return distance <= float(radius)