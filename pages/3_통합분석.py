#######################
# 라이브러리 불러오기
import streamlit as st
import pandas as pd
import plotly.express as px
import json

#######################
# 페이지 설정
st.set_page_config(
    page_title="대한민국 교통사고 및 자동차 통계 분석",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title('대한민국 교통사고 및 자동차 통계 분석 대시보드')
st.markdown("<br>", unsafe_allow_html=True)

#######################
# 데이터 불러오기


file_path="음주운전교통사고비율_시도_시_군_구__20241204193205.csv"
df = pd.read_csv(file_path,  encoding='UTF-8')

file_path2="1인당_자동차_등록대수_시도_시_군_구__20241216183029.csv"
df2 = pd.read_csv(file_path2,  encoding='UTF-8')


korea_geojson = json.load(open('SIDO_MAP_2022_geoJSON.json', encoding="UTF-8")) # json 파일 불러오기


############
# 데이터 전처리1
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



# 데이터 전처리2
def preprocess_data2(data):
    data.rename(columns={'행정구역별': '행정구역'}, inplace=True)
    data = data[data['행정구역'] != '전국']
    data = data.iloc[1:].reset_index(drop=True)
    data['행정구역'] = data['행정구역'].replace({
        '강원특별자치도': '강원도', 
        '전북특별자치도': '전라북도'
    })
    return data

df2 = preprocess_data2(df2)





# GeoJSON 매핑
region_mapping = {
    '서울특별시': '11', '부산광역시': '26', '대구광역시': '27',
    '인천광역시': '28', '광주광역시': '29', '대전광역시': '30',
    '울산광역시': '31', '세종특별자치시': '36', '경기도': '41',
    '강원도': '42', '충청북도': '43', '충청남도': '44',
    '전라북도': '45', '전라남도': '46', '경상북도': '47',
    '경상남도': '48', '제주특별자치도': '50'
}

df['code'] = df['행정구역'].map(region_mapping)
df2['code'] = df2['행정구역'].map(region_mapping)







# 열 이름 변환1
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


# 열 이름 변환2
def rename_columns2(columns):
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

df2.columns = rename_columns2(df2.columns)



# 데이터 변환1
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


# 데이터 변환2
df2 = df2.melt(
    id_vars=['행정구역','code'],
    var_name='prop',
    value_name='car'
)

if 'prop' in df2.columns:
    df2[['year', 'category']] = df2['prop'].str.split('_', expand=True)

df2.drop('prop', axis=1, inplace=True)
df2['year'] = df2['year'].astype(int)
df2['car'] = pd.to_numeric(df2['car'], errors='coerce')
df2 = df2.dropna(subset=['car'])




#######################
# 사이드바 설정
year_list = sorted(df['year'].unique(), reverse=True)
selected_year = st.sidebar.selectbox("연도를 선택하세요", year_list)


category_b = st.sidebar.selectbox("교통사고 관련 데이터 선택 ", df['category'].unique(), key='category_b')
category_a = st.sidebar.selectbox("자동차 관련 데이터 선택 ", df2['category'].unique(), key='category_a')

#######################
# 데이터 병합 및 비율 계산
df_a = df2[(df2['year'] == selected_year) & (df2['category'] == category_a)]
df_b = df[(df['year'] == selected_year) & (df['category'] == category_b)]

if df_a.empty or df_b.empty:
    st.warning("선택한 연도 또는 카테고리에 해당하는 데이터가 없습니다.")
else:
    # 데이터 병합
    merged = pd.merge(df_a, df_b, on=['code', '행정구역'], suffixes=('_a', '_b'))
    merged = merged[merged['car'] > 0]  # 분모가 0이 아닌 값만
    merged['ratio'] = merged['accident'] / merged['car']

    #######################
    # Choropleth Map 생성 함수
    def make_choropleth(data, geojson, column, title, scale):
        fig = px.choropleth_mapbox(
            data,
            geojson=geojson,
            locations='code',
            featureidkey='properties.CTPRVN_CD',
            color=column,
            color_continuous_scale=scale,
            labels={column: title},
            hover_name='행정구역',
            center={'lat': 36.5, 'lon': 127.5},
            zoom=5,
            mapbox_style="carto-positron"
        )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        return fig



col = st.columns((5.5 ,4.5), gap='medium')

with col[0]: 




    #######################
    # Choropleth Map 출력
    st.markdown(f"### {selected_year}년<br>{category_b} / {category_a} 비율 <br>Choropleth Map", unsafe_allow_html=True)
    choropleth = make_choropleth(merged, korea_geojson, 'ratio', f"{category_b} /<br> {category_a}", 'Oranges')
    st.plotly_chart(choropleth, use_container_width=True)








with col[1]:
        # 필요한 열만 선택
    filtered_data = merged[['행정구역', 'car', 'accident', 'ratio']]

    # 열 이름 변경 (보기 좋게)
    filtered_data.rename(columns={
      '행정구역': '지역',
      'car': f'{category_a} (분모)',
     'accident': f'{category_b} (분자)',
     'ratio': '비율'
    }, inplace=True)


    st.markdown("<br>", unsafe_allow_html=True)  
    st.markdown("<br>", unsafe_allow_html=True)  
# 병합된 데이터 확인
    st.markdown("### 데이터 값")
    st.dataframe(filtered_data)


st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)  

st.write('''
         
         선택한 연도의 (교통사고 관련 데이터) / (자동차 관련 데이터)
         값을 표현한 choropleht map 을 보여줍니다

         
         ''')
