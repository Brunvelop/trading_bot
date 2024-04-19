class Indicators:
    
    def calculate_max(self, data, period=300):
        max_value = data['Close'][-(period+1):-2].max()
        return max_value

    def calculate_min(self, data, period=300):
        min_value = data['Close'][-(period+1):-2].min()
        return min_value


    def calculate_std_dev_and_avg_range(self, data, window=200):
        volatility = self.calculate_volatility(data)
        avg_range = volatility.ewm(span=window).mean()
        std_dev = avg_range.rolling(window=window).std()
        return volatility, std_dev, avg_range


    def calculate_volatility(self, data):
        volatility = (data['High'] - data['Low']).abs() / data['Low'] * 100
        return volatility

    def calculate_avg_volatility(self, volatility, span):
        avg_volatility = volatility.ewm(span=span, adjust=False).mean()
        return avg_volatility
    

    def calculate_ma(self, data, window=200):
        average = data['Close'].rolling(window=window).mean()
        return average