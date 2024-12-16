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
    page_title="대한민국 자동차 수 추이 대시보드",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

st.title('대한민국 자동차 수 추이 분석 대시보드')

st.markdown("<br>", unsafe_allow_html=True)  
st.markdown("<br>", unsafe_allow_html=True)  
st.markdown("<br>", unsafe_allow_html=True)  

#######################
# 데이터 불러오기
file_path="1인당_자동차_등록대수_시도_시_군_구__20241216183029.csv"
df = pd.read_csv(file_path,  encoding='UTF-8')

# csv 파일 불러오기
korea_geojson = json.load(open('SIDO_MAP_2022_geoJSON.json', encoding="UTF-8")) # json 파일 불러오기


#######################
#######################
# 데이터 전처리
def preprocess_data(data):
    data.rename(columns={'행정구역별': '행정구역'}, inplace=True)
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
            new_columns.append(f"{col.split('.')[0]}_자동차등록수")
        elif col.endswith('.2'):
            new_columns.append(f"{col.split('.')[0]}_인구수")
        elif col.isdigit():
            new_columns.append(f"{col}_1인당 자동차수")
        else:
            new_columns.append(col)
    return new_columns

df.columns = rename_columns(df.columns)

# 데이터 변환
df = df.melt(
    id_vars=['행정구역','code'],
    var_name='prop',
    value_name='car'
)

if 'prop' in df.columns:
    df[['year', 'category']] = df['prop'].str.split('_', expand=True)

df.drop('prop', axis=1, inplace=True)
df['year'] = df['year'].astype(int)
df['car'] = pd.to_numeric(df['car'], errors='coerce')
df = df.dropna(subset=['car'])


col = st.columns((7, 3), gap='medium')


with col[0]:

    st.markdown('## 카테고리 선택')
    st.markdown("<br>", unsafe_allow_html=True)

    # 카테고리 선택 (라디오 버튼)
    category_list = list(df['category'].unique())  # 카테고리 리스트
    selected_category = st.radio(
      "카테고리 선택", 
      category_list, 
     index=0,  # 기본 선택 (첫 번째 항목)
     key="category_radio"
    )




with col[1]:
    st.markdown("<br>", unsafe_allow_html=True) 
    st.markdown("<br>", unsafe_allow_html=True) 
    st.markdown("<br>", unsafe_allow_html=True) 
    with st.expander('정보', expanded=True):
        st.write('''
            - 데이터: [사이트로 이동](https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1YL14001&conn_path=D9&vw_cd=MT_GTITLE01)
                 
            - 카테고리, 지역, 연도를 선택하면 해당 선택 대해 막대그래프와 파이차트를 관찰할수 있습니다
            ''')
        





st.markdown("<br>", unsafe_allow_html=True) 
st.markdown("<br>", unsafe_allow_html=True) 
st.markdown("<br>", unsafe_allow_html=True) 



#######################
# 행정구역 및 카테고리 선택
st.markdown('#### 선택한 행정구역의 연도별 추이')

st.markdown("<br>", unsafe_allow_html=True)  


# 행정구역 선택 박스
region_list = df['행정구역'].unique()  # 유일한 행정구역 리스트
selected_region = st.selectbox('행정구역 선택', region_list, key='region_selectbox')

st.markdown("<br>", unsafe_allow_html=True)  


# 선택한 행정구역의 데이터 필터링
df_selected_region = df.query('행정구역 == @selected_region & category == @selected_category')

if not df_selected_region.empty:
    # 막대 그래프 생성
    bar_chart = alt.Chart(df_selected_region).mark_bar().encode(
        x=alt.X('year:O', axis=alt.Axis(title='연도', titleFontSize=14, labelFontSize=12)),
        y=alt.Y('car:Q', axis=alt.Axis(title=selected_category, titleFontSize=14, labelFontSize=12)),
        color=alt.value('#29b5e8')  # 막대 색깔
    ).properties(
        width=700,
        height=400
    )

    # 막대그래프 출력
    st.altair_chart(bar_chart, use_container_width=True)
else:
    # 데이터가 없는 경우 메시지 출력
    st.info("선택한 행정구역의 데이터가 없습니다.")

#######################
# 연도 선택 및 파이차트 출력
#######################
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('#### 선택한 카테고리에 대한 상위 10개 지역 비율')
st.markdown("<br>", unsafe_allow_html=True)

# 연도 선택 박스
year_list = sorted(df['year'].unique(), reverse=True)  # 연도 리스트
selected_year = st.selectbox('연도 선택', year_list, key='year_selectbox')

# 선택한 연도와 카테고리에 해당하는 데이터 필터링
df_selected_year = df.query('year == @selected_year & category == @selected_category')

if not df_selected_year.empty:
    # 상위 5개 지역과 나머지를 "기타"로 묶기
    df_selected_year_sorted = df_selected_year.sort_values(by='car', ascending=False)
    top10 = df_selected_year_sorted.iloc[:10]
    others = pd.DataFrame({
        '행정구역': ['기타'],
        'car': [df_selected_year_sorted.iloc[10:]['car'].sum()],
        'category': [selected_category]
    })
    pie_data = pd.concat([top10, others], ignore_index=True)

    # 파이차트 생성
    pie_chart = px.pie(
        pie_data,
        names='행정구역',
        values='car',
        title=f'{selected_year}년 {selected_category} 상위 10개 지역 비율',
        color_discrete_sequence=px.colors.sequential.Blues
    )

    pie_chart.update_traces(textinfo='percent+label', hoverinfo='label+percent+value')

    # 파이차트 출력
    st.plotly_chart(pie_chart, use_container_width=True)
else:
    # 데이터가 없는 경우 메시지 출력
    st.info("선택한 연도와 카테고리에 대한 데이터가 없습니다.")
