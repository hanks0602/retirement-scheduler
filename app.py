import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ==========================================
# CORE SIMULATION LOGIC
# ==========================================
def calculate_tax(gross_salary):
    """Simple tax calculation placeholder."""
    return gross_salary * 0.10  # Assuming flat 10% for simplicity

def run_simulation(start_year, years_to_simulate, start_assets, start_salary, salary_growth, base_expense, inflation, roi, house_year, house_cost, retirement_year, car_year_1, car_year_2, car_cost):
    """
    Runs the financial simulation loop.
    Returns a pandas DataFrame with the yearly trajectory.
    """
    data = []
    
    current_assets = start_assets
    current_salary = start_salary
    current_expense = base_expense
    
    for i in range(years_to_simulate):
        current_year = start_year + i
        
        # Calculate Income
        if current_year >= retirement_year:
            gross_salary = 0
        else:
            gross_salary = current_salary
            
        tax = calculate_tax(gross_salary)
        net_salary = gross_salary - tax
        
        # Apply special milestone expenses (house, cars)
        milestone_cost = 0
        if current_year == house_year: milestone_cost += house_cost
        if current_year == car_year_1: milestone_cost += car_cost
        if current_year == car_year_2: milestone_cost += car_cost
            
        total_expenses_this_year = current_expense + milestone_cost
        
        # Calculate Assets
        beginning_assets = current_assets
        investment_return = beginning_assets * (roi / 100.0)
        
        annual_net_savings = net_salary - total_expenses_this_year
        ending_assets = beginning_assets + investment_return + annual_net_savings
        
        data.append({
            "Year": current_year,
            "Gross Salary": gross_salary,
            "Income Tax": tax,
            "Net Salary": net_salary,
            "Total Expenses": total_expenses_this_year,
            "Beginning Investment Assets": beginning_assets,
            "Investment Return": investment_return,
            "Annual Net Savings": annual_net_savings,
            "Ending Investment Assets": ending_assets
        })
        
        # Update for next year
        current_assets = ending_assets
        current_salary = current_salary * (1 + salary_growth / 100.0)
        current_expense = current_expense * (1 + inflation / 100.0)
        
    return pd.DataFrame(data)

def load_baseline_data(filepath):
    """Loads default data from CSV, handling potential whitespace in columns."""
    if not os.path.exists(filepath):
        st.error(f"Baseline data file '{filepath}' not found.")
        return pd.DataFrame()
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip()  # Clean whitespace
    return df

# ==========================================
# STREAMLIT UI MULTIPAGE SETUP
# ==========================================
st.set_page_config(page_title="Retirement Simulator", layout="wide")

