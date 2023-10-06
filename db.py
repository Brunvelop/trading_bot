import os
from supabase_py import create_client, Client
from dotenv import load_dotenv


class DB():
    def __init__(self):
        load_dotenv()
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

    def insert_order(self, timestamp, price, amount, cost, fees, closed):
        data = self.supabase.table('trades').insert([{
            'buy_timestamp': timestamp,
            'buy_price': price,
            'buy_amount': amount,
            'buy_cost': cost,
            'buy_fees': fees,
            'closed': closed
        }]).execute()
        return data

    def get_order_by_id(self, order_id):
        return self.supabase.table('trades').select().filter('order_id', 'eq', order_id).execute()

    def get_orders_below(self, price):
        return self.supabase.table('trades').select().filter('buy_price', 'lt', price).filter('closed', 'eq', 0).order('buy_price', ascending=False).execute()

    def get_all_orders(self):
        return self.supabase.table('trades').select().execute()

    def update_order(self, order_id, sell_timestamp, sell_price, sell_amount, sell_cost, sell_fees):
        self.supabase.table('trades').update({
            'closed': True,
            'sell_timestamp': sell_timestamp,
            'sell_price': sell_price,
            'sell_amount': sell_amount,
            'sell_cost': sell_cost,
            'sell_fees': sell_fees
        }).match({'order_id': order_id}).execute()
    
    def check_table(self):
        tables = self.supabase.rpc('pg_catalog', 'pg_tables')
        table_names = [table['tablename'] for table in tables['data']]
        if 'trades' not in table_names:
            print("Table 'trades' does not exist. Please create it via the Supabase web interface.")


if __name__ == '__main__':
    import datetime
    db = DB()
    a = db.insert_order(
        timestamp=datetime.datetime.fromtimestamp(1696436779).isoformat(),
        price=45000.00,
        amount=0.001,
        cost=45.00,
        fees=0.01,
        closed=False
    )
    a