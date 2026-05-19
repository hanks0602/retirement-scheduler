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

def run_simulation(start_year, years_to_simulate, start_assets, start_salary, salary_growth, base_expense, inflation, roi, house_year, house_cost):
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
        gross_salary = current_salary
        tax = calculate_tax(gross_salary)
        net_salary = gross_salary - tax
        
        # Apply special milestone expenses (e.g., house purchase)
        milestone_cost = house_cost if current_year == house_year else 0
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
# STREAMLIT UI LAYOUT
# ==========================================
st.set_page_config(page_title="Retirement Simulator", layout="wide")
st.title("Financial Planning & Retirement Simulator")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Configuration")
data_mode = st.sidebar.radio("Data Source Toggle", options=["Use CSV Baseline Data", "Custom Manual Simulation"])

df = pd.DataFrame()

if data_mode == "Use CSV Baseline Data":
    st.sidebar.info("Loading baseline configuration from personal_data.csv")
    df = load_baseline_data("personal_data.csv")
    
else:
    st.sidebar.subheader("Income Controls")
    start_salary = st.sidebar.number_input("Starting Gross Salary (TWD)", value=1000000, step=50000)
    salary_growth = st.sidebar.slider("Annual Salary Growth Rate (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.5)
    
    st.sidebar.subheader("Expense & Inflation Controls")
    expense_tier = st.sidebar.selectbox("Expense Tier", options=["Low", "Medium", "High"], index=1)
    
    tier_mapping = {"Low": 400000, "Medium": 600000, "High": 800000}
    base_expense = tier_mapping[expense_tier]
    
    inflation = st.sidebar.slider("Inflation Rate (%)", min_value=0.0, max_value=10.0, value=2.5, step=0.1)
    
    st.sidebar.subheader("Investment Controls")
    start_assets = st.sidebar.number_input("Starting Investment Assets (TWD)", value=1000000, step=100000)
    roi = st.sidebar.slider("Expected ROI (%)", min_value=0.0, max_value=20.0, value=6.0, step=0.5)
    
    st.sidebar.subheader("Key Milestones (Overrides)")
    house_year = st.sidebar.number_input("House Purchase Year", value=2035, step=1)
    house_cost = st.sidebar.number_input("House Downpayment/Total Cost (TWD)", value=3000000, step=100000)
    
    years_to_simulate = st.sidebar.slider("Simulation Years", min_value=10, max_value=60, value=50, step=5)
    
    # Run dynamic simulation
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
        house_cost=house_cost
    )

# --- MAIN DASHBOARD ---
if df.empty:
    st.warning("No data available to display.")
    st.stop()

# KPI Calculations
df['Passive Income Exceeds Expenses'] = df['Investment Return'] > df['Total Expenses']
crossover_years = df[df['Passive Income Exceeds Expenses']]['Year']

retirement_age_text = "Not Achieved"
if not crossover_years.empty:
    retirement_year = crossover_years.iloc[0]
    retirement_age_text = str(retirement_year)

peak_net_worth = df['Ending Investment Assets'].max()

# Sustainability Score
final_assets = df.iloc[-1]['Ending Investment Assets']
if final_assets < 0:
    sustainability = "Critical (Depleted)"
    sustainability_color = "red"
elif final_assets < df.iloc[0]['Ending Investment Assets']:
    sustainability = "Warning (Decreasing)"
    sustainability_color = "orange"
else:
    sustainability = "Safe (Growing)"
    sustainability_color = "green"

# Render KPIs
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Projected Retirement Year (Crossover)", value=retirement_age_text)
with col2:
    st.metric(label="Peak Net Worth (TWD)", value=f"{peak_net_worth:,.0f}")
with col3:
    st.markdown(f"**Financial Sustainability Status**")
    st.markdown(f"<h3 style='color: {sustainability_color}; margin-top: -10px;'>{sustainability}</h3>", unsafe_allow_html=True)

st.markdown("---")

# --- CHARTS ---
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Asset Accumulation Curve")
    fig1 = px.line(
        df, 
        x="Year", 
        y="Ending Investment Assets", 
        title="Projected Net Worth Over Time",
        markers=True
    )
    fig1.update_yaxes(tickformat=",.0f")
    st.plotly_chart(fig1, use_container_width=True)

with col_chart2:
    st.subheader("Income & Returns vs Expenses")
    fig2 = go.Figure()
    
    # Net Salary
    fig2.add_trace(go.Bar(
        x=df['Year'], 
        y=df['Net Salary'], 
        name='Net Salary', 
        marker_color='blue'
    ))
    
    # Investment Return (Passive Income)
    fig2.add_trace(go.Bar(
        x=df['Year'], 
        y=df['Investment Return'], 
        name='Investment Return', 
        marker_color='green'
    ))
    
    # Total Expenses (Negative for comparison or line overlay)
    fig2.add_trace(go.Scatter(
        x=df['Year'], 
        y=df['Total Expenses'], 
        name='Total Expenses', 
        mode='lines+markers',
        line=dict(color='red', width=3)
    ))
    
    fig2.update_layout(
        barmode='stack',
        title="Income Sources vs Total Expenses",
        yaxis=dict(tickformat=",.0f")
    )
    st.plotly_chart(fig2, use_container_width=True)

# --- DATA TABLE ---
st.subheader("Detailed Projection Data")

# Format dataframe for display
format_dict = {col: '{:,.0f}' for col in df.columns if df[col].dtype in ['float64', 'int64'] and col != 'Year'}
format_dict['Year'] = '{:.0f}'

styled_df = df.style.format(format_dict).map(
    lambda x: 'color: red' if isinstance(x, (int, float)) and x < 0 else '', 
    subset=['Annual Net Savings', 'Ending Investment Assets']
)

st.dataframe(styled_df, use_container_width=True, height=400)
