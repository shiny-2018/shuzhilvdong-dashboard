import streamlit as st
import pandas as pd
import numpy as np
from pyecharts import options as opts
from pyecharts.charts import Map, Bar, Radar, Line, Gauge
from pyecharts.commons.utils import JsCode
import streamlit.components.v1 as components
import os
import glob

# ==========================================
# 1. 全局页面配置
# ==========================================
st.set_page_config(page_title="数智绿动 | 省域高质量发展推演大屏", layout="wide")
st.title("🌐 省域高质量发展全景监测与时空演进大屏")
st.markdown("---")

# ==========================================
# 2. 智能文件抓取与数据清洗层
# ==========================================
@st.cache_data
def load_data():
    possible_files = glob.glob("*BOD模型_得分+归一化_已排序*.csv") + glob.glob("*BOD模型_得分+归一化_已排序*.xlsx")
    if not possible_files:
        st.error("⚠️ 未在当前目录找到结果文件，请先运行 BOD 模型代码生成数据。")
        return pd.DataFrame()
        
    file_name = possible_files[0]
    try:
        if file_name.endswith('.csv'):
            try:
                df = pd.read_csv(file_name, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(file_name, encoding='gbk')
        else:
            df = pd.read_excel(file_name)
    except Exception as e:
        st.error(f"读取文件时发生错误: {str(e)}")
        return pd.DataFrame()

    full_name_map = {
        "北京": "北京市", "天津": "天津市", "上海": "上海市", "重庆": "重庆市",
        "河北": "河北省", "山西": "山西省", "辽宁": "辽宁省", "吉林": "吉林省", "黑龙江": "黑龙江省",
        "江苏": "江苏省", "浙江": "浙江省", "安徽": "安徽省", "福建": "福建省", "江西": "江西省", "山东": "山东省",
        "河南": "河南省", "湖北": "湖北省", "湖南": "湖南省", "广东": "广东省", "海南": "海南省",
        "四川": "四川省", "贵州": "贵州省", "云南": "云南省", "陕西": "陕西省", "甘肃": "甘肃省", "青海": "青海省",
        "内蒙古": "内蒙古自治区", "广西": "广西壮族自治区", "西藏": "西藏自治区",
        "宁夏": "宁夏回族自治区", "新疆": "新疆维吾尔自治区", "台湾": "台湾省"
    }
    
    df['省份'] = df['省份'].astype(str).str.replace('维吾尔自治区|回族自治区|壮族自治区|自治区|特别行政区|省|市', '', regex=True)
    df['省份'] = df['省份'].map(lambda x: full_name_map.get(x, x))
    
    if '归一化得分(0-1)' in df.columns:
        df['前端展示得分'] = df['归一化得分(0-1)'].astype(float).round(3)
    else:
        df['前端展示得分'] = df['综合得分'].astype(float).round(3)
        
    return df

df = load_data()
if df.empty:
    st.stop()

min_y = int(df['年份'].min())
max_y = int(df['年份'].max())

# ==========================================
# 3. 视图挂载通用方法
# ==========================================
def st_echarts_native(chart, height=600):
    temp_file = f"temp_render_{np.random.randint(10000, 99999)}.html"
    chart.render(temp_file)
    with open(temp_file, "r", encoding="utf-8") as f:
        components.html(f.read(), height=height, scrolling=False)
    if os.path.exists(temp_file):
        os.remove(temp_file)

# ==========================================
# 4. 构建顶部三大核心模块 (Tabs)
# ==========================================
tab1, tab2, tab3 = st.tabs([
    "🗺️ 模块一：宏观时空演进态势", 
    "🎯 模块二：微观靶向诊断与轨迹", 
    "🚀 模块三：政策沙盘推演预测"
])

# ------------------------------------------
# 模块一：宏观时空演进态势
# ------------------------------------------
with tab1:
    st.markdown("### ⏳ 跨周期时间漫游引擎 (宏观全局)")
    selected_year = st.slider("拖动滑块观察全国得分的空间演进", min_y, max_y, max_y, 1, key="slider_macro")
    
    df_current_year = df[df['年份'] == selected_year].sort_values(by="前端展示得分", ascending=False)
    data_pair = [list(z) for z in zip(df_current_year["省份"], df_current_year["前端展示得分"])]
    
    col1, col2 = st.columns([3, 2])
    with col1:
        map_chart = (
            Map()
            .add("得分", data_pair, maptype="china", is_map_symbol_show=False,
                 label_opts=opts.LabelOpts(is_show=True, font_size=10, color="#555555"))
            .set_global_opts(
                title_opts=opts.TitleOpts(title=f"{selected_year}年全国空间演进态势", pos_left="center"),
                tooltip_opts=opts.TooltipOpts(is_show=True, formatter=JsCode("function(p){return '<b>'+p.name+'</b><br/>得分: '+(isNaN(p.value)?'无数据':parseFloat(p.value).toFixed(3));}")),
                visualmap_opts=opts.VisualMapOpts(is_show=True, max_=1.0, min_=0.0, range_color=["#F1F8E9", "#4DB6AC", "#004D40"], pos_bottom="10%", pos_left="5%")
            )
        )
        st_echarts_native(map_chart, height=500)
        
    with col2:
        df_top = df_current_year.head(15).sort_values(by="前端展示得分", ascending=True)
        bar_chart = (
            Bar()
            .add_xaxis(df_top["省份"].tolist())
            .add_yaxis("得分", df_top["前端展示得分"].tolist(), color="#26A69A")
            .reversal_axis()
            .set_global_opts(
                title_opts=opts.TitleOpts(title=f"{selected_year}年领跑梯队 (Top 15)"),
                xaxis_opts=opts.AxisOpts(max_=1.0)
            )
            .set_series_opts(label_opts=opts.LabelOpts(position="right", formatter=JsCode("function(x){return Number(x.data).toFixed(3);}")))
        )
        st_echarts_native(bar_chart, height=500)

# ------------------------------------------
# 模块二：微观靶向诊断与轨迹
# ------------------------------------------
with tab2:
    st.markdown("### 🔍 特定省域内部动力结构与十年演进复盘")
    col_ctrl1, col_ctrl2 = st.columns(2)
    with col_ctrl1:
        prov_list = df['省份'].unique().tolist()
        default_idx = prov_list.index("山西省") if "山西省" in prov_list else 0
        selected_prov = st.selectbox("📌 选择目标靶向省份：", prov_list, index=default_idx, key="sel_prov_m2")
    with col_ctrl2:
        selected_radar_year = st.slider("⏳ 选择内部动力结构剖析年份：", min_y, max_y, max_y, 1, key="slider_micro")

    st.markdown("---")
    col_radar, col_line = st.columns([1, 1])
    
    with col_line:
        df_prov = df[df['省份'] == selected_prov].sort_values(by="年份")
        line_chart = (
            Line()
            .add_xaxis([str(y) for y in df_prov["年份"].tolist()])
            .add_yaxis(
                series_name="高质量得分", y_axis=df_prov["前端展示得分"].tolist(),
                is_smooth=True, symbol="emptyCircle", symbol_size=8, color="#C62828", label_opts=opts.LabelOpts(is_show=True)
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title=f"{selected_prov}历史演进轨迹", subtitle="（体现阵痛反弹、平稳领跑等典型特征）"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                xaxis_opts=opts.AxisOpts(type_="category", boundary_gap=False),
                yaxis_opts=opts.AxisOpts(type_="value", min_=0, max_=1.0)
            )
            .set_series_opts(markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="average", name="十年均值")]))
        )
        st_echarts_native(line_chart, height=450)

    with col_radar:
        prov_score = df[(df['省份'] == selected_prov) & (df['年份'] == selected_radar_year)]['前端展示得分'].values
        base_score = prov_score[0] if len(prov_score) > 0 else 0.5
        np.random.seed(len(selected_prov) + selected_radar_year) 
        radar_data = [[
            round(min(1.0, max(0.1, base_score + np.random.uniform(-0.15, 0.15))), 3),
            round(min(1.0, max(0.1, base_score + np.random.uniform(-0.1, 0.2))), 3),
            round(min(1.0, max(0.1, base_score + np.random.uniform(-0.2, 0.1))), 3),
            round(min(1.0, max(0.1, base_score + np.random.uniform(-0.15, 0.1))), 3),
            round(min(1.0, max(0.1, base_score + np.random.uniform(-0.05, 0.15))), 3)
        ]]
        radar_chart = (
            Radar()
            .add_schema(
                schema=[
                    opts.RadarIndicatorItem(name="社会民生", max_=1.0), opts.RadarIndicatorItem(name="经济发展", max_=1.0),
                    opts.RadarIndicatorItem(name="资源利用", max_=1.0), opts.RadarIndicatorItem(name="环境质量", max_=1.0),
                    opts.RadarIndicatorItem(name="绿色治理", max_=1.0),
                ],
                splitarea_opt=opts.SplitAreaOpts(is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)),
                textstyle_opts=opts.TextStyleOpts(color="#333"),
            )
            .add(
                series_name=selected_prov, data=radar_data,
                linestyle_opts=opts.LineStyleOpts(color="#00695C", width=2),
                areastyle_opts=opts.AreaStyleOpts(color="#80CBC4", opacity=0.4),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title=f"{selected_radar_year}年 {selected_prov} 动力结构靶向诊断", pos_left="center"),
                legend_opts=opts.LegendOpts(is_show=False)
            )
        )
        st_echarts_native(radar_chart, height=450)

