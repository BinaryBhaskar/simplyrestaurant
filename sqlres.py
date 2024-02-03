### FLAVOURSYNC, A Restaurant Management Software

#IMPORTS
import mysql.connector as do
import sys
from prettytable import PrettyTable
import random
import string
from datetime import datetime as dt

#CONSTANTS
PASSKEY  = 'SPS'
INDIA_TIMEZONE = 'Asia/Kolkata'

#FUNCTIONS
def admin_access():
    super_access = len(sys.argv) > 1 and sys.argv[1] == PASSKEY
    return super_access or input("Enter your Passkey: ") == PASSKEY

def create_connection(command = None, table = None):
    global connection
    connection = do.connect(host = 'localhost', user = 'root', passwd='SPSProzekt')

    if connection.is_connected():
        cursor = connection.cursor()
        cursor.execute('CREATE DATABASE IF NOT EXISTS res_db')
        cursor.execute('USE res_db')
        cursor.execute('CREATE TABLE IF NOT EXISTS menu(item_id INT PRIMARY KEY AUTO_INCREMENT, item_name VARCHAR(50) NOT NULL, item_category VARCHAR(50) NOT NULL, item_code VARCHAR(50) UNIQUE NOT NULL, item_price FLOAT NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS deliveries(order_id VARCHAR(50) PRIMARY KEY, ordered_by VARCHAR(50) NOT NULL, total_price FLOAT, order_details TEXT)')

    if command:
        run_command(cursor, command)
    connection.close()

def run_command(cursor, command):
    if command == "m":
        print_menu(cursor, False)
    elif command == "a":
        accounting(cursor)
    elif command == "o":
        print_menu(cursor, True)
    elif command == "t":
        tracking(cursor)

def print_menu(cursor, for_order):
    cursor.execute('SELECT item_name, item_code, item_category, item_price FROM menu ORDER BY item_category')
    result = cursor.fetchall()
    line()
    if not result:
        print("No Menu Found.")
    if result:
        table = PrettyTable()
        table.field_names = ["Name", "Code", "Category", "Price"]
        for row in result:
            table.add_row(row)
        print(table)
    line()

    if not for_order:
        menu_options(cursor)
    elif for_order and result:
        start_order(cursor)
    else:
        home(True)

def menu_options(cursor):
    option = input("Press 'a' to add new item, 'u' to update existing item, 'd' to delete an item, or anything to return to home: ")
    if option in ['a', 'd', 'u']:
        is_admin = admin_access()
        if is_admin:
            if option == 'a':
                modify_menu_item(cursor, 'add')
            elif option == 'u':
                modify_menu_item(cursor, 'update')
            elif option == 'd':
                modify_menu_item(cursor, 'delete')
        else:
            print("You don't have access.")
            home()
    else:
        home()

def modify_menu_item(cursor, mode):
    cursor.execute('SELECT item_name, item_code FROM menu')
    result = cursor.fetchall()
    names_list = [item[0] for item in result]
    codes_list = [item[1] for item in result]

    if mode == 'update' or mode == 'delete':
        while True:
            existing_code = input("Enter the code of the existing item: ").upper()
            if existing_code in codes_list:
                x = codes_list.index(existing_code)
                codes_list.pop(x)
                names_list.pop(x)
                break
            else:
                print("Enter a valid code")
                home()

    if mode == 'delete':
        command = "DELETE FROM `res_db`.`menu` WHERE (`item_code` = '{}');".format(existing_code)
        cursor.execute(command)
        connection.commit()
        line()
        print("Database changed successfully")
        home()

    while True:
        name = input("Enter the name of the menu item: ").title()
        if name not in names_list:
            break
        print("Item already exists.")

    while True:
        try:
            price = float(input("Enter the price of the menu item: "))
            break
        except ValueError:
            print("Please enter a floating value.")

    categories = ["veg", "non-veg", "sweets", "drinks"]
    category = input(f"Enter the category of the  menu item ({'/'.join(categories)}): ").lower()
    while category not in categories:
        print("Invalid category. Please choose from the provided options.")
        category = input(f"Enter the category of the menu item ({'/'.join(categories)}): ").lower()

    while True:
        code = input("Enter the code of the item: ").upper()
        if code not in codes_list:
            break
        print("Code already exists.")

    if mode == 'add':
        command = "INSERT INTO `res_db`.`menu` (`item_name`, `item_category`, `item_code`, `item_price`) VALUES ('{}', '{}', '{}', '{}');".format(name, category, code, price)
    elif mode == 'update':
        command = "UPDATE `res_db`.`menu` SET `item_name` = '{}', `item_category` = '{}', `item_code` = '{}', `item_price` = '{}' WHERE (`item_code` = '{}');".format(name, category, code, price, existing_code)
    cursor.execute(command)
    connection.commit()
    line()
    print("Database changed successfully")
    home(True)

