#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import datetime
import keys

#===============================================================================

ALPHA_VANTAGE_APIKEY = keys.ALPHA_VANTAGE_APIKEY

#===============================================================================

def ok(response):
	return not (__http_status_error(response) or __response_error(response))

def __http_status_error(response):
	return type('') == type(response) and response.startswith('Status code:')

def __response_error(response):
	return type(()) == type(response) and response[0] == 'error'

def parse_time_series(time_series):
	return dict(map(lambda items: (__parse_date(items[0]), __parse_time_series_entry(items[1])), time_series.items()))

def parse_daily_time_series(time_series):
	return dict(map(lambda items: (__parse_datetime(items[0]), __parse_time_series_entry(items[1])), time_series.items()))

def __parse_date(date):
	[year, month, day] = map(int, date.split('-'))
	return datetime.date(year, month, day)

def __parse_datetime(date):
	[date, time] = date.split()
	[year, month, day] = map(int, date.split('-'))
	[hour, minute, second] = map(int, time.split(':'))
	return datetime.datetime(year, month, day, hour, minute, second)

def __parse_time_series_entry(entry):
	if '5. adjusted close' in entry:
		ts_entry = TSEntry({'open': eval(entry['1. open'])
			, 'high': eval(entry['2. high'])
			, 'low': eval(entry['3. low'])
			, 'close': eval(entry['4. close'])
			, 'volume': eval(entry['6. volume'])})
		k = eval(entry['5. adjusted close']) / ts_entry.close
		if k > 0.9 and ts_entry.open / ts_entry.close >= 2.0:
			ts_entry.open = ts_entry.close
			ts_entry.high = ts_entry.close
		else:
			ts_entry.adjust(k)
		return ts_entry
	else:
		return TSEntry({'open': eval(entry['1. open'])
			, 'high': eval(entry['2. high'])
			, 'low': eval(entry['3. low'])
			, 'close': eval(entry['4. close'])
			, 'volume': eval(entry['5. volume'])})

#===============================================================================

class TSEntry:
	open = None
	high = None
	low = None
	close = None
	volume = None

	def __init__(self, entry):
		self.open = entry['open']
		self.high = entry['high']
		self.low = entry['low']
		self.close = entry['close']
		self.volume = entry['volume']

	def __repr__(self):
		return 'stock.TSEntry(%s)' % str({'open': self.open, 'high': self.high, 'low': self.low, 'close': self.close, 'volume': self.volume})
	def __str__(self):
		return self.__repr__()

	def adjust(self, k):
		self.open *= k
		self.high *= k
		self.low *= k
		self.close *= k

#===============================================================================

class AlphaVantage:

	__apikey = None

	def __init__(self, apikey = ALPHA_VANTAGE_APIKEY):
		self.__apikey = apikey

	def intraday(self, symbol = 'MSFT', interval = '1min', outputsize = 'compact', datatype = 'json'):
		r = requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=%s&apikey=%s&datatype=%s&outputsize=%s&interval=%s' %(symbol, self.__apikey, datatype, outputsize, interval))
		if r.status_code != 200:
			return 'Status code: %i' % r.status_code
		data = r.json()
		if 'Error Message' in data: 
			return data
		try:
			return parse_daily_time_series(data['Time Series (%s)' % (interval,)])
		except Exception as exc:
			return ('error', exc, data)		

	def daily(self, symbol = 'MSFT', outputsize = 'full', datatype = 'json'):
		return self.__request('TIME_SERIES_DAILY', 'Time Series (Daily)', symbol, datatype)

	def daily_adjusted(self, symbol = 'MSFT', outputsize = 'full', datatype = 'json'):
		return self.__request('TIME_SERIES_DAILY_ADJUSTED', 'Time Series (Daily)', symbol, datatype)
    
	def weekly(self, symbol = 'MSFT', datatype = 'json'):
		return self.__request('TIME_SERIES_WEEKLY', 'Weekly Time Series', symbol, datatype)

	def weekly_adjusted(self, symbol = 'MSFT', datatype = 'json'):
		return self.__request('TIME_SERIES_WEEKLY_ADJUSTED', 'Weekly Adjusted Time Series', symbol, datatype)

	def monthly(self, symbol = 'MSFT', datatype = 'json'):
		return self.__request('TIME_SERIES_MONTHLY', 'Monthly Time Series', symbol, datatype)

	def monthly_adjusted(self, symbol = 'MSFT', datatype = 'json'):
		return self.__request('TIME_SERIES_MONTHLY_ADJUSTED', 'Monthly Adjusted Time Series', symbol, datatype)
		
	def __request(self, function, response_key, symbol, datatype):
		r = requests.get('https://www.alphavantage.co/query?function=' + function + '&symbol=%s&apikey=%s&datatype=%s' %(symbol, self.__apikey, datatype))
		if r.status_code != 200:
			return 'Status code: %i' % r.status_code
		data = r.json()
		if 'Error Message' in data: 
			return data		
		try:
			return parse_time_series(data[response_key])
		except Exception as exc:
			return ('error', exc, data)


#===============================================================================

def year_delta(series):
	return period_delta(series, datetime.timedelta(365))

def period_delta(series, period):
	timeline = sorted(series.items(), reverse = True)
	last = timeline[0]
	deltas = []
	for (date, entry) in timeline:
		if last[0] - date >= period:
			deltas.append( (date, last[0], last[1].close / entry.open) )
			last = (date, entry)
	return deltas


def years_are_positive(series, limit = datetime.timedelta(365*5)):
	year = datetime.timedelta(365)
	timeline = sorted(series.items(), reverse = True)
	for (date, entry) in timeline:
		year_before = date - year
		if year_before + limit < timeline[0][0]: continue
		if year_before in series and entry.close < series[year_before].open:
			return (date, entry.close, year_before, series[year_before].open)
	return True

#===============================================================================

class Open:
	name = None
	symbol = None
	date = None
	volume = 0
	origin = None
	currency = None

	def loads(s, dollar = 61.5):
		parts = s.split()
		name = parts[0]
		symbol = parts[1]
		date = list(map(int, parts[2].split('.')))
		currency = ''.join(list(filter(lambda c: c not in '0123456789+-.', parts[3])))
		volume = float(eval(''.join(list(filter(lambda c: c in '0123456789+-.', parts[3]))))) * (1./dollar if currency != '$' else 1.)
		return Open({'name': name
			, 'symbol': symbol
			, 'date': datetime.date(date[0], date[1], date[2])
			, 'volume': volume
			, 'currency': currency})

	def __init__(self, entry):
		self.name = entry['name']
		self.symbol = entry['symbol']
		self.date = entry['date']
		self.volume = entry['volume']

	def __repr__(self):
		return 'stock.Open(%s)' % str({'name': self.name
			, 'symbol': self.symbol
			, 'date': self.date
			, 'volume': self.volume})

	def __str__(self):
		return '%s        %s        %s        %.2f$' % (self.name, self.symbol, self.date.strftime('%Y.%m.%d'), self.volume)


#===============================================================================

def main():
	print("it is a module")

#===============================================================================

if __name__ == "__main__":
	main()
