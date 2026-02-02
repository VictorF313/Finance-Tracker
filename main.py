import streamlit as st
import plotly.express as px
import numpy as np
import pandas as pd

# Pandas

# Importing pandas

df = pd.read_excel(
    "/home/sharique/Desktop/Code/Projects/FinanceTracker/BankStatement(Outdated).xlsx"
)


# Setting streamlit Dashboard

st.set_page_config(
    layout="wide", page_title="📊 Finance Dashboard", initial_sidebar_state="expanded"
)
st.title("💵 Finance Dashboard")


# Setting streamlit filters

dateFilter = df[["Transaction Date"]].copy()
dateFilter["Transaction Date"] = pd.to_datetime(dateFilter["Transaction Date"])

startDate = dateFilter["Transaction Date"].iloc[0]
endDate = dateFilter["Transaction Date"].iloc[-1]

with st.sidebar:

    st.header("Filters")
    timeframe = st.date_input(
        label="Select date",
        value=(startDate, endDate),
        min_value=startDate,
        max_value=endDate,
        format="DD/MM/YYYY",
    )

if len(timeframe) == 2:

    timeframe = pd.DataFrame([timeframe])
    timeframe["0"] = pd.to_datetime(timeframe[0])
    timeframe["1"] = pd.to_datetime(timeframe[1])
    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"])

    df["StartPeriod"] = timeframe[0]
    df["EndPeriod"] = timeframe[1]

    df["StartPeriod"] = df["StartPeriod"].ffill()
    df["EndPeriod"] = df["EndPeriod"].ffill()

    df = df.where(
        (df["Transaction Date"] >= df["StartPeriod"])
        & (df["Transaction Date"] <= df["EndPeriod"])
    )

# Data cleaning & pre processing
df = df.drop("Value Date", axis=1)  # Removing the Value Date column
df["Category"] = np.nan
df["Category"] = (
    df["Particulars"].str[0:3].str.strip()
)  # Accessing first 4 letters from df["Particulars"] column


# Mapping category of payments in df["Category"] column

df["Category"] = df["Category"].map(
    {
        "ATM": "ATM Withdrawal",
        "UPI": "UPI Transaction",
        "NEF": "NEFT",
        "Non": "Non maintenance charges",
        "CGS": "Non maintenance charges",
        "SGS": "Non maintenance charges",
        "FD": "FD Maturity Interest",
        "BIL": "Bill Payment",
        "Rev": "Reverse Non maintenance charges",
        "IFT": "IFT",
        "MON": "Monthly Interest",
        "EMI": "EMI deduction",
        "POS": "Card Payment",
    }
)

# Creating a pivot table based on category wise debit and credit amount

# Debit
pivot_debit = df.groupby(by="Category")["Debit"].sum().reset_index()
pivot_debit = pivot_debit.where(pivot_debit["Debit"] > 0, other=0)
indices_to_drop_debit = pivot_debit[pivot_debit["Debit"] == 0].index
debit = pivot_debit.drop(indices_to_drop_debit)
debit = debit.sort_values(by="Debit")
debitedAmount = round(debit["Debit"].sum())

# Credit
pivot_credit = df.groupby(by="Category")["Credit"].sum().reset_index()
pivot_credit = pivot_credit.where(pivot_credit["Credit"] > 0, other=0)
indices_to_drop_credit = pivot_credit[pivot_credit["Credit"] == 0].index
credit = pivot_credit.drop(indices_to_drop_credit)
credit = credit.sort_values(by="Credit")
creditedAmount = round(credit["Credit"].sum())


# Cash Flow analysis
netCashFlow = creditedAmount - debitedAmount

if (netCashFlow != 0) and (creditedAmount != 0):
    netCashFlowPercent = ((netCashFlow) / creditedAmount) * 100
else:
    netCashFlowPercent = 0

netCashFlowPercent = round(netCashFlowPercent)

# Sum of transactions based on day of week

transactions = df[["Transaction Date", "Credit", "Debit"]].copy()
transactions = transactions.astype(
    {"Transaction Date": "datetime64[ns]", "Credit": "float64", "Debit": "float64"}
)

transactions["Credit"] = transactions["Credit"].fillna(0)
transactions["Debit"] = transactions["Debit"].fillna(0)

daywiseTransactons = transactions.pivot_table(
    index="Transaction Date", values=["Credit", "Debit"], aggfunc="sum"
).reset_index()

daywiseTransactons["WeekDay"] = daywiseTransactons["Transaction Date"]
daywiseTransactons["DayOfWeek"] = daywiseTransactons["WeekDay"].dt.day_name()
daywiseTransactons = daywiseTransactons.pivot_table(
    index="DayOfWeek", values=["Credit", "Debit"], aggfunc="sum"
).reset_index()

daywiseTransactons["DayIndex"] = daywiseTransactons["DayOfWeek"].map(
    {
        "Monday": 1,
        "Tuesday": 2,
        "Wednesday": 3,
        "Thursday": 4,
        "Friday": 5,
        "Saturday": 6,
        "Sunday": 7,
    }
)

