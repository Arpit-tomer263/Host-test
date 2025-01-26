from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters,CallbackQueryHandler
from flask import Flask, request
from threading import Thread
import pandas as pd
import json
from PIL import Image
import os
from PIL import ImageDraw, ImageFont
import matplotlib.pyplot as plt


# Flask setup
app = Flask(__name__)




Total_request = 0
Api_limit = 20000
admin_id = 5856117513

# Define CSV file path
CSV_FILE = 'data.csv'
main_csv_file = 'main.csv'
# Check if the CSV file exists and create headers if it doesn't
if not os.path.isfile(CSV_FILE):
    # Initialize CSV with headers
    df = pd.DataFrame(columns=['Type', 'Signal', 'Date/Time', 'Price', 'Contracts', 'Profit', 'Cum. Profit', 'Run-up', 'Drawdown'])
    df.to_csv(CSV_FILE, index=False)

def calculate_net_profit(trade_profit):
    # Ensure that trade_profit is a number (float)
    try:
        trade_profit = float(trade_profit)
    except ValueError:
        return "Invalid value for 'trade_profit'. Must be numeric."

    # Read the CSV file into a pandas DataFrame
    try:
        df = pd.read_csv('data.csv')
        
        # Ensure the 'Profit' column exists
        if 'Profit' not in df.columns:
            return "Error: 'Profit' column not found in CSV"
        
        # Convert the 'Profit' column to numeric values (forcing errors to NaN)
        df['Profit'] = pd.to_numeric(df['Profit'], errors='coerce')
        
        # Remove NaN values (those caused by non-numeric entries) for mean calculation
        df_cleaned = df.dropna(subset=['Profit'])

        # Calculate the average profit
        avg_profit = df_cleaned['Profit'].mean() if len(df_cleaned) > 0 else 0

        # Include the current trade profit in the calculation of the new average
        num_profits = len(df_cleaned) + 1

        # Calculate the new average profit (net profit)
        net_profit = (avg_profit * len(df_cleaned) + trade_profit) / num_profits

        # Return the net profit (average profit)
        return net_profit

    except Exception as e:
        return f"Error processing the CSV file: {e}"


Main_Capital = 9000000

