import os
import time
import logging
from datetime import datetime
import MetaTrader5 as mt5
from supabase import create_client
import pandas as pd
from strategies_full import strategy_map

from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# --- MT5 CONNECT ---
def connect_mt5(user):
    if not mt5.initialize():
        logging.error("MT5 init failed")
        return False
    return mt5.login(user["mt5_login"], user["mt5_password"], user["mt5_server"])

# --- TRADE EXECUTION ---
def execute_trade(user, signal, symbol, lot_size, sl_points=50, tp_points=100):
    if not connect_mt5(user):
        return False

    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        logging.warning(f"No price data for {symbol}")
        return False

    price = tick.ask if signal == "buy" else tick.bid
    deviation = 10
    sl = price - sl_points * 0.0001 if signal == "buy" else price + sl_points * 0.0001
    tp = price + tp_points * 0.0001 if signal == "buy" else price - tp_points * 0.0001
    order_type = mt5.ORDER_TYPE_BUY if signal == "buy" else mt5.ORDER_TYPE_SELL

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": deviation,
        "magic": 234000,
        "comment": "SupabaseBot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        log_trade(user["id"], symbol, signal, price)
        logging.info(f"{signal.upper()} trade executed on {symbol}")
        return True
    else:
        logging.warning(f"Trade failed: {result.comment}")
        return False

# --- TRADE LOGGING ---
def log_trade(user_id, symbol, trade_type, entry_price):
    trade = {
        "user_id": user_id,
        "symbol": symbol,
        "type": trade_type,
        "lot_size": 0.1,
        "entry_price": entry_price,
        "exit_price": 0,
        "profit": 0,
        "strategy": "from_supabase",
        "opened_at": datetime.utcnow().isoformat()
    }
    supabase.table("trades").insert(trade).execute()

# --- MAIN BOT LOOP ---
def run_bot():
    while True:
        try:
            users = supabase.table("users").select("*").execute().data
            for user in users:
                control = supabase.table("bot_control").select("*").eq("user_id", user["id"]).execute().data
                if control and control[0].get("start_bot") == True:
                    settings = supabase.table("settings").select("*").eq("user_id", user["id"]).execute().data
                    if not settings:
                        continue
                    settings = settings[0]
                    strategy_name = settings.get("selected_strategy")
                    strategy_func = strategy_map.get(strategy_name)
                    if not strategy_func:
                        logging.warning(f"Strategy '{strategy_name}' not found.")
                        continue

                    for symbol in settings["symbols"]:
                        bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 50)
                        if bars is None or len(bars) < 10:
                            continue
                        df = pd.DataFrame(bars)
                        df = strategy_func(df)

                        signal_val = df["signal"].iloc[-1]
                        signal = "buy" if signal_val == 1 else "sell" if signal_val == -1 else "hold"

                        if signal in ["buy", "sell"]:
                            execute_trade(user, signal, symbol, settings["risk_percent"] / 100)
        except Exception as e:
            logging.error(f"Bot loop error: {e}")
        time.sleep(10)

if __name__ == "__main__":
    run_bot()
