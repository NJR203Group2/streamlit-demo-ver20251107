import streamlit as st # 導入 Streamlit 函式庫，用於建構 Web 應用程式介面
from streamlit_folium import st_folium # 導入用於在 Streamlit 中嵌入 Folium 地圖的函式庫
import pandas as pd # 導入 Pandas 函式庫，通常用於處理和展示數據
from pathlib import Path # 導入 Path 函式庫，用於處理檔案路徑
import datetime as dt # 導入 datetime 函式庫，用於處理日期和時間
# from io import StringIO # 導入 StringIO 函式庫，用於在記憶體中處理字串 IO
import folium # 導入 Folium 函式庫，用於創建互動式地圖
# from fuzzywuzzy import fuzz, process
from rapidfuzz import fuzz, process # 導入 rapidfuzz 函式庫，用於高效的模糊字串匹配 (取代 fuzzywuzzy)
from map_utils import draw_exhibition_map
from dotenv import load_dotenv
import os

# 加載 .env 文件，讀取.env檔案中的key值
load_dotenv() 
FILEPATH = os.getenv('FEILPATH')

# 展覽資訊匯入 - 目前只有松山文創園區
def readfile(usr_selected, pathinfo) -> pd.DataFrame:
    fileym = dt.datetime.today().strftime('%Y_%m_%d')
    filedict = {'松山文創園區' : 'exhibition_info_', 
                '國立臺灣師範大學-師大美術館' : 'exhibition_info_',
                '台北當代藝術館' : 'exhibition_info_',
                '華山1914文化創意產業園區' : 'exhibition_info_',
                '國立故宮博物院' : 'exhibition_info_',
                '富邦美術館' : 'exhibition_info_',
                '緯育TibaMe附設台北職訓中心' : 'exhibition_info_'}
    filenm = f'{filedict[usr_selected]}{fileym}.csv'
    infopath = Path(str(pathinfo)) / filenm
    exhinfo = pd.read_csv(infopath, sep = ',')
    return exhinfo


# --- 頁面配置與標題區塊 ---
st.set_page_config(page_title = '展覽雷達：雙北展覽空間與文化趨勢地圖', page_icon = '📊', layout = 'wide') # 設定 Streamlit 頁面標題和圖示，並設定為寬模式布局

st.markdown(f'# **:orange[展覽雷達：雙北展覽空間與文化趨勢地圖]**') # 顯示主標題
st.markdown(f'> 目前日期 &ensp; {dt.datetime.today().strftime('%Y-%m-%d     %H:%M')}') # 顯示當前日期和時間
st.markdown(f'#### 主體發想及理念') # 顯示理念標題
st.markdown(f'''當前城市文化的脈動，往往藏在展覽與活動的空間分布中。            
            台北與新北作為台灣最具文化能量的地區，擁有豐富多元的展覽場域，從美術館、獨立藝廊到快閃策展空間，皆反映著城市居民的創意與思潮。  
            然而，這些文化活動資訊分散於不同平台與社群媒介，往往難以即時掌握。''')
            
st.markdown(f'''於是，我們發想了:violet[**「展覽雷達：雙北展覽空間與文化趨勢地圖」**]——以資料整合與自然語言分析為核心，
            將展覽資訊轉化為可視化的文化地圖。  
            透過地理、主題與時間的多維觀察，
            讓數據成為理解城市文化生態的窗口，重新看見雙北的創作能量如何在不同空間與時刻綻放。''')
st.markdown('---')

# --- 資料與設定區塊 ---
# 定義場館位置：字典，鍵為場館名稱，值為 [緯度, 經度]
locdict = {
    '松山文創園區' : [25.04386248376348, 121.56062801964043],
    '國立臺灣師範大學-師大美術館' : [25.02779364137553, 121.53009903793101],
    '台北當代藝術館' : [25.05085534309318, 121.51899525374114],
    '華山1914文化創意產業園區' : [25.04408280144262, 121.5293597040736],
    '國立故宮博物院' : [25.102380745430075, 121.54848396046067],
    '富邦美術館' : [25.039413601820286, 121.57120511116887],
    '緯育TibaMe附設台北職訓中心' : [25.05224018699662, 121.5432011459169]
}

