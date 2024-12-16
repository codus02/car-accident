#######################
# 라이브러리 불러오기
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import json

#######################
# 페이지 설정
st.set_page_config(
    page_title="대한민국 교통사고 추이 분석",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")


st.title('대한민국 교통사고 추이 분석 대시보드')

st.markdown("<br>", unsafe_allow_html=True)  
st.markdown("<br>", unsafe_allow_html=True)  
st.markdown("<br>", unsafe_allow_html=True)  

#######################
# 데이터 불러오기


file_path="음주운전교통사고비율_시도_시_군_구__20241204193205.csv"
df = pd.read_csv(file_path,  encoding='UTF-8')

korea_geojson = json.load(open('SIDO_MAP_2022_geoJSON.json', encoding="UTF-8")) # json 파일 불러오기

#######################
#######################
# 데이터 전처리
def preprocess_data(data):
    data.rename(columns={'행정구역별(1)': '행정구역'}, inplace=True)
    data = data[data['행정구역'] != '전국']
    data = data.iloc[1:].reset_index(drop=True)
    data['행정구역'] = data['행정구역'].replace({
        '강원특별자치도': '강원도', 
        '전북특별자치도': '전라북도'
    })
    return data

df = preprocess_data(df)

# GeoJSON CTPRVN_CD 값과 데이터프레임 행정구역 매핑
region_mapping = {
    '서울특별시': '11',
    '부산광역시': '26',
    '대구광역시': '27',
    '인천광역시': '28',
    '광주광역시': '29',
    '대전광역시': '30',
    '울산광역시': '31',
    '세종특별자치시': '36',
    '경기도': '41',
    '강원도': '42',
    '충청북도': '43',
    '충청남도': '44',
    '전라북도': '45',
    '전라남도': '46',
    '경상북도': '47',
    '경상남도': '48',
    '제주특별자치도': '50'
}

# 행정구역 열을 CTPRVN_CD와 매핑
df['code'] = df['행정구역'].map(region_mapping)


# 열 이름 변환
def rename_columns(columns):
    new_columns = []
    for col in columns:
        if col.endswith('.1'):
            new_columns.append(f"{col.split('.')[0]}_음주사고수")
        elif col.endswith('.2'):
            new_columns.append(f"{col.split('.')[0]}_교통사고수")
        elif col.isdigit():
            new_columns.append(f"{col}_음주사고비율")
        else:
            new_columns.append(col)
    return new_columns

df.columns = rename_columns(df.columns)

# 데이터 변환
df = df.melt(
    id_vars=['행정구역','code'],
    var_name='prop',
    value_name='accident'
)

if 'prop' in df.columns:
    df[['year', 'category']] = df['prop'].str.split('_', expand=True)

df.drop('prop', axis=1, inplace=True)
df['year'] = df['year'].astype(int)
df['accident'] = pd.to_numeric(df['accident'], errors='coerce')
df = df.dropna(subset=['accident'])



#######################
# 사이드바 설정

with st.sidebar:
    st.title('🚗 대한민국 교통사고 수 대시보드')
    
    year_list = list(df.year.unique())[::-1]  # 연도 리스트를 내림차순으로 정렬
    category_list = list(df.category.unique())  # 카테고리 리스트
    
    selected_year = st.selectbox('연도 선택', year_list) # selectbox에서 연도 선택
    selected_category = st.selectbox('카테고리 선택', category_list) # selectbox에서 카테고리 선택

    df_selected_year = df.query('year == @selected_year & category == @selected_category') # 선택한 연도와 카테고리에 해당하는 데이터만 가져오기
    df_selected_year_sorted = df_selected_year.sort_values(by="accident", ascending=False) # 선택한 연도와 카테고리에 해당하는 데이터를 인구수를 기준으로 내림차순 정렬

    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    selected_color_theme = st.selectbox('컬러 테마 선택', color_theme_list)


#######################
# 그래프 함수

# Heatmap 그래프
# Heatmap 그래프
def make_heatmap(input_df, input_y, input_x, input_color, input_color_theme, selected_category):
    # 필터링: 선택된 카테고리에 해당하는 데이터만 사용
    filtered_df = input_df[input_df['category'] == selected_category]
    
    heatmap = alt.Chart(filtered_df).mark_rect().encode(
        y=alt.Y(f'{input_y}:O', axis=alt.Axis(title="연도", titleFontSize=18, titlePadding=15, titleFontWeight=900, labelAngle=0)),
        x=alt.X(f'{input_x}:O', axis=alt.Axis(title=selected_category, titleFontSize=18, titlePadding=15, titleFontWeight=900)),
        color=alt.Color(f'max({input_color}):Q',
                        legend=None,
                        scale=alt.Scale(scheme=input_color_theme)),
        stroke=alt.value('black'),
        strokeWidth=alt.value(0.25),
    ).properties(
        width=900
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=12
    ) 
    return heatmap


# Choropleth map
def make_choropleth(input_df, input_gj, input_column, input_color_theme):
    # 데이터프레임의 열과 GeoJSON 속성 간 데이터 매칭
    input_df['행정구역'] = input_df['행정구역'].astype(str)  # GeoJSON 속성과 동일한 데이터 타입으로 변환
    
    # Choropleth MapBox 생성
    choropleth = px.choropleth_mapbox(
        input_df,
        geojson=input_gj,
        locations='code',  # 데이터프레임의 열
        featureidkey='properties.CTPRVN_CD',  # GeoJSON의 속성 키
        mapbox_style='carto-darkmatter',
        zoom=6,  # 줌 조정
        center={"lat": 37.5665, "lon": 126.9780},  # 대한민국 중심 좌표
        color=input_column,  # 색상 값
        color_continuous_scale=input_color_theme,
        labels={ '행정구역': '시도명'},  # 라벨 설정
        hover_data=['행정구역', 'accident']  # 툴팁 데이터
    )
    
    # 레이아웃 업데이트
    choropleth.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=600
    )
    return choropleth



