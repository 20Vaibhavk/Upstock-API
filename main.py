import pymysql
import requests
import websocket
import json

# MySQL Connection Configuration
mysql_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '@20helltocollege',
    'database': 'broker_db'
}

# Connect to MySQL
mysql_connection = pymysql.connect(**mysql_config)
mysql_cursor = mysql_connection.cursor()

# Upstox API Config
upstox_api_key = 'your_upstox_api_key'
upstox_access_token = 'actual_access_token_value_here'  # Replace with your actual access token

# Upstox API URLs
upstox_base_url = 'https://api.upstox.com/live/'

def fetch_holdings():
    holdings_url = f"{upstox_base_url}holdings"
    headers = {'x-api-key': upstox_api_key, 'Authorization': f'token {upstox_access_token}'}
    response = requests.get(holdings_url, headers=headers)
    if response.status_code == 200:
        holdings_data = response.json()
        return holdings_data
    else:
        print("Failed to fetch holdings:", response.text)
        return None

def place_order(symbol, quantity, price, transaction_type):
    order_url = f"{upstox_base_url}order"
    headers = {'x-api-key': upstox_api_key, 'Authorization': f'token {upstox_access_token}'}
    data = {
        "symbol": symbol,
        "quantity": quantity,
        "price": price,
        "transaction_type": transaction_type  # 'BUY' or 'SELL'
    }
    response = requests.post(order_url, headers=headers, json=data)
    if response.status_code == 200:
        order_response = response.json()
        return order_response
    else:
        print(f"Failed to place {transaction_type} order:", response.text)
        return None

def subscribe_to_websocket():
    websocket_url = f"wss://api.upstox.com/ws/feeds/{upstox_access_token}"
    ws = websocket.WebSocketApp(websocket_url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()

def save_holdings_to_db(holdings):
    for holding in holdings:
        symbol = holding['symbol']
        quantity = holding['quantity']
        mysql_cursor.execute("INSERT INTO holdings (symbol, quantity) VALUES (%s, %s) ON DUPLICATE KEY UPDATE quantity = VALUES(quantity)",
                   (symbol, quantity))
    mysql_connection.commit()

def save_order_to_db(order):
    symbol = order['symbol']
    quantity = order['quantity']
    price = order['price']
    transaction_type = order['transaction_type']
    mysql_cursor.execute("INSERT INTO orders (symbol, quantity, price, transaction_type) VALUES (%s, %s, %s, %s)",
               (symbol, quantity, price, transaction_type))
    mysql_connection.commit()

def handle_postback(postback_data):
    postback_type = postback_data['type']
    if postback_type == 'order_update':
        order_status = postback_data['order_status']
        if order_status == 'complete':
            order = postback_data['order']
            save_order_to_db(order)

def on_message(ws, message):
    data = json.loads(message)
    message_type = data['type']
    if message_type == 'postback':
        handle_postback(data['data'])

def on_error(ws, error):
    print("WebSocket Error:", error)

def on_close(ws):
    print("WebSocket Closed")

def on_open(ws):
    print("WebSocket Opened")

def main():
    holdings = fetch_holdings()
    if holdings:
        save_holdings_to_db(holdings)
    else:
        print("Failed to fetch holdings.")

    subscribe_to_websocket()

if __name__ == "__main__":
    main()
