import sqlite3
from sqlite3 import Error

class DB():

    def __init__(self, db_name='db.db'):
        self.db_name = db_name
        self.create_table()

    def sql_connection(self):
        try:
            conexion = sqlite3.connect(self.db_name)
            return conexion
        except Error as e:
            print(f"Error establishing connection to database: {e}")

    def create_table(self):
        conexion = self.sql_connection()
        cursor = conexion.cursor()
        create_table_query = """
            CREATE TABLE IF NOT EXISTS trades (
                order_id TEXT, 
                buy_timestamp INT, 
                buy_price REAL, 
                buy_amount REAL, 
                buy_cost REAL, 
                buy_fees REAL,
                closed BOOL,
                sell_timestamp INT, 
                sell_price REAL, 
                sell_amount REAL, 
                sell_cost REAL,  
                sell_fees REAL
            );
        """
        cursor.execute(create_table_query)
        conexion.commit()
        print("Table 'trades' created successfully")
        cursor.close()
        conexion.close()

    def insert_order(self, order_id, timestamp, price, amount, cost, fees, closed):
        conexion = self.sql_connection()
        cursor = conexion.cursor()
        insert_query = """
            INSERT INTO trades (order_id, buy_timestamp, buy_price, buy_amount, buy_cost, buy_fees, closed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        values = (order_id, timestamp, price, amount, cost, fees, closed)
        cursor.execute(insert_query, values)
        conexion.commit()
        print("Data inserted successfully")
        cursor.close()
        conexion.close()

    def get_order_by_id(self, order_id):
        conexion = self.sql_connection()
        cursor = conexion.cursor()
        query = """
            SELECT * FROM trades WHERE order_id = ?
        """
        cursor.execute(query, (order_id,))
        orders = cursor.fetchall()
        cursor.close()
        conexion.close()
        return orders

    def get_orders_below(self, price):
        conexion = self.sql_connection()
        cursor = conexion.cursor()
        query = """
            SELECT * FROM trades WHERE buy_price < ? AND closed = 0 ORDER BY buy_price DESC
        """
        cursor.execute(query, (price,))
        orders = cursor.fetchall()
        cursor.close()
        conexion.close()
        return orders

    def get_all_orders(self):
        conexion = self.sql_connection()
        cursor = conexion.cursor()
        query = """
            SELECT * FROM trades
        """
        cursor.execute(query)
        orders = cursor.fetchall()
        cursor.close()
        conexion.close()
        return orders

    def update_order(self, order_id, sell_timestamp, sell_price, sell_amount, sell_cost, sell_fees):
        conexion = self.sql_connection()
        cursor = conexion.cursor()
        update_query = """
            UPDATE trades SET 
            closed = 1, 
            sell_timestamp = ?, 
            sell_price = ?, 
            sell_amount = ?, 
            sell_cost = ?, 
            sell_fees = ?
            WHERE order_id = ?
        """
        values = (sell_timestamp, sell_price, sell_amount, sell_cost, sell_fees, order_id)
        cursor.execute(update_query, values)
        conexion.commit()
        print(f"Order {order_id} updated successfully")
        cursor.close()
        conexion.close()