def start_order(cursor):
    order_list = []
    cursor.execute("SELECT item_code, item_name, item_price FROM menu")
    result = cursor.fetchall()
    codes_list = [item[0] for item in result]
    price_list = [item[2] for item in result]
    while True:
        add_item = input("Enter code of dish to buy (Write 'done' to proceed): ").upper()
        if add_item.lower() == 'done':
            break

        if add_item in codes_list:
            order_list.append(add_item)
            print(f"Added {add_item} to list.")
            print(f"Current List: {order_list}")
            line()

    total_price = 0.0
    for item in order_list:
        total_price += float(price_list[codes_list.index(item)])
    print("Currently Ordered Items: {}".format(order_list))
    print(f'Total Price: {total_price}')
    line()
    cancel_continue = input("Enter 'cancel' to Cancel or 'pay' to Continue to Payment: ").strip().lower()
    if cancel_continue == 'cancel':
        home()
    else:
        line()
        name = input("Enter your name here: ").strip().title()
        address = input("Enter your full address here: ").strip()
        order_details = [order_list, address, dt.now().strftime('%d/%m/%Y, %A, %H:%M')]

    bill_id = gen_pay_id(cursor)
    new_delivery_order = {
        "name": name,
        "order_id": bill_id,
        "price": total_price,
        "order_details": order_details
    }

    line()
    print("New delivery order has been added to 'deliveries'.")
    print(f"Please kindly pay your bill during delivery.\n  Rs.{total_price}\n  Bill ID: {bill_id}")

    command = '''INSERT INTO `res_db`.`deliveries` (`order_id`, `ordered_by`, `total_price`, `order_details`) VALUES ("{}", "{}", "{}", "{}");'''.format(str(bill_id), name, str(total_price), str(order_details))

    cursor.execute(command)
    connection.commit()
    line()
    home(True)

def gen_pay_id(cursor):
    alphabetical_caps = list(string.ascii_uppercase)
    numerical_digits = [str(i) for i in range(10)]
    while True:
        bill_id = f"{random.choice(alphabetical_caps)}{random.choice(alphabetical_caps)}{random.choice(numerical_digits)}{random.choice(numerical_digits)}_{dt.now().strftime('%d-%m')}"
        command = "SELECT order_id FROM deliveries WHERE order_id = '{}'".format(bill_id)
        cursor.execute(command)
        cursor.fetchall()
        if not cursor.fetchall():
            return bill_id

def home(prompt = False):
    if prompt:
        input("Enter to return to home.")
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
        if chosen_menu == 'exit':
            line()
            print("Exited Program Smoothly")
            line()
            sys.exit()
        else:
            create_connection(chosen_menu)
    else:
        line()
        print("Please Enter a valid input")
        home()

def accounting(cursor):
    line()
    is_admin = admin_access()
    line()
    if is_admin:
        cursor.execute('SELECT total_price FROM deliveries')
        result = cursor.fetchall()
        sales = [price_tupple[0] for price_tupple in result]
        total_deliveries = len(sales)
        total_payment = sum(sales)
        estimated_expenses = total_payment * 62 / 100
        estimated_profit = total_payment * 38 / 100
        
        print(f"Accounting:\n\nTotal Deliveries: {total_deliveries}\nTotal Payment: Rs.{total_payment}\nEstimated Expenses: Rs.{estimated_expenses}\nEstimated Profit (without GST): Rs.{estimated_profit}")
        line()
    
    else:
        print("You need admin access")
    home(True)

def tracking(cursor):
    order_id = input("Enter your Order ID here: ")
    command = 'SELECT * FROM deliveries WHERE order_id = "{}"'.format(order_id)
    cursor.execute(command)
    result = cursor.fetchall()
    if result:
        result = result[0]
        id, name, price, more = result[0], result[1], result[2], result[3]
        print(f"Order Info: \n    Order ID: {id}\n    Ordered by: {name}\n    Total Price: {price}    \n    More Info: {more}")
    else:
        print("No data found")
    line()
    home(True)

def line():
    print('‿⁔'*60)

def main():
    line()
    print("Welcome to FlavourSync, a restaurant management software.")
    home()

#RUNNING THE PROGRAM
if __name__ == "__main__":
    try:
        main()
    except do.Error as error:
        print("SQL Error: ", error)