def page_settings():
    st.title("⚙️ 財務參數設定中心")
    st.markdown("請設定您的財務參數。調整滑桿時**不會即時重新計算**，確認無誤後請點擊最下方的按鈕執行模擬。")
    
    data_mode = st.radio("資料來源", options=["使用 CSV 基準資料", "自訂手動模擬"])
    
    if data_mode == "使用 CSV 基準資料":
        st.info("已載入 personal_data.csv 基準設定")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("收入設定")
            start_salary = st.number_input("初始稅前年薪 (元)", value=1000000, step=50000)
            salary_growth = st.slider("預估年薪成長率 (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.5)
            
            st.subheader("支出與通膨設定")
            expense_tier = st.selectbox("日常支出級距", options=["低", "中", "高"], index=1)
            
            tier_mapping = {"低": 400000, "中": 600000, "高": 800000}
            base_expense = tier_mapping[expense_tier]
            
            inflation = st.slider("預估通膨率 (%)", min_value=0.0, max_value=10.0, value=2.5, step=0.1)
            
        with col2:
            st.subheader("投資設定")
            start_assets = st.number_input("初始投資資產 (元)", value=1000000, step=100000)
            roi = st.slider("預期投資報酬率 (%)", min_value=0.0, max_value=20.0, value=6.0, step=0.5)
            
            st.subheader("重大人生里程碑")
            retirement_year = st.number_input("預定退休年份 (薪資歸零)", value=2041, step=1)
            house_year = st.number_input("預定買房年份", value=2030, step=1)
            house_cost = st.number_input("買房頭期款/總花費 (元)", value=5000000, step=100000)
            
            car_year_1 = st.number_input("第一次買車年份", value=2030, step=1)
            car_year_2 = st.number_input("第二次買車年份", value=2040, step=1)
            car_cost = st.number_input("購車預算 (元)", value=750000, step=50000)
            
            years_to_simulate = st.slider("模擬年數", min_value=10, max_value=60, value=54, step=1)
    
    st.markdown("---")
    if st.button("📊 儲存配置並執行模擬", type="primary", use_container_width=True):
        if data_mode == "使用 CSV 基準資料":
            df = load_baseline_data("personal_data.csv")
            ret_year = 2041
        else:
            df = run_simulation(
                start_year=2027,
                years_to_simulate=years_to_simulate,
                start_assets=start_assets,
                start_salary=start_salary,
                salary_growth=salary_growth,
                base_expense=base_expense,
                inflation=inflation,
                roi=roi,
                house_year=house_year,
                house_cost=house_cost,
                retirement_year=retirement_year,
                car_year_1=car_year_1,
                car_year_2=car_year_2,
                car_cost=car_cost
            )
            ret_year = retirement_year
        
        st.session_state.sim_data = df
        st.session_state.data_mode = data_mode
        st.session_state.ret_year = ret_year
        st.switch_page(page_dashboard_obj)

def page_dashboard():
    st.title("📊 退休資產模擬看板")
    
    if "sim_data" not in st.session_state or st.session_state.sim_data.empty:
        st.warning("⚠️ 請先至左側「⚙️ 財務參數設定中心」設定參數並點擊執行模擬。")
        if st.button("前往設定", type="primary"):
            st.switch_page(page_settings_obj)
        st.stop()
        
    df = st.session_state.sim_data
    data_mode = st.session_state.data_mode
    ret_year = st.session_state.ret_year

    # --- KPI Calculations ---
    df['Passive Income Exceeds Expenses'] = df['Investment Return'] > df['Total Expenses']
    crossover_years = df[df['Passive Income Exceeds Expenses']]['Year']

    retirement_age_text = "未能達成"
    if not crossover_years.empty:
        crossover_yr = crossover_years.iloc[0]
        retirement_age_text = str(crossover_yr)

    # 1. 2040 Baseline Asset Check
    assets_2040 = 0
    if 2040 in df['Year'].values:
        assets_2040 = df.loc[df['Year'] == 2040, 'Ending Investment Assets'].values[0]

    # 2. First Year of Retirement Total Expenses
    ret_expenses = 0
    if ret_year in df['Year'].values:
        ret_expenses = df.loc[df['Year'] == ret_year, 'Total Expenses'].values[0]

    # 3. 4% Safe Withdrawal Rate Amount (Based on year prior to retirement)
    safe_withdrawal = 0
    if (ret_year - 1) in df['Year'].values:
        assets_at_ret = df.loc[df['Year'] == (ret_year - 1), 'Ending Investment Assets'].values[0]
        safe_withdrawal = assets_at_ret * 0.04

    # Sustainability Score
    final_assets = df.iloc[-1]['Ending Investment Assets']
    if final_assets < 0:
        sustainability = "危險 (資產耗盡)"
        sustainability_color = "red"
    elif final_assets < df.iloc[0]['Ending Investment Assets']:
        sustainability = "警告 (資產衰退)"
        sustainability_color = "orange"
    else:
        sustainability = "安全 (資產成長)"
        sustainability_color = "green"

    # Render KPIs
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="預估達成財務自由年份", value=retirement_age_text)
    with col2:
        st.metric(label="2040 年底期末資產 (元)", value=f"{assets_2040:,.0f}")
    with col3:
        st.markdown(f"**長期財務永續性評估**")
        st.markdown(f"<h3 style='color: {sustainability_color}; margin-top: -10px;'>{sustainability}</h3>", unsafe_allow_html=True)

    st.markdown("---")

    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric(label=f"4% 安全提領金 (元)", value=f"{safe_withdrawal:,.0f}")
    with col5:
        st.metric(label=f"退休首年 ({ret_year}) 總支出 (元)", value=f"{ret_expenses:,.0f}")
    with col6:
        rule_status = "安全 ✅" if safe_withdrawal >= ret_expenses else "危險 ⚠️"
        rule_color = "green" if safe_withdrawal >= ret_expenses else "red"
        st.markdown(f"**4% 法則健康檢查**")
        st.markdown(f"<h3 style='color: {rule_color}; margin-top: -10px;'>{rule_status}</h3>", unsafe_allow_html=True)

    st.markdown("---")

    # --- CHARTS ---
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("資產累積曲線")
        fig1 = px.line(
            df, 
            x="Year", 
            y="Ending Investment Assets", 
            title="歷年期末投資資產走勢",
            markers=True,
            labels={"Year": "年份", "Ending Investment Assets": "期末投資資產"}
        )
        fig1.update_yaxes(tickformat=",.0f")
        st.plotly_chart(fig1, width='stretch')

    with col_chart2:
        st.subheader("收入與報酬 vs. 總支出")
        fig2 = go.Figure()
        
        # Net Salary
        fig2.add_trace(go.Bar(
            x=df['Year'], 
            y=df['Net Salary'], 
            name='稅後淨薪資', 
            marker_color='blue'
        ))
        
        # Investment Return (Passive Income)
        fig2.add_trace(go.Bar(
            x=df['Year'], 
            y=df['Investment Return'], 
            name='投資報酬 (被動收入)', 
            marker_color='green'
        ))
        
        # Total Expenses (Negative for comparison or line overlay)
        fig2.add_trace(go.Scatter(
            x=df['Year'], 
            y=df['Total Expenses'], 
            name='總支出', 
            mode='lines+markers',
            line=dict(color='red', width=3)
        ))
        
        fig2.update_layout(
            barmode='stack',
            title="資金來源 vs. 總支出對比",
            yaxis=dict(tickformat=",.0f")
        )
        st.plotly_chart(fig2, width='stretch')

    # --- DATA TABLE ---
    st.subheader("歷年詳細模擬數據")
    
    column_mapping = {
        "Year": "年份",
        "Gross Salary": "稅前年薪",
        "Income Tax": "所得稅",
        "Net Salary": "稅後淨薪資",
        "Total Expenses": "總支出",
        "Beginning Investment Assets": "期初投資資產",
        "Investment Return": "投資報酬",
        "Annual Net Savings": "年度淨結餘",
        "Ending Investment Assets": "期末投資資產",
        "Passive Income Exceeds Expenses": "財務自由達標"
    }
    display_df = df.rename(columns=column_mapping)

    # Format dataframe for display
    format_dict = {col: '{:,.0f}' for col in display_df.columns if display_df[col].dtype in ['float64', 'int64'] and col != '年份'}
    if '年份' in display_df.columns:
        format_dict['年份'] = '{:.0f}'

    styled_df = display_df.style.format(format_dict).map(
        lambda x: 'color: red' if isinstance(x, (int, float)) and x < 0 else '', 
        subset=['年度淨結餘', '期末投資資產']
    )

    st.dataframe(styled_df, width='stretch', height=400)

# --- PAGE REGISTRATION & NAVIGATION ---
page_settings_obj = st.Page(page_settings, title="財務參數設定中心", icon="⚙️", default=True)
page_dashboard_obj = st.Page(page_dashboard, title="退休資產模擬看板", icon="📊")

pg = st.navigation([page_settings_obj, page_dashboard_obj])
pg.run()
