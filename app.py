import requests
import csv
import os
import re
import streamlit as st
from datetime import datetime
from lxml import html

datalist = []

if "current_time" not in st.session_state:
    st.session_state.current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

if "datalist" not in st.session_state:
    st.session_state["datalist"] = []

TMDB_BASE_URL = 'https://www.themoviedb.org'
TMDB_PAGE_1 = 'https://www.themoviedb.org/movie/top-rated'
TMDB_PAGE_2 ='https://www.themoviedb.org/discover/movie/items'

#定义加载数据函数
def load_infos():
    l_info = []
    #判断是否存在这个文件
    if os.path.exists('csv_data'):
        file_name_list = os.listdir('csv_data')
        for filename in file_name_list:
            if filename.endswith('.csv'):
                l_info.append(filename[:-4])#截取.csv前的文件名
        l_info.sort(reverse=True)#进行降序排序
    return l_info

#加载指定数据函数
def load_info(info):
    if os.path.exists(f'csv_data/{info}.csv'):
        with open(f'csv_data/{info}.csv','r',encoding='utf-8') as f:
            r = csv.DictReader(f)
            st.session_state.current_time = info
            return list(r)
    return []
#删除数据函数
def delete_info(info):
    if os.path.exists(f'csv_data/{info}.csv'):
        os.remove(f'csv_data/{info}.csv')
        st.session_state.datalist = []
        if info == st.session_state.current_time:
            st.session_state.current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')


#清洗年份数据函数
def get_movie_publish_year(movie_years):
    movie_year = movie_years[0].strip() if movie_years else ''
    return re.search(r'\d{4}',movie_year).group() if re.search(r'\d{4}',movie_year) else ''

#清洗上映时间数据函数
def get_movie_publish_date(movie_dates):
    movie_date = movie_dates[0].strip() if movie_dates else ''
    return re.search(r'\d{4}-\d{2}-\d{2}',movie_date).group() if re.search(r'\d{4}-\d{2}-\d{2}',movie_date) else ''


#清洗时长函数
def get_movie_publish_time(movie_times):
    movie_time = movie_times[0].strip() if movie_times else ''
    h_res = re.search(r'(\d+)h',movie_time)
    m_res = re.search(r'(\d+)m',movie_time)
    h = int(h_res.group(1)) if h_res else 0
    m = int(m_res.group(1)) if m_res else 0
    return h*60+m


#保存数据函数
def save_all_movies(movie_info):
    filename = './csv_data'
    if not os.path.exists(filename):
        os.makedirs(filename)
    with open(f'csv_data/{st.session_state.current_time}.csv','w',encoding='utf-8') as f:
         writer = csv.DictWriter(f, fieldnames=['电影名','年份','上映时间','类型','时长','评分','语言','导演','作者','主演','slogan','简介'])
         writer.writeheader()
         writer.writerows(movie_info)
#获取电影详情函数
def get_movie_info(movie_url):
    print(f'正在获取{movie_url}的数据...')
    response = requests.get(movie_url)
    #解析数据
    html_text = response.text
    doc = html.fromstring(html_text)

    #数据清洗 年份 上映时间 时长

    #电影名
    movie_names = doc.xpath('//*[@id="original_header"]/div[2]/section/div[1]/h2/a/text()')

    #年份
    movie_years = doc.xpath('//*[@id="original_header"]/div[2]/section/div[1]/h2/span/text()')

    #获取电影上映时间
    movie_dates = doc.xpath('//*[@id="original_header"]/div[2]/section/div[1]/div/span[2]/text()')

    #类型
    movie_tags = doc.xpath('//*[@id="original_header"]/div[2]/section/div[1]/div/span[3]/a/text()')

    #时长
    movie_times = doc.xpath('//*[@id="original_header"]/div[2]/section/div[1]/div/span[4]/text()')


    #评分
    movie_scores = doc.xpath('//*[@id="consensus_pill"]/div/div[1]/div/div/@data-percent')
  
    #语言
    movie_languages = doc.xpath('//*[@id="media_v4"]/div/div/div[2]/div/section/div[1]/div/section[1]/p[contains(./strong/bdi,"默认语言")]/text()')
    
    #导演
    movie_directors = doc.xpath('//li[@class="profile"][contains(./p[@class="character"],"Director")]/p[1]/a/text()')

    #作者
    movie_authors = doc.xpath('//li[@class="profile"][contains(./p[@class="character"],"Writer")]/p[1]/a/text()')


    #主演
    movie_star = []
    url_list = doc.xpath('//*[@id="media_v4"]/div/div/div[1]/div/section[contains(./p[@class="new_button"],"完整演职员表")]/p/a/@href')
    for i in url_list:
        star_url = TMDB_BASE_URL+i
        responses = requests.get(star_url)
        html_tx = responses.text
        dc = html.fromstring(html_tx)
        movie_star = dc.xpath('//*[@id="cast"]/ol/li/div/div/p/a/text()')
        
    #slogan
    movie_slogans = doc.xpath('//*[@id="original_header"]/div[2]/section/div[3]/h3[1]/text()')
    # print(movie_slogans)

    #简介
    movie_jj = doc.xpath('//*[@id="original_header"]/div[2]/section/div[3]/div/p/text()')

    #返回信息-字典
    movie_info = {
        '电影名': movie_names[0].strip() if movie_names else '',
        '年份': get_movie_publish_year(movie_years),
        '上映时间': get_movie_publish_date(movie_dates),
        '类型': ','.join(movie_tags) if movie_tags else '',
        '时长': get_movie_publish_time(movie_times),
        '评分': movie_scores[0].strip() if movie_scores else '',
        '语言': movie_languages[0].strip() if movie_languages else '',
        '导演': ','.join(movie_directors) if movie_directors else '',
        '作者': ','.join(movie_authors) if movie_authors else '',
        '主演': ','.join(movie_star) if movie_star else '',
        'slogan': movie_slogans[0].strip() if movie_slogans and movie_slogans[0]!='简介' else '',
        '简介': movie_jj[0].strip() if movie_jj else '',

    }
    return movie_info

    
