import asyncio
import streamlit as st
import pandas as pd
import pandas_datareader as pdr
import datetime
import numpy as np

# Define the function to perform the backtesting
async def backtest(ticker, start_date, end_date, initial_investment, ma_period, buy_below_pct):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, pdr.get_data_yahoo, ticker, start_date, end_date)

    data[f'SMA_{ma_period}'] = data['Close'].rolling(window=ma_period).mean()
    data['Buy_Signal'] = data['Close'].shift() < data[f'SMA_{ma_period}'].shift() * (1 - buy_below_pct / 100)
    data['Sell_Signal'] = data['Close'].shift() > data[f'SMA_{ma_period}'].shift()

    money = initial_investment
    shares = 0.0
    in_position = False

    for i in range(len(data)):
        if data['Buy_Signal'].iloc[i] and not in_position:
            shares = money / data['Close'].iloc[i]
            in_position = True
        elif data['Sell_Signal'].iloc[i] and in_position:
            money = shares * data['Close'].iloc[i]
            shares = 0.0
            in_position = False

    if in_position:
        money = shares * data['Close'].iloc[-1]

    # Calculate performance metrics
    years = (end_date - start_date).days / 365.25
    annualized_return = (money / initial_investment) ** (1/years) - 1

    # Assuming risk-free rate to be 0 for simplicity, and calculate the Sharpe ratio
    sharpe_ratio = data['Close'].pct_change().dropna().mean() / data['Close'].pct_change().dropna().std() * np.sqrt(252)

    return money, annualized_return, sharpe_ratio, data

# Streamlit code to create the web UI
st.title("SPX Backtesting Tool")

# Define inputs
ticker = '^GSPC'
start_date = st.date_input("Start Date", datetime.date(2013, 1, 1))
end_date = st.date_input("End Date", datetime.date(2023, 1, 1))
initial_investment = st.number_input("Initial Investment", min_value=0.0, value=10000.0, step=100.0)
ma_period = st.number_input("Moving Average Period (in days)", min_value=1, value=50, step=1)
buy_below_pct = st.number_input("Buy Below Moving Average (in %)", min_value=0.0, value=5.0, step=0.1)

if st.button("Run Backtest"):
    # Run the backtest function asynchronously
    final_amount, annualized_return, sharpe, data = asyncio.run(backtest(ticker, start_date, end_date, initial_investment, ma_period, buy_below_pct))
    
    st.write(f"Final Amount: ${final_amount:.2f}")
    st.write(f"Annualized Return: {annualized_return*100:.2f}%")
    st.write(f"Sharpe Ratio: {sharpe:.2f}")

    # Plot the closing prices and the moving average
    st.line_chart(data[['Close', f'SMA_{ma_period}']])
