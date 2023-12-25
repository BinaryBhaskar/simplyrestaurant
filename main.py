import sys
import json
import random
import string
from datetime import datetime as dt
from tabulate import tabulate

#CONSTANTS
INDIA_TIMEZONE = 'Asia/Kolkata'
PASSKEY = 'ProzektSPS'

#FILES
with open("res_menu.json", encoding='utf-8') as menu_file, open('orders_log.json', 'r', encoding='utf-8') as order_file:
    menu_data = json.load(menu_file)
    order_data = json.load(order_file)

#FUNCTIONS
def check_weekend():
    today = dt.now().weekday()
    return today >= 5

def admin_access():
    super_access = len(sys.argv) > 1 and sys.argv[1] == PASSKEY
    return super_access or input("Enter your Passkey: ") == PASSKEY

def add_menu_item(menu_data):
    names_list = {item['name'] for item in menu_data["menu"]}
    codes_list = {item['code'] for item in menu_data["menu"]}

    while True:
        name = input("Enter the name of the new menu item: ").title()
        if name not in names_list:
            break
        print("Item already exists.")

    while True:
        try:
            price = float(input("Enter the new price of the menu item: "))
            break
        except ValueError:
            print("Please enter a floating value.")

    categories = ["veg", "non-veg", "sweets", "drinks"]
    category = input(f"Enter the category of the new menu item ({'/'.join(categories)}): ").lower()
    while category not in categories:
        print("Invalid category. Please choose from the provided options.")
        category = input(f"Enter the category of the new menu item ({'/'.join(categories)}): ").lower()

    while True:
        code = input("Enter the code of the new item: ").upper()
        if code not in codes_list:
            break
        print("Code already exists.")

    special = input("Is this a special item for weekends? (y/n): ").lower() == 'y'

    new_item = {
        "name": name,
        "price": price,
        "category": category,
        "code": code,
        "special": special
    }

    menu_data["menu"].append(new_item)

    with open('res_menu.json', 'w', encoding='utf-8') as menu_file:
        json.dump(menu_data, menu_file, indent=4)

def line():
    print("_"*110)

def filter_special_items(menu_data, for_order):
    filtered_items = []

    for item in menu_data["menu"]:
        if item["special"] and (check_weekend() or not for_order):
            filtered_items.append([item["name"], item["price"], item["code"]])
        elif not item["special"]:
            filtered_items.append([item["name"], item["price"], item["code"]])

    return filtered_items

def display_menu_table(categorized_menu):
    table_data = []

    for category, items in categorized_menu.items():
        if items:
            table_data.append([f"{category.capitalize()} Category", ""])
            table_data.extend(items)
            table_data.append([])

    table = tabulate(table_data, headers=["Item", "Price", "Code"], tablefmt="grid")
    print(table)
    print("=" * 70)

def print_categorized_menu(menu_data, for_order=False):
    categorized_menu = {"veg": [], "non-veg": [], "sweets": [], "drinks": []}
    
    for item in menu_data["menu"]:
        if item["category"] in categorized_menu:
            categorized_menu[item["category"]].append([item["name"], item["price"], item["code"]])

    display_menu_table(categorized_menu)

    if for_order:
        start_order(menu_data)
    else:
        handle_admin_options(menu_data)



def handle_admin_options(menu_data):
    option = input("Press 'a' to add new item, 'u' to update existing item, 'd' to delete an item, or anything to return to home: ")
    if option in ['a', 'd', 'u']:
        is_admin = admin_access()
        if is_admin:
            if option == 'a':
                add_menu_item(menu_data)
            elif option == 'u':
                update_menu_item(menu_data)
            elif option == 'd':
                delete_menu_item(menu_data)
        else:
            print("You don't have access.")
    else:
        home()

def update_menu_item(menu_data):
    code = input("Enter the code of the item to update: ").upper()
    item = next((item for item in menu_data["menu"] if item["code"] == code), None)

    if item:
        menu_data["menu"].remove(item)
        add_menu_item(menu_data)
    else:
        print("Item not found.")

def delete_menu_item(menu_data):
    code = input("Enter the code of the item to delete: ").upper()
    item = next((item for item in menu_data["menu"] if item["code"] == code), None)

    if item:
        menu_data["menu"].remove(item)
        with open('res_menu.json', 'w', encoding='utf-8') as menu_file:
            json.dump(menu_data, menu_file, indent=4)
        print("Item deleted successfully.")
    else:
        print("Item not found.")

def start_order(menu_data):
    order_list = []
    
    while True:
        add_item = input("Enter code of dish to buy (Write 'done' to proceed): ").lower()
        
        if add_item == 'done':
            break
        
        buy_item = next((item for item in menu_data['menu'] if item['code'].lower() == add_item), None)
        
        if buy_item:
            order_list.append(buy_item)
            current_order = [item['name'] for item in order_list]
            print(f"Added {buy_item['name']} to list.")
            print(f"Current List: {current_order}")
            line()
        else:
            print("Item not found. Please enter a valid code.")

    order_info(order_list)