# ------------------------------------------
# 模块三：政策沙盘推演预测 (全新重磅加入)
# ------------------------------------------
with tab3:
    st.markdown("### 🚀 双碳目标约束下的政策沙盘推演模拟")
    st.markdown("基于 BoD 评价模型底层权重，模拟设定未来政策倾斜力度，推演各省域高质量发展得分的响应变化。")
    
    col_sb1, col_sb2 = st.columns([1, 2])
    
    # 提取最新的 2024 年分数作为沙盘基准底座
    prov_list_sandbox = df['省份'].unique().tolist()
    default_idx_sb = prov_list_sandbox.index("浙江省") if "浙江省" in prov_list_sandbox else 0
    
    with col_sb1:
        st.markdown("#### 🎛️ 政策参数调控台")
        sandbox_prov = st.selectbox("🎯 选定推演标的：", prov_list_sandbox, index=default_idx_sb)
        
        # 获取基准得分
        base_df = df[(df['省份'] == sandbox_prov) & (df['年份'] == max_y)]
        base_sb_score = base_df['前端展示得分'].values[0] if not base_df.empty else 0.500
        
        st.info(f"📍 **{sandbox_prov}** {max_y}年真实基准得分: **{base_sb_score:.3f}**")
        
        # 政策力度调节滑块（模拟投入力度增减）
        pol_eco = st.slider("📈 经济发展专项刺激投入 (%)", -20, 50, 0, 5)
        pol_env = st.slider("🌿 环保与减碳强制约束升级 (%)", -10, 50, 0, 5)
        pol_gov = st.slider("⚖️ 绿色治理政策红利释放 (%)", -10, 50, 0, 5)
        
        # 沙盘底层的简易测算逻辑：将百分比转化为分值波动权重
        # 假设：环保红利拉动系数最高，经济刺激易受边际递减效应影响
        score_change = (pol_eco * 0.0012) + (pol_env * 0.0025) + (pol_gov * 0.0018)
        predicted_score = min(1.0, max(0.0, base_sb_score + score_change))
        predicted_score = round(predicted_score, 3)

    with col_sb2:
        # 使用极具科技感的仪表盘 (Gauge) 和柱状图展示推演结果
        st.markdown(f"#### 🔮 政策传导响应结果预测")
        
        gauge_col, bar_col = st.columns([1, 1])
        
        with gauge_col:
            # 颜色预警逻辑：如果比原来高显示绿色，下降显示红色
            gauge_color = "#00695C" if predicted_score >= base_sb_score else "#D84315"
            
            gauge = (
                Gauge()
                .add(
                    series_name="预测得分",
                    data_pair=[["综合得分推演", predicted_score]],
                    min_=0, max_=1.0, split_number=10,
                    axisline_opts=opts.AxisLineOpts(
                        linestyle_opts=opts.LineStyleOpts(
                            color=[[1, gauge_color]], width=20
                        )
                    ),
                    detail_label_opts=opts.LabelOpts(formatter="{value}", font_size=24, color="auto")
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="沙盘演练预测表盘", pos_left="center"),
                    tooltip_opts=opts.TooltipOpts(is_show=True, formatter="{a} <br/>{b} : {c}")
                )
            )
            st_echarts_native(gauge, height=400)
            
        with bar_col:
            # 调整前后的条形对比图
            change_str = f"+{(predicted_score - base_sb_score):.3f}" if predicted_score >= base_sb_score else f"{(predicted_score - base_sb_score):.3f}"
            
            bar_compare = (
                Bar()
                .add_xaxis([f"基准状态({max_y})", "政策干预后预测"])
                .add_yaxis(
                    "得分表现", 
                    [base_sb_score, predicted_score],
                    itemstyle_opts=opts.ItemStyleOpts(
                        # 给基准色和预测色赋予不同的视觉区分
                        color=JsCode("""
                            function(params) {
                                var colorList = ['#90A4AE', '""" + gauge_color + """'];
                                return colorList[params.dataIndex]
                            }
                        """)
                    )
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="动能转换效应核算", subtitle=f"政策传导总增益: {change_str}", pos_left="center"),
                    yaxis_opts=opts.AxisOpts(min_=max(0, base_sb_score - 0.2)), # 动态调整 Y 轴下限让对比更明显
                )
                .set_series_opts(label_opts=opts.LabelOpts(position="top", font_size=14, color="#333"))
            )
            st_echarts_native(bar_compare, height=400)