# 場館圖片
venue_image_urls = {
    '松山文創園區': 'https://www-ws.gov.taipei/001/Upload/686/relpic/45246/119026/a521ecda-6ee6-4b86-8d6e-5572f432df5a.jpg', # 替換為實際圖片URL
    '國立臺灣師範大學-師大美術館': 'https://www.artmuse.ntnu.edu.tw/wp-content/uploads/2023/04/%E5%B8%AB%E5%A4%A7%E7%BE%8E%E8%A1%93%E9%A4%A8-03-1024x681.jpg',
    '台北當代藝術館': 'https://grace-520.com/wp-content/uploads/2025/03/%E5%8F%B0%E5%8C%97%E5%AE%A4%E5%85%A7%E6%99%AF%E9%BB%9E-%E5%8F%B0%E5%8C%97%E7%95%B6%E4%BB%A3%E7%BE%8E%E8%A1%93%E9%A4%A8-1.jpg',
    '華山1914文化創意產業園區': 'https://upload.wikimedia.org/wikipedia/commons/5/55/Huashan_1914%2C_Syntrend_and_Jinshan_e01_20150701.jpg',
    '國立故宮博物院': 'https://www.travel.taipei/content/images/attractions/221739/1920x1080_attractions-image-hrvtkvaowueb7-w8--qy9g.jpg',
    '富邦美術館': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Fubon_Art_Museum_20241127.jpg/1200px-Fubon_Art_Museum_20241127.jpg',
    '緯育TibaMe附設台北職訓中心': 'https://cdn-static.tibame.com/template/202149/images/178e3b43-fd7f-4624-a63f-dc6ff45787d0.png'
}

# tag - 未完成!!跟組員再討論一下!!
venue_hashtags = {
    '松山文創園區': '#文創基地 #設計展覽 #市集活動',
    '國立臺灣師範大學-師大美術館': '#校園藝廊 #美術教育 #當代學術',
    '台北當代藝術館': '#MOCA #當代藝術 #議題探討',
    '華山1914文化創意產業園區': '#紅磚建築 #文化聚落 #展演空間',
    '國立故宮博物院': '#中華文物 #國寶級 #歷史典藏',
    '富邦美術館': '#企業收藏 #現代藝術 #信義區新館',
    '緯育TibaMe附設台北職訓中心': '#職訓中心 #數據分析 #技能培訓'
}

