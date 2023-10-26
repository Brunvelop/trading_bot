import os
from dotenv import load_dotenv

from supabase import create_client, Client

# | Column Name | Data Type | Default Value | Primary Key |
# |-------------|-----------|---------------|-------------|
# | id          | int8      | NULL          | Yes         |
# | order_id    | text      | NULL          | No          |
# | timestamp   | timestamp | NULL          | No          |
# | pair        | text      | NULL          | No          |
# | type        | text      | NULL          | No          |
# | price       | numeric   | NULL          | No          |
# | amount      | numeric   | NULL          | No          |
# | cost        | numeric   | NULL          | No          |
# | executed    | bool      | NULL          | No          |
# | order_info  | jsonb     | {}            | No          |

class DB():
    def __init__(self, table_name='trades'):
        load_dotenv()
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        self.table_name = table_name

    def insert_order(self, order_id, timestamp, pair, type, price, amount, cost, executed, order_info):
        data = self.supabase.table(self.table_name).insert([{
            'order_id': order_id, 
            'timestamp': timestamp,
            'pair': pair,
            'type': type,
            'price': price,
            'amount': amount,
            'cost': cost,
            'executed': executed,
            'order_info': order_info
        }]).execute()
        return data
    
    def get_order_by_id(self, order_id):
        return self.supabase.table(self.table_name).select('*').filter('order_id', 'eq', order_id).execute()

    def get_orders_below(self, price):
        return self.supabase.table(self.table_name).select('*').filter('buy_price', 'lt', price).filter('closed', 'eq', False).order('buy_price', desc=True).execute()

    def get_all_orders(self):
        return self.supabase.table(self.table_name).select('*').execute().data

    def update_order(self, order_id, sell_timestamp, sell_price, sell_amount, sell_cost, sell_fees):
        self.supabase.table(self.table_name).update({
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
        if self.table_name not in table_names:
            print("Table does not exist. Please create it via the Supabase web interface.")

    def get_last_position(self):
        result = self.supabase.table(self.table_name).select('position').order('position', desc=True).neq('position', 0).limit(1).execute()
        if not result.data[0]['position']:
            return 0  # return 0 if the result is None or empty
        return result.data[0]['position']
    

    def update_null_positions(self, position_number):
        return self.supabase.table(self.table_name).update(
            {'position': position_number}
            ).is_('position', 'null').execute()

    def get_current_trades(self):
        return self.supabase.table(self.table_name).select('*').is_('position', 'null').filter(
            'closed', 'eq', False
        ).execute().data
    
    def get_open_trades_with_highest_position(self):
        highest_position = self.get_last_position()
        return self.supabase.table(self.table_name).select('*').filter(
            'position', 'eq', highest_position).filter(
            'closed', 'eq', False
        ).execute().data