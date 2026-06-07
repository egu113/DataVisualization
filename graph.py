import plotly.graph_objects as go
import plotly.express as px
import data_storage as ds
import streamlit as st
import calc
import pandas as pd
import pprint
import pydeck as pdk



# 複折れ線グラフの作成
def create_multiple_lines_graph(direction_difference_dict, poi_name_list):
    for key, all_lines in direction_difference_dict.items():
        st.caption(poi_name_list[key])
        fig = go.Figure()
        for i, line_data in enumerate(all_lines):
            fig.add_trace(go.Scatter(
                y=line_data["data"],
                mode='lines+markers',
                name=line_data["name"]
            ))
        fig.update_layout(
            margin=dict(l=50, r=30, t=40, b=50),
            height=550,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, width='stretch', key=f"multi_line_{key}")


# 折れ線グラフの作成
def create_line_graph(list, poi_name_list, caption=True, unique_key=None):
    fig = go.Figure()
    if caption:
        st.caption(poi_name_list[list[0]])
    fig.add_trace(go.Scatter(
        y=list[1],
        mode='lines+markers',
        name='角度差',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=4)
    ))
    
    fig.add_shape(
        type="line",
        x0=0, x1=len(list[1]) - 1,
        y0=0, y1=0,
        line=dict(color="red", width=2, dash="dash"),
    )
    
    fig.update_layout(
        yaxis=dict(
            range=[-180, 180]
        ),
        margin=dict(l=50, r=30, t=40, b=50),
        height=550,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    chart_key = unique_key if unique_key else f"line_{list[0]}"
    st.plotly_chart(fig, width='stretch', key=chart_key)



# タイムライングラフの作成
def create_timeline_graph(data_list, flame_in_list, i, timeline_data, poi_id, poi_name_list):
    pprint.pprint(data_list)

    df_graph = pd.DataFrame(data_list)
    st.caption(f"{poi_name_list[poi_id]} データ数: {len(data_list)}")

    current_flame_timeline = flame_in_list[i]["flame_in"]

    combined_flame_timeline = []
    for block in timeline_data.get("flame_in", []):
        if block["id"] == poi_id:
            combined_flame_timeline.extend(block["flame_in"])

    geofence_y_pos = 2
    orig_flame_y_pos = 1 
    json_flame_y_pos = 0

    inside_y = [geofence_y_pos if d["status"][0] == "inside" else None for d in data_list]
    base_geofence_y = [geofence_y_pos] * len(df_graph)
    
    orig_flame_y = [
        orig_flame_y_pos if (d["status"][0] == "inside" and d["status"][1] == "flame_in") else None 
        for d in data_list
    ]
    base_orig_flame_y = [orig_flame_y_pos] * len(df_graph)

    json_flame_y = []
    for idx in range(len(df_graph)):
        if idx < len(current_flame_timeline) and current_flame_timeline[idx]:
            json_flame_y.append(json_flame_y_pos)
        else:
            json_flame_y.append(None)
    base_json_flame_y = [json_flame_y_pos] * len(df_graph)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_graph.index, y=base_geofence_y, mode='lines',
        line=dict(color='#F0F0F0', width=2), hoverinfo='skip', showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=df_graph.index, y=inside_y, mode='lines+markers',
        name='Geofence Inside',
        line=dict(color='#00BFAF', width=12), marker=dict(size=12, symbol='circle'),
        connectgaps=False,
        hovertemplate='Index: %{x}<br>Geofence: Inside<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=df_graph.index, y=base_orig_flame_y, mode='lines',
        line=dict(color='#F0F0F0', width=2), hoverinfo='skip', showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=df_graph.index, y=orig_flame_y, mode='lines+markers',
        name='Original Flame In',
        line=dict(color='#FFA500', width=12), marker=dict(size=12, symbol='circle'),
        connectgaps=False,
        hovertemplate='Index: %{x}<br>Orig Flame: In<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=df_graph.index, y=base_json_flame_y, mode='lines',
        line=dict(color='#F0F0F0', width=2), hoverinfo='skip', showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=df_graph.index, y=json_flame_y, mode='lines+markers',
        name='JSON Flame In',
        line=dict(color='#FF6B6B', width=12), marker=dict(size=12, symbol='circle'),
        connectgaps=False,
        hovertemplate='Index: %{x}<br>JSON Flame: In<extra></extra>'
    ))

    # レイアウト設定
    fig.update_layout(
        margin=dict(l=120, r=30, t=10, b=30),
        height=240,
        showlegend=False,
        yaxis=dict(
            tickvals=[0, 1, 2],
            ticktext=["JSON Flame In", "Orig Flame In", "Inside Geofence"],
            showgrid=False,
            zeroline=False,
            showline=False,
            range=[-0.6, 2.6]
        ),
        xaxis=dict(
            showgrid=False,
            title="Time / Index"
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig, width='stretch', key=f"timeline_{poi_id}_{i}")



# ヒートマップの作成
def create_heatmap(union_dict, selected_attention_poi, target_id):
    heatmap_coords = []    
    if selected_attention_poi == "全て":
        for poi_id, coords in union_dict.items():
            heatmap_coords.extend(coords)
    else:
        heatmap_coords = union_dict.get(target_id, [])
    st.write(f"データ数: {len(heatmap_coords)} ")
    df_heat = pd.DataFrame(heatmap_coords, columns=["lat", "lon"])

    avg_lat = df_heat["lat"].mean()
    avg_lon = df_heat["lon"].mean()

    heatmap_layer = pdk.Layer(
        "HeatmapLayer",
        data=df_heat,
        get_position="[lon, lat]", 
        radius_pixels=30, 
        intensity=1,
        threshold=0.05,
    )

    return heatmap_layer, avg_lat, avg_lon