daywiseTransactons = daywiseTransactons.sort_values(by="DayIndex")
daywiseTransactons = daywiseTransactons.drop("DayIndex", axis=1)
daywiseTransactons = daywiseTransactons.set_index("DayOfWeek").T


tableData = daywiseTransactons.T.reset_index()
tableData = (
    tableData.astype({"Credit": "int64", "Debit": "int64"}).set_index("DayOfWeek").T
)

# Monthly trend

monthlyTrend = df[["Transaction Date", "Credit", "Debit"]].copy()
monthlyTrend["Transaction Date"] = pd.to_datetime(monthlyTrend["Transaction Date"])
monthlyTrend["MonthIndex"] = monthlyTrend["Transaction Date"].dt.month
monthlyTrend["Month"] = monthlyTrend["Transaction Date"].dt.month_name()
monthlyTrend = monthlyTrend.pivot_table(
    index=["Month", "MonthIndex"], values=["Credit", "Debit"], aggfunc="sum"
).reset_index()

monthlyTrend = monthlyTrend.sort_values(by="MonthIndex")
monthlyTrend["NetCashFlow"] = monthlyTrend["Credit"] - monthlyTrend["Debit"]

# Streamlit

# Creating Tabs
tab1, tab2 = st.tabs(["📈 Charts", "📑 Data"])

# Setting KPIs

with tab1.container(vertical_alignment="center"):
    # Setting metric cards for credit and debit
    with st.container(border=True, horizontal=True, horizontal_alignment="distribute"):
        a, b, c = st.columns([1, 1, 1])
        a.metric(
            label=":green[Total Credit]",
            value=creditedAmount,
            border=True,
            delta="N/A",
            delta_arrow="off",
            chart_data=monthlyTrend["Credit"],
            chart_type="area",
        )
        b.metric(
            label=":red[Total Debit]",
            value=debitedAmount,
            border=True,
            delta="N/A",
            delta_arrow="off",
            delta_color="red",
            chart_data=monthlyTrend["Debit"],
            chart_type="area",
        )

        if netCashFlow < 0:
            c.metric(
                label=":red[Net Cash Flow]",
                value=netCashFlow,
                border=True,
                delta=f"{netCashFlowPercent}%",
                chart_data=monthlyTrend["NetCashFlow"],
                chart_type="area",
            )
        elif netCashFlow > 0:

            c.metric(
                label=":green[Net Cash Flow]",
                value=netCashFlow,
                border=True,
                delta=f"{netCashFlowPercent}%",
                chart_data=monthlyTrend["NetCashFlow"],
                chart_type="area",
            )
        else:
            c.metric(
                label="Net Cash Flow",
                value=netCashFlow,
                border=True,
                width=200,
                delta=f"{netCashFlowPercent}%",
                chart_data=monthlyTrend["NetCashFlow"],
                chart_type="area",
            )

    # Setting graphs for credit and debit

    with st.container(
        gap=None,
        border=True,
        vertical_alignment="center",
        horizontal=True,
        horizontal_alignment="center",
    ):
        a, b = st.columns(2)

        # Credit
        a.subheader(":green[Monthly Credit by Category]")
        figMonthlyCredit = px.bar(
            credit,
            x="Category",
            y="Credit",
            text="Credit",
            color_discrete_sequence=["#03fc8c"],
            height=500,
            width=100,
        )
        figMonthlyCredit.update_traces(textposition="outside")
        a.plotly_chart(figMonthlyCredit)

        # Debit
        b.subheader(":red[Monthly Debit by Category]")
        figMonthlyDebit = px.bar(
            debit,
            x="Category",
            y="Debit",
            text="Debit",
            color_discrete_sequence=["#a83232"],
            height=500,
            width=100,
        )
        figMonthlyDebit.update_traces(textposition="outside")
        b.plotly_chart(figMonthlyDebit)

    # Heatmap
    with st.container(border=True):
        st.subheader("Day Wise Transaction Amounts (Credit & Debit)")
        option = st.selectbox(
            "Select Color Palette",
            (
                "aggrnyl",
                "agsunset",
                "algae",
                "blues",
                "blackbody",
                "bluered",
                "blugrn",
                "bupu",
                "teal",
                "sunsetdark",
            ),
            width=150,
        )

        heatmap = px.imshow(
            daywiseTransactons,
            height=300,
            width=100,
            labels=dict(x="Day Of Week", y="Amount"),
            text_auto=True,
            color_continuous_scale=option,
            aspect="auto",
        )
        st.plotly_chart(heatmap)


# Setting Data Tab

tab2.subheader("Monthwise Cashflow Details")
tab2.dataframe(monthlyTrend[["Month", "Credit", "Debit", "NetCashFlow"]])

tab2.subheader("Categorywise Credit")
tab2.dataframe(credit)

tab2.subheader("Categorywise Debit")
tab2.dataframe(debit)

tab2.subheader("Day Wise Transaction Amounts (Credit & Debit)")
tab2.dataframe(tableData)