# 도넛 차트
def make_donut(input_response, input_text, input_color):
  if input_color == 'blue':
      chart_color = ['#29b5e8', '#155F7A']
  if input_color == 'green':
      chart_color = ['#27AE60', '#12783D']
  if input_color == 'orange':
      chart_color = ['#F39C12', '#875A12']
  if input_color == 'red':
      chart_color = ['#E74C3C', '#781F16']
    
  source = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100-input_response, input_response]
  })
  source_bg = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100, 0]
  })
    
  plot = alt.Chart(source).mark_arc(innerRadius=45, cornerRadius=25).encode(
      theta="% value",
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          #domain=['A', 'B'],
                          domain=[input_text, ''],
                          # range=['#29b5e8', '#155F7A']),  # 31333F
                          range=chart_color),
                      legend=None),
  ).properties(width=130, height=130)
    
  text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=32, fontWeight=700, fontStyle="italic").encode(text=alt.value(f'{input_response} %'))
  plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=45, cornerRadius=20).encode(
      theta="% value",
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          # domain=['A', 'B'],
                          domain=[input_text, ''],
                          range=chart_color),  # 31333F
                      legend=None),
  ).properties(width=130, height=130)
  return plot_bg + plot + text # 백그라운드, 차트, 텍스트를 합쳐서 그래프 생성

# Convert population to text 

def format_number(num):
    return f"{num:,}"  # 숫자에 천 단위 구분 쉼표 추가


# Calculation year-over-year population migrations
def calculate_population_difference(input_df, input_year, input_category):
  selected_year_data = input_df.query('year == @input_year & category == @input_category').reset_index()
  previous_year_data = input_df.query('year == @input_year-1 & category == @input_category').reset_index()
  selected_year_data['population_difference'] = selected_year_data['accident'].sub(previous_year_data['accident'], fill_value=0)
  selected_year_data['population_difference_abs'] = abs(selected_year_data['population_difference'])
  return pd.concat([
    selected_year_data['행정구역'], 
    selected_year_data['code'], 
    selected_year_data['accident'], 
    selected_year_data['population_difference'], 
    selected_year_data['population_difference_abs']
    ], axis=1).sort_values(by='population_difference', ascending=False)

#######################
# 대시보드 레이아웃
col = st.columns((7, 3), gap='medium')

with col[0]:  # 왼쪽


    st.markdown('#### ' + str(selected_year) + '년 ' + str(selected_category))
    
    # Choropleth map 표시
    choropleth = make_choropleth(df_selected_year, korea_geojson, 'accident', selected_color_theme)
    st.plotly_chart(choropleth, use_container_width=True)

    
    # 간격 추가
    st.markdown("<br>", unsafe_allow_html=True)  
    st.markdown("<br>", unsafe_allow_html=True)  
    st.markdown("<br>", unsafe_allow_html=True)  
    st.markdown("<br>", unsafe_allow_html=True)         

    


    # Heatmap 표시
    heatmap = make_heatmap(df, 'year', '행정구역', 'accident', selected_color_theme,selected_category)
    st.altair_chart(heatmap, use_container_width=True)
    
    


with col[1]:

    
    with st.expander('정보', expanded=True):
        st.write('''
            - 데이터: [사이트로 이동](https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1YL14001&conn_path=D9&vw_cd=MT_GTITLE01)
                 
            - 연도, 사고 카테고리를 선택하면 해당 연도의 해당 카테고리에 대해 지도와 heatmap으로 관찰할수 있습니다
            ''')
        
    st.markdown('#### 시도별 ' + str(selected_category))

    st.dataframe(df_selected_year_sorted,
                 column_order=("행정구역", "accident"),
                 hide_index=True,
                 width=500,
                 column_config={
                    "행정구역": st.column_config.TextColumn(
                        "시도명",
                    ),
                    "accident": st.column_config.ProgressColumn(
                        str(selected_category),
                        format="%f",
                        min_value=0,
                        max_value=max(df_selected_year_sorted.accident),
                     )}
                 )
 
