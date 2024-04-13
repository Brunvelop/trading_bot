class Indicators:
    def calculate_std_dev_and_avg_range(self, data):
        bar_range = (data['High'] - data['Low']).abs() / data['Low'] * 100
        avg_range = bar_range.ewm(span=10).mean()
        std_dev = avg_range.rolling(window=200).std()
        return std_dev, avg_range
    
    def calculate_max_min(self, data, period=300):
        max_value = data['Close'][-(period+1):-2].max()
        min_value = data['Close'][-(period+1):-2].min()
        return max_value, min_value