# 場館簡介
palintrod = {
    '松山文創園區': '''松山文創園區定位為「臺北市原創基地」，自2011年對外開放以來，肩負帶動城市原創力與軟實力的使命。園區前身為松山菸廠，保留了歷史建築，並規劃了「跨界實驗」、「創意學院」等五大創新策略。這裡作為國際級的文創聚落，致力於扶植原創人才，鼓勵創新與實驗性創作。園區提供從創業育成到品牌建立，從核心創作到商業運用的全流程支持，實現設計發想、測試製作到國際鏈結。松山文創園區已成為台灣重要的創意樞紐，民眾可在此平台參與藝術與原創，體驗無限的創意與活力。''',
    '國立臺灣師範大學-師大美術館': '''師大美術館承載自1947年以來國立臺灣師範大學師生與校友的美術創作實踐，典藏超過4000件藝術作品，是臺灣近代美術史的重要見證者。美術館以「典藏研究轉譯」、「美術當代策展」、「跨域參與共學」等為核心，旨在擁抱校園與社區，垂直連接不同世代與族群，並積極與國際交流藝術思維。標誌設計上，以獨特的建築形體為靈感，不對稱的三角形展現創新與突破，虛實相映的佈局則反映其訊息整合與開放性。美術館以書法墨色為基底的代表色彩，蘊含著東方文化的儒雅與師大綿延的人文素養，致力於傳承在地文化並與全球接軌。''',
    '台北當代藝術館': '''台北當代藝術館館舍建築落成於1921年，原為日治時期的「建成尋常小學校」，後曾作為近五十年的台北市政府辦公廳舍，是驅動市政的神經中樞。1996年舊廈登錄為市定古蹟，並在古蹟再利用政策下，於2001年轉型為國內唯一的「當代藝術館」，與建成國中結合，創造了美術館與學校共用建物的先例。當代館位於歷史文化軸線的延展上，象徵帶動大同區再發展的新契機。作為台灣當代藝術的重要窗口，當代館自我期許推動多元風貌的藝術創作與展覽，激發民眾的新觀點和新思維，並為城市發展提供源源不絕的創意與活力。''',
    '華山1914文化創意產業園區': '''華山1914文創園區前身是歷史悠久的酒廠。自2002年行政院將其納入「創意文化園區」計畫後，經歷整修，拆除圍牆，並修復古蹟與歷史建築。2007年由臺灣文創發展股份有限公司入主經營，正式以「華山1914文創園區」重新營運。園區秉持「一本大書、一個舞台、一種風景、一所學校」的理念，旨在將華山轉型為台灣文創旗艦基地。華山走過百年風華，積極接軌國際，透過結合文化資產活化與再生的概念，導入文化、創意、藝術與設計等元素，提供民眾一個集展覽、表演、休閒於一體的多元文化體驗空間。''',
    '國立故宮博物院': '''國立故宮博物院典藏了匯集北平、熱河、瀋陽三處清宮的珍稀文物，是亞洲文物菁華與人類文化史上的瑰寶。故宮文物因緣際會來到臺灣，成為臺灣多元文化源流中極為重要的部分，肩負著承繼數千年中華文化之責。故宮致力於「深耕在地，邁向國際」的願景，施政原則聚焦在公共化、在地化、專業化、多元化、國際化及年輕化。近年來，故宮積極推動新故宮計畫，優化北部院區和南院空間設施，並以「參觀者本位之原則」提升整體服務品質，期盼強化其作為國際矚目博物館的專業與高度。''',
    '富邦美術館': '''富邦美術館經歷近10年籌備，於2024年5月在台北市信義區開啟嶄新場域。美術館以「藝術每一天 Art Every Day」為本質，旨在傳遞藝術帶來的幸福與喜悅。美術館積極關注台灣與世界各地的藝術家，抱持開放、積極的態度推動藝術對話與交流。其展覽聚焦現當代藝術，以激發觀者想像為目標，為信義區這片商業核心地帶注入了重要的文化與創意元素。美術館以綠意環繞的設計，為市民提供了一個全新的、充滿熱情與想像力的藝術空間。''',
    '緯育TibaMe附設台北職訓中心':'''緯育TibaMe於2015年由全球最大資通訊集團之一的緯創資通股份有限公司（Wistron）正式成立。其核心使命是以雲端科技服務為本，優化人才培育，積極發展數位教育創新商業模式。緯育致力於提供企業最佳的人才解決方案，並滿足個人在數位學習上的全方位需求。作為附設的台北職訓中心，它專注於提供專業的資訊科技（IT）、數據分析、AI 等高科技領域的技能培訓，是培養台灣數位轉型所需人才的重要基地。'''
}

# --- 周邊設施定義 ---

# 定義周邊設施的搜尋半徑（米）
radius = 500  # 搜尋半徑設為 500 公尺

# 場館名稱列表，等等用於用戶篩選
choices = list(locdict.keys())

# 用戶自行輸入搜尋
usr_input = st.sidebar.text_input('今天要去哪裡看展?')
st.markdown('---')

# 周圍環境篩選器 (位於側邊欄)
facility_options_choices = ['餐廳', '購物', '住宿', '交通']
facility_options_usr_choices = st.sidebar.multiselect(
    '周邊設施類型',  # 側邊欄 Multiselect 標題
    facility_options_choices,  # 供使用者選擇的選項
    default = ['餐廳'] # 預設選中的選項
)
# 搜尋半徑滑桿 (位於側邊欄)
radius = st.sidebar.slider('周圍半徑(公尺)', min_value = 500, max_value = 1500, value = 1000, step = 100) # 側邊欄 Slider，min=1500, max=1000 (此處應為 min=500, max=1500), 預設=1000, 步長=100