def generate_dashboard():
    # Read the CSV file
    csv_file = 'data.csv'
    df = pd.read_csv(csv_file)
    
    def parse_dates(date_series):
        formats = ["%m/%d/%y %H:%M", "%Y-%m-%d %H:%M:%S"]  # List of formats to try
        for fmt in formats:
            try:
                return pd.to_datetime(date_series, format=fmt, errors='coerce')
            except ValueError:
                continue
        # If all formats fail, fall back to auto-parsing
        return pd.to_datetime(date_series, errors='coerce')

    df['Date/Time'] = parse_dates(df['Date/Time'])
    df['Profit'] = pd.to_numeric(df['Profit'], errors='coerce')

    # Calculate cumulative capital growth
    initial_capital = 9000000
    df['Capital'] = initial_capital + df['Profit'].cumsum()

    # Calculate other financial statistics
    total_trades = len(df)
    win_trades = df[df['Profit'] > 0].shape[0]
    loss_trades = df[df['Profit'] <= 0].shape[0]
    profit_percent = (win_trades / total_trades) * 100
    max_drawdown = df['Drawdown'].max()
    gross_profit = df[df['Profit'] > 0]['Profit'].sum()
    gross_loss = df[df['Profit'] < 0]['Profit'].sum()
    profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float('inf')
    avg_trade = abs(df['Profit'].sum() / total_trades) if total_trades != 0 else 0
    total_risk = df['Risk'].sum()
    total_reward = df['Reward'].sum()
    avg_risk_reward = f"{total_risk / total_reward:.2f}" if total_reward != 0 else 'N/A'
    max_loss = abs(df['Profit'][df['Profit'] < 0].min()) if not df[df['Profit'] < 0].empty else 0
    max_profit = df['Profit'][df['Profit'] > 0].max() if not df[df['Profit'] > 0].empty else 0
    total_profit = df[df['Profit'] > 0]['Profit'].sum()
    total_loss = abs(df[df['Profit'] < 0]['Profit'].sum())

    # New Y-Axis Limits
    df['Capital'] = initial_capital + df['Profit'].cumsum()
    y_axis_max = initial_capital + total_profit + 1000
    y_axis_min = initial_capital - (total_loss + 1000)
    # Center Y-Axis with Initial Capital
    y_axis_middle = initial_capital
    
    # Define chart dimensions and margins
    chart_width, chart_height = 600, 200
    chart_margin = 2

    # Define colors
    white = (209, 212, 220)
    green = (8, 153, 129)
    red = (242, 54, 69)
    background = (19, 23, 34)
    purple = (128, 0, 128)
    
    # Create an image with the specified background color
    img = Image.new(mode='RGB', size=(800, 500), color=background)
    draw = ImageDraw.Draw(img)
    
    # Load font
    font_path = "arial.ttf"  # Use a valid font path on your system
    font = ImageFont.truetype(font_path, size=13)
    
    # Define positions
    x, y = 10, 10
    spacing = 110
    
    # Draw the headers
    headers = ["Net Profit:", "Total Closed Trades:", "Win Rate:", "Profit Factor:", "Max Drawdown:", "Avg P/L per trade", "RR Ratio:"]
    values = [
        f"{df['Profit'].sum():,.2f}$",
        str(total_trades),
        f"{profit_percent:.2f}%",
        f"{profit_factor:.2f}",
        str(max_drawdown),
        f"{avg_trade:.2f}",
        avg_risk_reward
    ]

    # Colors for the values
    colors = [green if df['Profit'].sum() >= 0 else red, white, green, red, red, green, green]

    for i, header in enumerate(headers):
        header_bbox = draw.textbbox((0, 0), header, font=font)
        header_width = header_bbox[2] - header_bbox[0]
        header_x = x + i * spacing + (spacing - header_width) / 2
        draw.text((header_x, y), header, fill=white, font=font)

        # Draw value text
        value_bbox = draw.textbbox((0, 0), str(values[i]), font=font)
        value_width = value_bbox[2] - value_bbox[0]
        value_x = x + i * spacing + (spacing - value_width) / 2
        draw.text((value_x, y + 40), str(values[i]), fill=colors[i], font=font)
    
    # Calculate the center position for the chart
    chart_x = (img.width - chart_width) // 2
    chart_y = (img.height - chart_height) // 2
    # Normalize capital for chart
    min_capital = df['Capital'].min()
    max_capital = df['Capital'].max()
    initial_capital = df['Capital'].iloc[0]  # Initial Capital
    normalized_capital = (df['Capital'] - initial_capital) / (y_axis_max - y_axis_min) * (chart_height - 2 * chart_margin)

    # Find the Y-coordinate for the initial capital
    initial_y = chart_y + chart_height / 2  # Middle of the chart
    normalized_y = initial_y - normalized_capital.iloc[0]  # Adjust based on normalized value

    # Draw rectangle for the chart background
    draw.rectangle([chart_x, chart_y, chart_x + chart_width, chart_y + chart_height], outline=white, width=2)

    # Generate Y-axis labels dynamically
    num_labels = 5
    step = (y_axis_max - y_axis_middle) / ((num_labels - 1) / 2)

    y_labels = [
        f"${(y_axis_middle - step * ((num_labels - 1) / 2 - i)):,.0f}" for i in range(num_labels)
    ]

    for i, label in enumerate(y_labels):
        y = chart_y + chart_height - chart_margin - i * (chart_height - 2 * chart_margin) / (len(y_labels) - 1)
        draw.text((12, y), label, fill="white", font=font)

    # Draw the X-axis
    if total_trades > 6:
        gap = (chart_width - 2 * chart_margin) / 5
        x_positions = [chart_x + chart_margin + i * gap for i in range(6)]
        x_values = [1] + [(total_trades - 1) // 5 * i + 1 for i in range(1, 5)] + [total_trades]

        for i, (x_pos, val) in enumerate(zip(x_positions, x_values)):
            draw.text((x_pos - 5, chart_y + chart_height + 10), str(val), fill=white, font=font)
    else:
        for i in range(total_trades):
            x_position = chart_x + chart_margin + i * (chart_width - 2 * chart_margin) / (total_trades - 1)
            draw.text((x_position - 12, chart_y + chart_height + 10), str(i + 1), fill=white, font=font)

    for i in range(1, total_trades):
        # Calculate X1, Y1 (previous point)
        x1 = chart_x + chart_margin + (i - 1) * (chart_width - 2 * chart_margin) / (total_trades - 1)
        y1 = initial_y - normalized_capital.iloc[i - 1]

        # Calculate X2, Y2 (current point)
        x2 = chart_x + chart_margin + i * (chart_width - 2 * chart_margin) / (total_trades - 1)
        y2 = initial_y - normalized_capital.iloc[i]

        # Ensure Y-coordinates stay within the chart area
        y1 = min(max(y1, chart_y + chart_margin), chart_y + chart_height - chart_margin)
        y2 = min(max(y2, chart_y + chart_margin), chart_y + chart_height - chart_margin)

        # Line color (based on profit/loss)
        if df['Capital'].iloc[i] < Main_Capital:
            line_color = red  # Color the line red if the capital is less than Main_Capital (loss)
        elif df['Capital'].iloc[i] > Main_Capital:
            line_color = green  # Color the line green if the capital is greater than Main_Capital (profit)
        else:
            line_color = white  # This line is optional for when the capital equals Main_Capital

        draw.line([(x1, y1), (x2, y2)], fill=line_color, width=3)

    # Add additional information below the chart
    date_range = f"Date Range: From {df['Date/Time'].min().date()} to {df['Date/Time'].max().date()}"
    currency_pair = ', '.join(df['Pair'].unique())
    time_frame = ', '.join(str(tf) for tf in df['Timeframe'].unique())

    draw.text((250, chart_y + chart_height + 40), date_range, fill=white, font=font)
    draw.text((250, chart_y + chart_height + 60), f"Currency Pair: {currency_pair}", fill=white, font=font)
    draw.text((250, chart_y + chart_height + 80), f"Time Frame: {time_frame}", fill=white, font=font)

    # Save the image
    img.save('dashboard.png')

def ready_main_csv():
    # Define file paths
    main_file = 'main.csv'
    csv_file = 'data.csv'

    # Load data from data.csv into a DataFrame
    df = pd.read_csv(csv_file)

    # Calculate the required statistics
    net_profit = df['Profit'].sum()
    gross_profit = df[df['Profit'] > 0]['Profit'].sum()
    gross_loss = df[df['Profit'] < 0]['Profit'].sum()
    max_run_up = df['Run-up'].max()
    max_drawdown = df['Drawdown'].min()
    total_closed_trades = df.shape[0]

    # Calculate the number of winning and losing trades
    num_winning_trades = df[df['Profit'] > 0].shape[0]
    num_losing_trades = df[df['Profit'] < 0].shape[0]
    percent_profitable = (num_winning_trades / total_closed_trades) * 100

    # Calculate average trade, winning trade, and losing trade
    avg_trade = df['Profit'].mean()

    # Calculate Avg Winning Trade (positive profits only)
    avg_winning_trade = df[df['Profit'] > 0]['Profit'].mean()

    # Calculate Avg Losing Trade (negative profits only) -- Handle no losing trades
    avg_losing_trade = df[df['Profit'] < 0]['Profit'].mean() if num_losing_trades > 0 else None

    # Calculate Ratio Avg Win / Avg Loss
    ratio_avg_win_loss = avg_winning_trade / abs(avg_losing_trade) if avg_losing_trade and avg_losing_trade != 0 else None

    # Calculate the largest winning and losing trades
    largest_winning_trade = df['Profit'].max()
    largest_losing_trade = df['Profit'].min()

    # Profit factor (ratio of gross profit to gross loss)
    profit_factor = gross_profit / abs(gross_loss) if gross_loss != 0 else float('inf')

    # Calculate Average Risk/Reward Ratio (ratio of risk to reward per trade)
    df['Risk'] = abs(df['Risk'])  # Ensuring Risk is positive
    df['Reward'] = abs(df['Reward'])  # Ensuring Reward is positive
    avg_risk_reward_ratio = (df['Risk'] / df['Reward']).mean() if not df['Risk'].isnull().any() and not df['Reward'].isnull().any() else 0

    # Create a dictionary for the results
    results = {
        'Metric': [
            'Net Profit',
            'Gross Profit',
            'Gross Loss',
            'Max Run-up',
            'Max Drawdown',
            'Profit Factor',
            'Total Closed Trades',
            'Number Winning Trades',
            'Number Losing Trades',
            'Percent Profitable',
            'Avg Trade',
            'Avg Winning Trade',
            'Avg Losing Trade',
            'Ratio Avg Win/Avg Loss',
            'Largest Winning Trade',
            'Largest Losing Trade',
            'Avg Risk/Reward Ratio'
        ],
        'All USD': [
            net_profit,
            gross_profit,
            gross_loss,
            max_run_up,
            max_drawdown,
            profit_factor,
            total_closed_trades,
            num_winning_trades,
            num_losing_trades,
            percent_profitable,
            avg_trade,
            avg_winning_trade,
            avg_losing_trade if avg_losing_trade is not None else 'N/A',
            ratio_avg_win_loss if ratio_avg_win_loss is not None else 'N/A',
            largest_winning_trade,
            largest_losing_trade,
            avg_risk_reward_ratio
        ]
    }

    # Convert the results dictionary to a DataFrame
    results_df = pd.DataFrame(results)

    # Set the "Metric" column as the index (so that metrics are on the rows)
    results_df.set_index('Metric', inplace=True)

    # Save to main.csv
    results_df.to_csv(main_file)



# Bot logic
async def get_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Here is the report")
    generate_dashboard()
    with open('dashboard.png', 'rb') as file:
        await update.message.reply_photo(file)
        os.remove('dashboard.png')

async def get_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ready_main_csv()
    await update.message.reply_text("Here is the csv")
    with open(main_csv_file, 'rb') as file:
        await update.message.reply_document(file, filename=main_csv_file)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(user_id)
    await update.message.reply_text("Welcome to NRT-Forex Management Bot")
    keyboard = [
            [InlineKeyboardButton("Get DashBoard", callback_data='dashboard'),
            InlineKeyboardButton("Get Perfomance CSV", callback_data='csv_perform')],
            [InlineKeyboardButton("Get Trade List CSV", callback_data='csv_list'),
            InlineKeyboardButton("Check Limit",callback_data="check_limit")]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select the type of report you want to make:", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Check which callback query the user pressed and handle accordingly
    if query.data == 'dashboard':
        await query.edit_message_text("Sending DashBoard please wait....")
        generate_dashboard()
        with open('dashboard.png', 'rb') as file:
            # Use query.message, not update.message
            await query.message.reply_photo(file)
    elif query.data == 'csv_perform':
        await query.edit_message_text("Sending Perfomance CSV please wait....")
        ready_main_csv()
        with open(main_csv_file, 'rb') as file:
            # Use query.message for replying
            await query.message.reply_document(file, filename=main_csv_file)
    elif query.data == 'csv_list':
        await query.edit_message_text("Sending Trade List CSV please wait....")
        with open(CSV_FILE, 'rb') as file:
            # Use query.message for replying
            await query.message.reply_document(file, filename=CSV_FILE)
    elif query.data == 'check_limit':
        if Total_request >= 20000:
            await query.edit_message_text(f"NGROK limit of 20000 got exceeds.Please re-run the server.")
        else:
            await query.edit_message_text(f"Currently Limit Used is:-{Total_request}")



# Set up and run the Telegram bot
def start_bot():
    TOKEN = '8104386873:AAEWaF_YHG0Me8Jn185W7ssEuXwl34ZYli0'
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start",start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.run_polling()

# Flask routes
def calculate_risk_reward(entry_price, take_profit, stop_loss):
    try:
        # Risk = Entry Price - Stop Loss and Reward = Take Profit - Entry Price
        risk = abs(float(entry_price) - float(stop_loss))  # Risk calculation
        reward = abs(float(take_profit) - float(entry_price))  # Reward calculation
        
        return risk, reward  # Return both Risk and Reward
    except ValueError:
        return None, None

# Function to handle creating the CSV file with headers
def create_csv_with_headers():
    headers = [
        "Trade No", "Type", "Signal", "Date/Time", "Price USD", "Contracts", "Profit", "Profit %", 
        "Cum. Profit", "Cum. Profit %", "Run-up", "Run-up %", "Drawdown", "Drawdown %", 
        "Risk", "Reward", "Pair", "Timeframe", "Comment"
    ]
    df = pd.DataFrame(columns=headers)
    df.to_csv(CSV_FILE, index=False)

# Webhook route to process incoming JSON data
@app.route('/webhook', methods=['POST'])
def webhook():
    global Total_request
    Total_request += 1
    
    print(Total_request)
    
    json_data = request.get_json()  # Get JSON data from the webhook

    # Check if json_data is available and has the correct structure
    if json_data:
        # Extract the necessary data from the JSON payload
        trade_data = {
            "Type": json_data.get("Signal", ""),
            "Signal": json_data.get("Signal", ""),
            "Date/Time": json_data.get("Date/time", ""),
            "Price USD": json_data.get("Price USD", ""),
            "Contracts": json_data.get("Contracts", ""),
            "Profit": json_data.get("Profit", ""),
            "Profit %": json_data.get("Profit %", ""),
            "Run-up": json_data.get("Run-up", ""),
            "Run-up %": json_data.get("Run-up %", ""),
            "Drawdown": json_data.get("Drawdown", ""),
            "Drawdown %": json_data.get("Drawdown %", ""),
            "Risk": json_data.get("Risk", ""),
            "Reward": json_data.get("Reward", ""),
            "Pair": json_data.get("Pair", ""),  # Get Pair
            "Timeframe": json_data.get("Timeframe", ""),  # Get Timeframe
            "Comment": json_data.get("Comment", "")  # Get Comment
        }

        # Ensure the CSV file exists and is not empty
        if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
            create_csv_with_headers()

        # Read the existing data
        df = pd.read_csv(CSV_FILE)
        
        # Append the new trade data to the DataFrame using pd.concat
        trade_data["Trade No"] = len(df) + 1  # Increment trade number for each new trade
        new_trade_df = pd.DataFrame([trade_data])
        df = pd.concat([df, new_trade_df], ignore_index=True)
        
        # Ensure "Profit" and "Cum. Profit" are numeric
        df["Profit"] = pd.to_numeric(df["Profit"], errors='coerce')
        df["Cum. Profit"] = df["Profit"].cumsum()
        df["Cum. Profit %"] = df["Cum. Profit"] / df["Cum. Profit"].iloc[0] * 100  # Assuming the first entry is the initial investment
        
        # Save the updated DataFrame back to the CSV file
        df.to_csv(CSV_FILE, index=False)
        
        print("Received and saved data:", trade_data)
        return 'OK', 200
    else:
        return 'Bad Request', 400



# Flask web server in another thread
def start_flask():
    app.run(host='0.0.0.0', port=5000)  # Run Flask app on port 5000

if __name__ == '__main__':
    # Running Flask and the Telegram Bot concurrently using Threads
    flask_thread = Thread(target=start_flask)
    flask_thread.daemon = True  # Allow thread to exit when the main program exits
    flask_thread.start()
    generate_dashboard()
    start_bot()
    