def order_info(ordered_list):
    line()
    print("Current Order:")
    total_price = sum(item['price'] for item in ordered_list)
    
    for item in ordered_list:
        print(f"  {item['name']} : {item['price']}")
    
    print(f'Total Price: {total_price}')
    line()
    cancel_continue = input("Enter 'cancel' to Cancel or 'pay' to Continue to Payment: ").strip().lower()
    if cancel_continue == 'cancel':
        home()
    else:
        line()
        name = input("Enter your name here: ").strip().title()
        address = input("Enter your full address here: ").strip()
        payment_prompt = gen_pay_id(total_price, ordered_list, address, name)
        print(payment_prompt)
        line()
        input("Press Enter to return to home. ")
        home()

def gen_pay_id(total_price, order_details, address, name):
    alphabetical_caps = list(string.ascii_uppercase)
    numerical_digits = [str(i) for i in range(10)]
    all_orders = [order['order_id'] for order in order_data['deliveries']]
    
    while True:
        bill_id = f"{random.choice(alphabetical_caps)}{random.choice(alphabetical_caps)}{random.choice(numerical_digits)}{random.choice(numerical_digits)}_{dt.now().strftime('%d-%m')}"
        
        if bill_id not in all_orders:
            break

    new_delivery_order = {
        "name": name,
        "order_id": bill_id,
        "price": total_price,
        "order_details": order_details,
        "address": address,
        "time_of_order": dt.now().strftime('%d/%m/%Y, %A, %H:%M')
    }

    order_data["deliveries"].append(new_delivery_order)
    
    with open('orders_log.json', 'w', encoding='utf-8') as order_file:
        json.dump(order_data, order_file, indent=2)

    print("New delivery order has been added to 'deliveries'.")
    return f"Please kindly pay your bill during delivery.\n  Rs.{total_price}\n  Bill ID: {bill_id}"

def home():
    line()
    options = {
        'o': "Order Food",
        't': "Track Orders",
        'm': "Show Menu",
        'a': "Accounting",
        'exit': "Exit Program"
    }
    
    chosen_menu = input(f"Enter what you want to see:\n    {'\n    '.join(f'{key}: {value}' for key, value in options.items())}\n"+"> ").lower()
    
    if chosen_menu in options:
        if chosen_menu == 'm':
            print_categorized_menu(menu_data, False)
            home()
        elif chosen_menu == 'o':
            print_categorized_menu(menu_data, True)
        elif chosen_menu == 't':
            tracking()
        elif chosen_menu == 'a':
            accounting()
        elif chosen_menu == 'exit':
            sys.exit()
    else:
        home()

def accounting():
    line()
    is_admin = admin_access()
    line()
    
    if is_admin:
        sales = [order['price'] for order in order_data['deliveries']]
        total_deliveries = len(sales)
        total_payment = sum(sales)
        estimated_expenses = total_payment * 62 / 100
        estimated_profit = total_payment * 38 / 100
        
        print(f"Accounting:\n\nTotal Deliveries: {total_deliveries}\nTotal Payment: Rs.{total_payment}\nEstimated Expenses: Rs.{estimated_expenses}\nEstimated Profit (without GST): Rs.{estimated_profit}")
        line()
    
    else:
        print("You need admin access")

    input("Enter to go to home.")
    home()

def tracking():
    line()
    all_orders = [order['order_id'] for order in order_data['deliveries']]
    get_id = input(f"Enter your Order ID here (Enter 'last' to see last made order or 'recent' to see last 10 orders): ").strip()
    
    if get_id.lower() in ['last', 'recent']:
        is_admin = admin_access()
        
        if is_admin:
            if get_id == 'last':
                while all_orders:
                    item_id = all_orders.pop()
                    print_order_info(item_id)
                    
                    cont = input("Enter anything to see previous order or 'exit' to exit: ").strip().lower()
                    if cont == 'exit':
                        break
            elif get_id == 'recent':
                while len(all_orders) > 10:
                    for item_id in all_orders[-10:]:
                        print_order_info(item_id)
                    
                    cont = input("Enter anything to see previous 10 orders or 'exit' to exit: ").strip().lower()
                    if cont == 'exit':
                        break
                    else:
                        all_orders = all_orders[:-10]
        else:
            print("You need admin access")
    else:
        print_order_info(get_id)

    input("Enter to go to home.")
    home()

def print_order_info(order_id_input):
    order = next((order for order in order_data["deliveries"] if str(order["order_id"]) == str(order_id_input)), None)

    if order:
        ordered_by = order['name']
        order_value = order['price']
        ordered_items = [item['name'] for item in order['order_details']]
        order_time = order['time_of_order']
        order_address = order['address']

        line()
        print(f"Order ID: {order_id_input}\nOrdered By: {ordered_by}\nTotal price: {order_value}\nTime of Order: {order_time}\nOrdered Items:{ordered_items}\nAddress: {order_address}")
        line()
    else:
        line()
        print("Order not found.")
        line()

if __name__ == "__main__":
    home()