# --- 模糊搜尋邏輯區塊 ---
# 用戶搜尋比對：使用 rapidfuzz 進行模糊匹配
best_match = process.extract(usr_input, choices, limit = 3)
scor = sum([i[1] for i in best_match])
score_cutoff = 80
filtered_match = [i for i in best_match if i[1] >= score_cutoff]
cholist = [i[0] for i in filtered_match if int(i[1]) == best_match[0][1]]
default_venue = '緯育TibaMe附設台北職訓中心'
# --- 地圖顯示邏輯區塊 ---
if usr_input == '': # 都還沒有輸入時

    exmap = folium.Map(location = locdict[default_venue], zoom_start = 20) # 初始化 Folium

    image_url = venue_image_urls.get(default_venue, venue_image_urls[default_venue]) # 圖片擷取
    hashtags_list = venue_hashtags.get(default_venue, None) # hashtag擷取

    # 組合最終的 Popup HTML 內容
    popup_html_content = f'''
    <h4 font-weight:bold; style="color:#004080">{default_venue}</h4>
    <div style="margin-bottom: 10px;">
        <code style = "border-radius: 4px; font-family: monospace; color: #666; display: inline-block; background-color: #f0f0f0; font-size = 0.9em;">
        {hashtags_list}
        </code>
    </div>
    <img src="{image_url}" alt="緯育TibaMe附設台北職訓中心" style="width:250px; height:auto; border-radius: 10px;">'''

    iframe = folium.IFrame(html = popup_html_content, width = 400, height = 300)
    poppup = folium.Popup(iframe, max_width = 300)
    folium.Marker(
        locdict[default_venue], 
        popup = poppup, # 點擊出現資訊
        tooltip = f'{default_venue}<br>{hashtags_list}', # 游標移到上面出現的資訊
        icon = folium.Icon(color='red', icon='palette', prefix='fa') # 讓主標記更醒目
    ).add_to(exmap)
    # st.components.v1.html(exmap._repr_html_(), height = 1000)
    st_folium(exmap, width = 700, height = 500) # 使用 st_folium 顯示地圖

elif (scor == 0) or (len(filtered_match) == 0): # 沒有找到接近或符合的展館名稱
    st.warning('沒有接近或符合的展館名稱，請再重新輸入查詢:')

