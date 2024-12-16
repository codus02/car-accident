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
    page_title="대한민국 교통사고 추이 대시보드",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

st.title('대한민국 교통사고 추이 정밀 분석')

st.markdown("<br>", unsafe_allow_html=True)  
st.markdown("<br>", unsafe_allow_html=True)  
st.markdown("<br>", unsafe_allow_html=True)  
#######################
# 데이터 불러오기
df = pd.read_csv("C:/Users/chaet/Downloads/음주운전교통사고비율_시도_시_군_구__20241204193205.csv", encoding='UTF-8') # csv 파일 불러오기
korea_geojson = json.load(open("C:/Users/chaet/Downloads/SIDO_MAP_2022_geoJSON.json", encoding="UTF-8")) # json 파일 불러오기



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







#######################
# 행정구역 및 카테고리 선택
st.markdown('#### 선택한 행정구역의 연도별 사고 추이')

st.markdown("<br>", unsafe_allow_html=True)  



# 행정구역 선택 박스
region_list = df['행정구역'].unique()  # 유일한 행정구역 리스트
selected_region = st.selectbox('행정구역 선택', region_list, key='region_selectbox')



st.markdown("<br>", unsafe_allow_html=True)  



# 카테고리 선택 (라디오 버튼)
category_list = list(df['category'].unique())  # 카테고리 리스트
selected_category = st.radio(
    "카테고리 선택", 
    category_list, 
    index=0,  # 기본 선택 (첫 번째 항목)
    key="category_radio"
)

# 선택한 행정구역의 데이터 필터링
df_selected_region = df.query('행정구역 == @selected_region & category == @selected_category')

if not df_selected_region.empty:
    # 꺾은선 그래프 생성
    line_chart = alt.Chart(df_selected_region).mark_line().encode(
        x=alt.X('year:O', axis=alt.Axis(title='연도', titleFontSize=14, labelFontSize=12)),
        y=alt.Y('accident:Q', axis=alt.Axis(title=selected_category, titleFontSize=14, labelFontSize=12)),
        color=alt.value('#29b5e8')  # 선 색깔
    ).properties(
        width=700,
        height=400
    )

    # 꺾은선 그래프 출력
    st.altair_chart(line_chart, use_container_width=True)
else:
    # 데이터가 없는 경우 메시지 출력
    st.info("선택한 행정구역의 데이터가 없습니다.")




    st.markdown("<br>", unsafe_allow_html=True)  
    st.markdown("<br>", unsafe_allow_html=True)  

# 연도 선택 박스
year_list = df['year'].unique()  # 유일한 행정구역 리스트
selected_year = st.selectbox('연도 선택', year_list, key='year_selectbox')


col = st.columns((4, 5), gap='medium')





with col[0]:
    st.markdown('#### 증가/감소')

    df_population_difference_sorted = calculate_population_difference(df, selected_year, selected_category)

    if selected_year > 2014:
        first_state_name = df_population_difference_sorted.행정구역.iloc[0]
        first_state_population = df_population_difference_sorted.accident.iloc[0]
        first_state_delta = round(df_population_difference_sorted.population_difference.iloc[0], 1)
    else:
        first_state_name = '-'
        first_state_population = '-'
        first_state_delta = '-'
    st.metric(label=first_state_name, value=first_state_population, delta=first_state_delta)

    if selected_year > 2014:
        last_state_name = df_population_difference_sorted.행정구역.iloc[-1]
        last_state_population = df_population_difference_sorted.accident.iloc[-1]
        last_state_delta = round(df_population_difference_sorted.population_difference.iloc[-1], 1)
    else:
        last_state_name = '-'
        last_state_population = '-'
        last_state_delta = '-'
    st.metric(label=last_state_name, value=last_state_population, delta=last_state_delta)




    st.write('''
             - 선택 연도에서 선택 카테고리 사고 수가 가장 많이 사고 증가/감소한 시도 
             ''')







with col[1]:
    st.markdown('#### 변동 시도 비율')

    # 항상 '음주사고수'를 기준으로 계산
    df_population_difference_sorted_accidents = calculate_population_difference(
        df.query('category == "음주사고수"'), selected_year, "음주사고수"
    )

    if selected_year > 2014:
        # Filter states with population difference > 100
        df_greater_100 = df_population_difference_sorted_accidents[
            df_population_difference_sorted_accidents.population_difference > 100
        ]
        df_less_100 = df_population_difference_sorted_accidents[
            df_population_difference_sorted_accidents.population_difference < -100
        ]

        # % of States with population difference > 100
        states_migration_greater = round(
            (len(df_greater_100) / df_population_difference_sorted_accidents.행정구역.nunique()) * 100
        )
        states_migration_less = round(
            (len(df_less_100) / df_population_difference_sorted_accidents.행정구역.nunique()) * 100
        )

        donut_chart_greater = make_donut(states_migration_greater, "증가", "green")
        donut_chart_less = make_donut(states_migration_less, "감소", "red")
    else:
        states_migration_greater = 0
        states_migration_less = 0
        donut_chart_greater = make_donut(states_migration_greater, "증가", "green")
        donut_chart_less = make_donut(states_migration_less, "감소", "red")

    migrations_col = st.columns((0.2, 1, 0.2))
    with migrations_col[1]:
        st.write("증가")
        st.altair_chart(donut_chart_greater)
        st.write("감소")
        st.altair_chart(donut_chart_less)



    st.write('''
             - 선택 연도에서 :orange[**음주사고 수**] 가 100 이상 증가/감소한 시도의 비율
             ''')





