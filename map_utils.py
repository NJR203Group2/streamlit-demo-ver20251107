import streamlit as st
import folium # 匯入 Folium，這是用於建立互動式 Leaflet 地圖的 Python 函式庫。它負責地圖本身和標記的繪製。
import osmnx as ox # 匯入 OSMnx，這是一個強大的工具，用於從 OpenStreetMap (OSM) 下載、處理和分析地理空間數據（例如查詢周邊設施）。
from folium.plugins import MarkerCluster # 匯入 MarkerCluster，用於將地圖上密集的小標記自動分組，讓地圖在縮小時看起來更清晰。

# --- 1. OSM 設施標籤對應字典 ---
# 定義您感興趣的 OSM 設施類型（Key: OSM標籤, Value: (顏色, 圖標)）
# osm_icon_options = {
#     'restaurant': ('green', 'cutlery'),    # 餐廳/餐飲
#     'cafe': ('lightgreen', 'coffee'),      # 咖啡館
#     'atm': ('blue', 'money'),              # 提款機/銀行
#     'bus_stop': ('darkred', 'bus'),        # 公車站
#     'bicycle_rental': ('orange', 'bicycle'), # 自行車租賃
#     'parking': ('gray', 'parking'),        # 停車場
#     'public_transport': ('darkpurple', 'subway'), # 捷運/地鐵
# }

# 將使用者友好的設施名稱映射到 OSM 標籤
osm_facility_mapping = {
    '餐廳': {
        'amenity': ['restaurant', 'cafe', 'food_court', 'fast_food', 'pub'],
        'cuisine': True  # 通常用於描述食物服務設施（主要是餐廳、咖啡館等）提供哪種類型的料理。
        # 常見的 cuisine 標籤值 (Value)： chinese, italian, japanese, burger, pizza, vietnamese, taiwanese, 等等。
    },
    '購物': {
        'shop': ['clothing', 'boutique', 'department_store', 'mall', 'supermarket', 'bakery']
    },
    '住宿': {
        'amenity': ['hotel', 'guest_house'],
        'tourism': ['hotel', 'hostel', 'motel']
    },
    '交通': {
        'public_transport': ['station', 'stop'],
        'railway': ['station', 'subway_entrance'],
        'amenity': ['bus_station', 'parking']
    }
}

def _build_osm_query_tags(facility_options): # 根據 Streamlit 側邊欄的選項，建立 osmnx 所需的查詢標籤字典。
    query_tags = {} # 準備一個要回傳給osm的查詢字典
    for f_display in facility_options: # 輸入的list，每個標籤都拿出來 
        osm_tags = osm_facility_mapping.get(f_display) # ex:用戶選擇**餐廳**，那會get出**對應 OSM 標籤的字典(amenity、cuisine)**
        if osm_tags: # 檢查是否取得 OSM 標籤組（即非 None），如果使用者選擇了有效的中文類別。
            for key, values in osm_tags.items(): # 取出**amenity**，對應value為['restaurant', 'cafe', 'food_court', 'fast_food', 'pub']
                if key not in query_tags: # 如果最終查詢字典中還沒有這個 OSM Key (如 amenity)，則在該 Key 下建立一個 set，用於後續合併不同中文類別的標籤值，避免重複
                    query_tags[key] = set()
                
                if isinstance(values, list): # 如果 values 是列表，則將所有值加到 set 中 (合併不同中文類別的標籤值)
                    query_tags[key].update(values) 
                elif values is True:
                    # 如果設置為 True，表示查詢所有該類型（例如所有 cuisine）
                    query_tags[key] = True

    # 將 set 轉換為 list，以便 osmnx 的 features_from_point 函式能夠接受
    for key, value in query_tags.items():
        if isinstance(value, set):
            query_tags[key] = list(value)
            
    return query_tags

