import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

def format_value(val, unit):
    if not isinstance(val, (int, float)):
        return val
    if pd.isna(val):
        return "0"
    if unit == "萬元":
        return f"{val / 10000:,.1f}"
    elif unit == "k":
        return f"{val / 1000:,.0f}"
    elif unit == "M":
        return f"{val / 1000000:,.2f}"
    else:
        return f"{val:,.0f}"

# ==========================================
# CORE SIMULATION LOGIC
# ==========================================
def calculate_tax(gross_salary):
    """Calculates Taiwan progressive income tax."""
    deduction = 446000  # 包含基本免稅額、標準扣除額與薪資特別扣除額
    taxable_income = max(0, gross_salary - deduction)
    
    brackets = [
        (560000, 0.05),
        (1260000, 0.12),
        (2520000, 0.20),
        (4720000, 0.30),
        (float('inf'), 0.40)
    ]
    
    tax = 0
    previous_limit = 0
    for limit, rate in brackets:
        if taxable_income > previous_limit:
            tax += (min(taxable_income, limit) - previous_limit) * rate
            previous_limit = limit
            
    return tax

def run_simulation(start_year, years_to_simulate, start_assets, start_salary, salary_growth, base_expense, inflation, roi, retirement_year, enable_pension, current_age, pension_start_age, pension_monthly, milestones_list=None):
    """
    Runs the financial simulation loop.
    Returns a pandas DataFrame with the yearly trajectory.
    """
    if milestones_list is None:
        milestones_list = []
        
    data = []
    
    current_assets = start_assets
    current_salary = start_salary
    current_expense = base_expense
    
    for i in range(years_to_simulate):
        current_year = start_year + i
        sim_age = current_age + i
        
        # Calculate Income
        if current_year >= retirement_year:
            gross_salary = 0
        else:
            gross_salary = current_salary
            
        tax = calculate_tax(gross_salary)
        net_salary = gross_salary - tax
        
        # Calculate Pension
        annual_pension = 0
        if enable_pension and sim_age >= pension_start_age:
            annual_pension = pension_monthly * 12
            
        # Apply special milestone expenses
        milestone_cost = 0
        for m in milestones_list:
            if m["type"] == "one_time" and current_year == m["year"]:
                milestone_cost += m["cost"]
            elif m["type"] == "duration" and m["start_year"] <= current_year <= m["end_year"]:
                milestone_cost += m["annual_cost"]
            elif m["type"] == "interval" and m["start_year"] <= current_year <= m["end_year"]:
                if (current_year - m["start_year"]) % m["interval"] == 0:
                    milestone_cost += m["cost"]
            
        total_expenses_this_year = current_expense + milestone_cost
        
        # Calculate Assets
        beginning_assets = current_assets
        investment_return = beginning_assets * (roi / 100.0)
        
        annual_net_savings = (net_salary + annual_pension) - total_expenses_this_year
        ending_assets = beginning_assets + investment_return + annual_net_savings
        
        data.append({
            "Year": current_year,
            "Gross Salary": gross_salary,
            "Income Tax": tax,
            "Net Salary": net_salary,
            "Pension Income": annual_pension,
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

def load_baseline_data(uploaded_file):
    """Loads data from an uploaded CSV file, handling potential whitespace in columns."""
    if uploaded_file is None:
        return pd.DataFrame()
    df = pd.read_csv(uploaded_file)
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
    
    uploaded_file = None
    if data_mode == "使用 CSV 基準資料":
        uploaded_file = st.file_uploader("請上傳您的 CSV 基準資料", type=["csv"])
        if uploaded_file is not None:
            st.success(f"已成功載入: {uploaded_file.name}")
    else:
        display_unit = st.radio("輸入與顯示數值單位", ["元", "萬元", "k", "M"], horizontal=True, key="global_display_unit")
        scale = 1
        if display_unit == "萬元":
            scale = 10000
        elif display_unit == "k":
            scale = 1000
        elif display_unit == "M":
            scale = 1000000

        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("💰 收入與投資設定")
            tab_income, tab_invest = st.tabs(["💵 薪資與年金", "📈 投資資產配置"])
            
            with tab_income:
                st.markdown("##### 薪資設定")
                use_tsmc_path = st.checkbox("套用台積電 31-33 職等預設薪資路徑")
                start_salary_input = st.number_input(f"初始稅前年薪 ({display_unit})", value=float(1000000 / scale), step=float(50000 / scale) if scale <= 50000 else 1.0, disabled=use_tsmc_path)
                start_salary = start_salary_input * scale
                salary_growth = st.slider("預估年薪成長率 (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.5, disabled=use_tsmc_path)
                
                st.markdown("##### 退休金設定")
                enable_pension = st.toggle("啟用台灣勞退/勞保年金估算")
                if enable_pension:
                    current_age = st.number_input("目前年齡", value=30, step=1)
                    pension_start_age = st.number_input("預期開始領取年齡", value=65, step=1)
                    pension_monthly_input = st.number_input(f"預估每月年金 ({display_unit})", value=float(30000 / scale), step=float(1000 / scale) if scale <= 1000 else 1.0)
                    pension_monthly = pension_monthly_input * scale
                else:
                    current_age = 30
                    pension_start_age = 65
                    pension_monthly = 0
                    
            with tab_invest:
                st.markdown("##### 投資設定")
                start_assets_input = st.number_input(f"初始投資資產 ({display_unit})", value=float(1000000 / scale), step=float(100000 / scale) if scale <= 100000 else 1.0)
                start_assets = start_assets_input * scale
                roi = st.slider("預期投資報酬率 (%)", min_value=0.0, max_value=20.0, value=6.0, step=0.5)
                years_to_simulate = st.slider("模擬年數", min_value=10, max_value=60, value=54, step=1)

        with col_right:
            st.subheader("💸 支出與台灣重大花費")
            tab_expense, tab_milestones = st.tabs(["🍔 日常與娛樂", "⚠️ 台灣重大花費設定"])
            
            with tab_expense:
                st.markdown("##### 日常支出與通膨")
                expense_tier = st.selectbox("日常支出級距", options=["低", "中", "高"], index=1)
                tier_mapping = {"低": 400000, "中": 600000, "高": 800000}
                base_expense = tier_mapping[expense_tier]
                inflation = st.slider("預估通膨率 (%)", min_value=0.0, max_value=10.0, value=2.5, step=0.1)
                
            with tab_milestones:
                st.markdown("##### 基礎重大里程碑")
                retirement_year = st.number_input("預定退休年份 (薪資歸零)", value=2041, step=1)
                
                st.markdown("---")
                st.markdown("##### 動態重大花費設定")
                dynamic_milestones = st.multiselect("選擇重大花費項目", options=["買房", "定期換車", "育兒", "孝親"])
                
                house_year = None
                if "買房" in dynamic_milestones:
                    st.markdown("###### 🏠 買房設定")
                    house_year = st.number_input("預定買房年份", value=2030, step=1)
                    house_downpayment_input = st.number_input(f"買房頭期款 ({display_unit})", value=float(5000000 / scale), step=float(100000 / scale) if scale <= 100000 else 1.0)
                    house_downpayment = house_downpayment_input * scale
                    annual_mortgage_input = st.number_input(f"每年房貸本息 ({display_unit})", value=float(668000 / scale), step=float(10000 / scale) if scale <= 10000 else 1.0)
                    annual_mortgage = annual_mortgage_input * scale
                    mortgage_years = st.number_input("房貸還款年限", value=30, step=1)

                if "定期換車" in dynamic_milestones:
                    st.markdown("###### 🚗 定期換車設定")
                    car_freq = st.number_input("換車頻率 (每 N 年)", value=10, step=1)
                    car_budget_input = st.number_input(f"單台購車預算 ({display_unit})", value=float(1000000 / scale), step=float(100000 / scale) if scale <= 100000 else 1.0)
                    car_budget = car_budget_input * scale
                    car_end_year = st.number_input("換車計畫截止年份", value=2070, step=1)
    
    st.markdown("---")
    if st.button("📊 儲存配置並執行模擬", type="primary", use_container_width=True):
        if data_mode == "使用 CSV 基準資料":
            if uploaded_file is None:
                st.error("請先上傳 CSV 檔案，或切換至「自訂手動模擬」！")
                st.stop()
            df = load_baseline_data(uploaded_file)
            ret_year = 2041
            st.session_state.milestones_list = []
        else:
            milestones_list = []
            
            if "買房" in dynamic_milestones:
                milestones_list.append({"name": "買房頭期款", "type": "one_time", "year": house_year, "cost": house_downpayment})
                milestones_list.append({"name": "房貸", "type": "duration", "start_year": house_year, "end_year": house_year + mortgage_years - 1, "annual_cost": annual_mortgage})
            
            if "定期換車" in dynamic_milestones:
                milestones_list.append({"name": "定期換車", "type": "interval", "start_year": 2030, "end_year": car_end_year, "interval": car_freq, "cost": car_budget})
            
            df = run_simulation(
                start_year=2027,
                years_to_simulate=years_to_simulate,
                start_assets=start_assets,
                start_salary=start_salary,
                salary_growth=salary_growth,
                base_expense=base_expense,
                inflation=inflation,
                roi=roi,
                retirement_year=retirement_year,
                enable_pension=enable_pension,
                current_age=current_age,
                pension_start_age=pension_start_age,
                pension_monthly=pension_monthly,
                milestones_list=milestones_list
            )
            ret_year = retirement_year
            st.session_state.milestones_list = milestones_list
        
        st.session_state.sim_data = df
        st.session_state.data_mode = data_mode
        st.session_state.ret_year = ret_year
        st.switch_page(page_dashboard_obj)

def page_dashboard():
    st.title("📊 退休資產模擬看板")
    
    display_unit = st.radio("顯示數值單位", ["元", "萬元", "k", "M"], horizontal=True)
    
    if "sim_data" not in st.session_state or st.session_state.sim_data.empty:
        st.warning("⚠️ 請先至左側「⚙️ 財務參數設定中心」設定參數並點擊執行模擬。")
        if st.button("前往設定", type="primary"):
            st.switch_page(page_settings_obj)
        st.stop()
        
    df = st.session_state.sim_data
    data_mode = st.session_state.data_mode
    ret_year = st.session_state.ret_year
    house_year = st.session_state.get('house_year')

    # --- KPI Calculations ---
    df['Passive Income Exceeds Expenses'] = (df['Investment Return'] + df.get('Pension Income', 0)) > df['Total Expenses']
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
        st.metric(label=f"2040 年底期末資產 ({display_unit})", value=format_value(assets_2040, display_unit))
    with col3:
        st.markdown(f"**長期財務永續性評估**")
        st.markdown(f"<h3 style='color: {sustainability_color}; margin-top: -10px;'>{sustainability}</h3>", unsafe_allow_html=True)

    st.markdown("---")

    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric(label=f"4% 安全提領金 ({display_unit})", value=format_value(safe_withdrawal, display_unit))
    with col5:
        st.metric(label=f"退休首年 ({ret_year}) 總支出 ({display_unit})", value=format_value(ret_expenses, display_unit))
    with col6:
        rule_status = "安全 ✅" if safe_withdrawal >= ret_expenses else "危險 ⚠️"
        rule_color = "green" if safe_withdrawal >= ret_expenses else "red"
        st.markdown(f"**4% 法則健康檢查**")
        st.markdown(f"<h3 style='color: {rule_color}; margin-top: -10px;'>{rule_status}</h3>", unsafe_allow_html=True)

    st.markdown("---")

    # --- CHARTS ---
    # Apply Unit Scaling for Charts
    plot_df = df.copy()
    scale = 1
    if display_unit == "萬元":
        scale = 10000
    elif display_unit == "k":
        scale = 1000
    elif display_unit == "M":
        scale = 1000000

    if scale != 1:
        for col in ["Ending Investment Assets", "Net Salary", "Investment Return", "Pension Income", "Total Expenses"]:
            if col in plot_df.columns:
                plot_df[col] = plot_df[col] / scale

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("資產累積曲線")
        fig1 = px.line(
            plot_df, 
            x="Year", 
            y="Ending Investment Assets", 
            title=f"歷年期末投資資產走勢 ({display_unit})",
            markers=True,
            labels={"Year": "年份", "Ending Investment Assets": f"期末投資資產 ({display_unit})"}
        )
        # Add vertical lines for dynamic milestones
        if 'milestones_list' in st.session_state:
            for m in st.session_state.milestones_list:
                if m["type"] == "one_time" and m["year"] in df['Year'].values:
                    fig1.add_vline(x=m["year"], line_width=1, line_dash="dash", line_color="purple", annotation_text=f'{m["name"]}', annotation_position="top right")
                elif m["type"] == "interval":
                    for y in range(m["start_year"], m["end_year"] + 1, m["interval"]):
                        if y in df['Year'].values:
                            fig1.add_vline(x=y, line_width=1, line_dash="dash", line_color="purple", annotation_text=f'{m["name"]}', annotation_position="top right")
                            
        if ret_year and ret_year in df['Year'].values:
            fig1.add_vline(x=ret_year, line_width=2, line_dash="dash", line_color="red", annotation_text=f"退休 ({ret_year})", annotation_position="top left")

        fig1.update_yaxes(tickformat=",.1f" if scale != 1 else ",.0f")
        st.plotly_chart(fig1, width='stretch')

    with col_chart2:
        st.subheader("收入與報酬 vs. 總支出")
        fig2 = go.Figure()
        
        # Net Salary
        fig2.add_trace(go.Bar(
            x=plot_df['Year'], 
            y=plot_df['Net Salary'], 
            name=f'稅後淨薪資 ({display_unit})', 
            marker_color='blue'
        ))
        
        # Investment Return (Passive Income)
        fig2.add_trace(go.Bar(
            x=plot_df['Year'], 
            y=plot_df['Investment Return'], 
            name=f'投資報酬 ({display_unit})', 
            marker_color='green'
        ))
        
        # Pension Income (Passive Income)
        if 'Pension Income' in plot_df.columns and plot_df['Pension Income'].sum() > 0:
            fig2.add_trace(go.Bar(
                x=plot_df['Year'], 
                y=plot_df['Pension Income'], 
                name=f'勞退/勞保年金 ({display_unit})', 
                marker_color='orange'
            ))
        
        # Total Expenses (Negative for comparison or line overlay)
        fig2.add_trace(go.Scatter(
            x=plot_df['Year'], 
            y=plot_df['Total Expenses'], 
            name=f'總支出 ({display_unit})', 
            mode='lines+markers',
            line=dict(color='red', width=3)
        ))
        
        # Add vertical lines for dynamic milestones
        if 'milestones_list' in st.session_state:
            for m in st.session_state.milestones_list:
                if m["type"] == "one_time" and m["year"] in df['Year'].values:
                    fig2.add_vline(x=m["year"], line_width=1, line_dash="dash", line_color="purple", annotation_text=f'{m["name"]}', annotation_position="top right")
                elif m["type"] == "interval":
                    for y in range(m["start_year"], m["end_year"] + 1, m["interval"]):
                        if y in df['Year'].values:
                            fig2.add_vline(x=y, line_width=1, line_dash="dash", line_color="purple", annotation_text=f'{m["name"]}', annotation_position="top right")
                            
        if ret_year and ret_year in df['Year'].values:
            fig2.add_vline(x=ret_year, line_width=2, line_dash="dash", line_color="red", annotation_text=f"退休 ({ret_year})", annotation_position="top left")
        
        fig2.update_layout(
            barmode='stack',
            title=f"資金來源 vs. 總支出對比 ({display_unit})",
            yaxis=dict(tickformat=",.1f" if scale != 1 else ",.0f")
        )
        st.plotly_chart(fig2, width='stretch')

    # --- DATA TABLE ---
    st.subheader("歷年詳細模擬數據")
    
    column_mapping = {
        "Year": "年份",
        "Gross Salary": "稅前年薪",
        "Income Tax": "所得稅",
        "Net Salary": "稅後淨薪資",
        "Pension Income": "年金收入",
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