elif cholist: # 有找到符合或接近的場館名稱
    if len(cholist) > 1:
        selected = st.sidebar.selectbox('請選擇最適合的場館', cholist) # 讓使用者從最高分選項中選擇一個
    else:
        selected = cholist[0]
    
    # 顯示選擇的場館
    st.warning(f'你現在搜尋的是\n # **{selected}**') # 在上面顯示當前選擇的場館
    # exmap = folium.Map(location = locdict[selected], zoom_start = 18) # 創建地圖，以選定場館為中心，設定高縮放級別
    
    # 繪製地圖
    exmap = draw_exhibition_map(
        selected_venue = selected, 
        locdict = locdict, 
        facility_options = facility_options_usr_choices, 
        radius = radius
    )

    # 游標指到的地方增加的資訊
    image_url = venue_image_urls.get(selected, venue_image_urls[default_venue]) # 清單中抓出場館外觀的網址
    hashtags_list = venue_hashtags.get(selected, None) # hashtag擷取

    # 組合最終的 Popup HTML 內容
    popup_html_content = f'''
    <h4 font-weight:bold; style="color:#004080">{selected}</h4>
    <div style="margin-bottom: 10px;">
        <code style = "border-radius: 4px; font-family: monospace; color: #666; display: inline-block; background-color: #f0f0f0; font-size = 0.9em;">
        {hashtags_list}
        </code>
    </div>
    <img src="{image_url}" alt="{selected}" style="width:250px; height:auto; border-radius: 10px;">'''

    iframe = folium.IFrame(html = popup_html_content, width = 400, height = 300) # 增加的資訊框框大小
    poppup = folium.Popup(iframe, max_width = 300) # 圖片大小

    # 顯示選定場館的標記
    folium.Marker(
        locdict[selected], 
        popup = poppup, # 點擊出現資訊
        tooltip = f'{selected}<br>{hashtags_list}', # 游標移到上面出現的資訊
        icon = folium.Icon(color='orange', icon='palette', prefix='fa') # 改變標記 - 地圖上的icon
    ).add_to(exmap)

    # 讀取檔案
    exhinfo = readfile(selected, FILEPATH)
    
    # 資料處理
    newcol = ['展覽開始日期', '展覽結束日期', '展覽名稱', '展覽說明', '展覽地點', '官網網址', '展覽時間', '門票資訊', '備註']
    exhinfo.rename(columns = dict(zip(exhinfo.columns.tolist(), newcol)), inplace = True)
    all_exhibitions = ['請選擇您感興趣的展覽 (預設顯示全部)'] + exhinfo['展覽名稱'].unique().tolist()

    # 展覽圖片匯入
    img_path = os.getenv('IMGPATH')
    imgym = dt.datetime.today().strftime('%Y_%m_%d')
    imgPath = Path(str(img_path)) / (imgym + '_images') # 目前只有文創
    imgdict = {} # 用來裝圖片的路徑
    for i in imgPath.iterdir():
        if i.is_file():
            check = process.extract(i.name, exhinfo['展覽名稱'].unique().tolist(), limit = 1)
            imgdict[exhinfo['展覽名稱'].unique().tolist()[check[0][2]]] = i
        
    selected_exhibits = st.selectbox(
            label = '請選擇您感興趣的展覽：',
            options = all_exhibitions
        )

    default_col = ['展覽名稱', '展覽開始日期', '展覽結束日期', '展覽時間', '展覽地點', '門票資訊']
    printdf = exhinfo[exhinfo['展覽名稱'] == selected_exhibits] if selected_exhibits != '請選擇您感興趣的展覽 (預設顯示全部)' else exhinfo[default_col]
    all_col = printdf.columns.tolist()
    selected_cols = st.multiselect(
            label = "請選擇您需要的欄位：",
            options = all_col,
            default = default_col, # 預設選擇欄位
            placeholder = '請點開選擇'
        )

    # 版面配置
    col_map, col_list = st.columns([2, 3]) # 3/5 寬度給地圖, 2/5 寬度給清單
    with col_map:
        st.markdown(f'#### 🗺️ **:blue[{selected}]** 及其周邊設施')
        st_folium(exmap, width = 500, height = 800, use_container_width = True, key = 'folium_map') # 使用 st_folium 顯示地圖
    
    with col_list:

        st.markdown(f'#### 📌 **:orange[{selected}]** 場館簡介')
        st.markdown(f'{palintrod[selected]}')
        st.markdown('')
        
        selected_name = printdf['展覽名稱'].iloc[0]
        selected_cols_name = [col for col in selected_cols if col != '展覽名稱']
        if selected_exhibits != '請選擇您感興趣的展覽 (預設顯示全部)':

            st.markdown(f'#### 📚 **:orange[{selected}]** {'目前展覽清單' if selected_exhibits == '請選擇您感興趣的展覽 (預設顯示全部)' else ' - ' + selected_name}')

            st.dataframe( # 顯示資料
                    printdf[selected_cols], 
                    hide_index = True, 
                    use_container_width = True 
                )
            
            st.image( # 顯示圖片
                imgdict[selected_name] if selected_exhibits != '請選擇您感興趣的展覽 (預設顯示全部)' else image_url,
                caption = f'**:orange[{selected_name}]**',
                width = 600
                )
        else:
            st.image( # 顯示圖片
                imgdict[selected_name] if selected_exhibits != '請選擇您感興趣的展覽 (預設顯示全部)' else image_url,
                caption = f'**:orange[{selected}]**',
                width = 800
                )
else:
    st.sidebar.warning('無此場館，請重新輸入有效場館名稱')

st.markdown('---')