def draw_exhibition_map(selected_venue, locdict, facility_options, radius):
    '''
    主要繪圖函式：繪製中心展館標記和周邊 OSM 設施標記。

    Args:
        selected_venue (str): 被選中的展館名稱。
        locdict (dict): 所有展館的座標字典。
        facility_options (list): 使用者在側邊欄選擇的周邊設施清單。
        radius (int): 使用者在側邊欄設定的搜尋半徑 (公尺)。

    Returns:
        folium.Map: 繪製完成的 Folium 地圖物件。
    '''
    center_lat, center_lng = locdict[selected_venue]
    center_point = (center_lat, center_lng)
    
    # 1. 初始化地圖 - 建立 Folium 地圖物件。設置地圖中心點 (center_point)、縮放等級 (zoom_start) 和地圖風格 (tiles = 'OpenStreetMap')。
    exmap = folium.Map(location = center_point, zoom_start = 18, tiles = 'OpenStreetMap') # , tiles = 'CartoDB dark_matter'
    
    # 2. 繪製中心展館標記 (使用 Icon 讓它更醒目)
    folium.Marker(
        center_point, 
        popup = f'**:red[{selected_venue}]**',
        tooltip = f'更多資訊 : {selected_venue}',
        icon = folium.Icon(color='orange', icon='palette', prefix='fa')
    ).add_to(exmap)
    
    # 3. 準備 OSM 查詢標籤
    query_tags = _build_osm_query_tags(facility_options) # 呼叫輔助函式，取得 osmnx 所需的查詢標籤。
    
    # --- 偵錯點 A ---
    # 在 Streamlit 側邊欄顯示 OSM Tags 和半徑
    st.sidebar.markdown('---')
    st.sidebar.markdown(f'**🛠️ 搜尋資訊**')
    st.sidebar.write(f'  - **場館**：{selected_venue}')
    st.sidebar.write(f'  - **半徑**：{radius} 公尺')
    # st.sidebar.write(f'  - **OSM Tags**：{query_tags}')

    # 4. 執行 OSM 查詢並繪製周邊設施
    if query_tags:
        # 使用 MarkerCluster 幫助管理大量標記，避免地圖混亂
        marker_cluster = MarkerCluster().add_to(exmap)
        
        try:
            # 查詢符合標籤的 POI
            gdf = ox.features.features_from_point( # 使用 osmnx 根據中心點、使用者定義的標籤 (tags) 和搜尋半徑 (dist) 查詢周邊的 POI 數據，結果儲存在 GeoDataFrame (gdf) 中。
                center_point = center_point,
                tags = query_tags,
                dist = radius 
            )
            # --- 資訊點 B ---
            st.sidebar.write(f'  - **查詢結果**：**{len(gdf)} 筆** 相關設施')
            st.sidebar.write(f'  - **查詢部分結果**：**{list(set(gdf.get('name')))[:10]}**')

            for _, row in gdf.iterrows(): # 遍歷所有項目，會同時回傳index 和 column
                if row.geometry.geom_type == 'Point':
                    lat, lon = row.geometry.y, row.geometry.x
                    
                    # 獲取 POI 資訊
                    name = row.get('name', '未命名設施')
                    category_key = next((k for k in ['amenity', 'shop', 'tourism', 'public_transport'] if row.get(k)), '設施')
                    category = row.get(category_key, '其他')
                    
                    # 根據類別設定顏色和圖示
                    color = 'blue'
                    icon = 'info-sign'
                    if category_key == 'amenity' and category in ['restaurant', 'cafe', 'food_court']:
                        color = 'green'
                        icon = 'cutlery'
                    elif category_key == 'shop':
                        color = 'purple'
                        icon = 'shopping-cart'
                    elif category_key == 'public_transport' or category_key == 'railway':
                        color = 'darkred'
                        icon = 'bus'
                        
                    # 繪製 Marker
                    folium.Marker(
                        location = [lat, lon],
                        popup = f'**{name}**<br>類型: {category_key.capitalize()}: {category}',
                        tooltip = name,
                        icon=folium.Icon(color=color, icon=icon, prefix='fa')
                    ).add_to(marker_cluster) # 新增到 MarkerCluster
                    
        except Exception as e:
            # 顯示查詢錯誤
            st.warning(f"OSM 查詢周邊設施發生錯誤，請稍候再試或檢查網路: {e}")
            
    return exmap