import pandas as pd
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt

def get_mfv(ticker, period='1y'):
    comp = yf.Ticker(ticker)
    data = comp.history(period=period)
    high_low_range = data['High'] - data['Low']
    data['MFM'] = ((data['Close'] - data['Low']) - (data['High'] - data['Close'])) / high_low_range
    data['MFV'] = round(data['MFM'] * data['Volume'], 1)
    return data['MFV']

ticker='NVDA'
period='2y'
mfv_df = get_mfv(ticker, period=period)
price = yf.Ticker(ticker).history(period=period)

avg_value = mfv_df.mean().round(1)
avg = pd.Series(avg_value, index=mfv_df.index)
ma10 = mfv_df.rolling(window=10).mean().round(1)
ma60 = mfv_df.rolling(window=60).mean().round(1)
ma120 = mfv_df.rolling(window=120).mean().round(1)
ma240 = mfv_df.rolling(window=240).mean().round(1)
ma_df = pd.concat([avg, ma10, ma60, ma120, ma240], axis=1)
ma_df.columns = ['avg', 'ma10', 'ma60', 'ma120', 'ma240']

prev = ma_df.shift(1)
cond_today = ma_df['ma10'] > ma_df['ma60']
cond_yesterday = prev['ma10'] <= prev['ma60']
golden_cross_df = ma_df[cond_today & cond_yesterday]

cond_today_inv = ma_df['ma10'] < ma_df['ma60']
cond_yesterday_inv = prev['ma10'] >= prev['ma60']
dead_cross_df = ma_df[cond_today_inv & cond_yesterday_inv]

prev = ma_df.shift(1)
cond_gc = (ma_df['ma10'] > ma_df['ma60']) & (prev['ma10'] <= prev['ma60'])
cond_dc = (ma_df['ma10'] < ma_df['ma60']) & (prev['ma10'] >= prev['ma60'])
gc_points = ma_df[cond_gc]
dc_points = ma_df[cond_dc]

price_res = price.reset_index()
golden_cross_res = golden_cross_df.reset_index()
dead_cross_res = dead_cross_df.reset_index()

buy = price_res[price_res['Date'].isin(golden_cross_res['Date'])]
buy = buy[['Date', 'Close']]

sell = price_res[price_res['Date'].isin(dead_cross_res['Date'])]
sell = sell[['Date', 'Close']]


# -----------------------------
# Backtesting Logic
# -----------------------------

# 1. Prepare Signals
buy = buy.copy()
sell = sell.copy()
buy['Signal'] = 'BUY'
sell['Signal'] = 'SELL'

# Combine and Sort
all_signals = pd.concat([buy, sell]).sort_values('Date')
all_signals = all_signals.reset_index(drop=True)

# 2. Simulate Trades
trades = []
position = False
entry_price = 0
entry_date = None

for index, row in all_signals.iterrows():
    # BUY CONDITION
    if row['Signal'] == 'BUY' and not position:
        entry_price = row['Close']
        entry_date = row['Date']
        position = True
        
    # SELL CONDITION
    elif row['Signal'] == 'SELL' and position:
        exit_price = row['Close']
        exit_date = row['Date']
        pct_change = (exit_price - entry_price) / entry_price
        
        trades.append({
            'Entry_Date': entry_date,
            'Exit_Date': exit_date,
            'Entry_Price': entry_price,
            'Exit_Price': exit_price,
            'Return': pct_change
        })
        position = False

# 3. Create Results DataFrame
trades_df = pd.DataFrame(trades)

if not trades_df.empty:
    # Cumulative Return (Compounded)
    trades_df['Cumulative_Return'] = (1 + trades_df['Return']).cumprod()
    
    # Save Results
    trades_df.to_csv(f'{ticker}_adl_backtest_trades.csv', index=False)
    
    print("Backtest Complete!")
    print(f"Total Trades: {len(trades_df)}")
    print(f"Final Cumulative Return: {trades_df['Cumulative_Return'].iloc[-1]:.4f}")
    print("\nRecent Trades:")
    print(trades_df.tail())
else:
    print("No complete trades generated.")