#主函数，定义核心逻辑
def main():
    #streamlit实现前端页面
    st.title('TMDB电影榜单爬虫')
    st.markdown("[点我跳转到爬取的起始页面](https://www.themoviedb.org/movie/top-rated)")

    col1,col2 = st.columns(2)
    with col1:
        start_page = st.number_input('起始页码',min_value=1,step=1)
    with col2:
        end_page = st.number_input('结束页码',min_value=1,step=1)


    with st.sidebar:
        st.title('爬取记录')
        info_name = load_infos()
        for info in info_name:
                col1,col2 = st.columns([4,1])#利用st.columns()在一行里面设置多列容器[4,1]是指前面一个占四份 后面一个占一份
                with col1:
                    if st.button(info,width='stretch',icon='📄',key=f'load_{info}',type='primary' if info == st.session_state.current_time else 'secondary'):
                        st.session_state['datalist'] = load_info(info)
                        st.rerun()
                with col2:
                    if st.button('',icon='❌️',key=f'delete_{info}'):
                        delete_info(info)
                        st.rerun()

    if st.button('开始爬取数据',width='stretch'): 
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        st.session_state.current_time = current_time
        all_movie = []
        #1.循环获取电影列表
        if start_page>end_page:
            st.error('起始页码不能大于结束页码！')

        else:
            st.text('正在爬取，可能需要一些时间，请您稍等...')
            for page_num in range(start_page,end_page+1):
                if page_num == 1:
                    response = requests.get(TMDB_PAGE_1)
                else:
                    response = requests.post(TMDB_PAGE_2,f'air_date.gte=&air_date.lte=&certification=&certification_country=CN&debug=&first_air_date.gte=&first_air_date.lte=&include_adult=false&include_softcore=false&latest_ceremony.gte=&latest_ceremony.lte=&page={page_num}&primary_release_date.gte=&primary_release_date.lte=&region=&release_date.gte=&release_date.lte=2027-05-12&show_me=everything&sort_by=vote_average.desc&vote_average.gte=0&vote_average.lte=10&vote_count.gte=300&vote_count.lte=&watch_region=CN&with_genres=&with_keywords=&with_networks=&with_origin_country=&with_original_language=&with_watch_monetization_types=&with_watch_providers=&with_release_type=&with_runtime.gte=0&with_runtime.lte=400&view=&discover_preset=top-rated')   
                print('正在获取TMDB榜单数据...')
            #2.解析数据，获取电影列表
                html_text = response.text
                doc = html.fromstring(html_text)
                url_list = doc.xpath(f'//*[@id="page_{page_num}"]//*[@id]/div/div[2]/div/a/@href')
                #3.遍历电影列表，获取电影详情
                for i in url_list:
                    #获取电影详情链接
                    movie_url = TMDB_BASE_URL + i
                    all_movie.append(get_movie_info(movie_url))
                print('获取成功！')
                #4.保存数据，保存为csv文件
            save_all_movies(all_movie)
            st.success('爬取成功！')
            st.session_state.datalist = all_movie
            st.rerun()

    if st.session_state["datalist"]:
        st.text('数据表格')
        st.dataframe(st.session_state["datalist"])

if __name__ == '__main__':
    main()
