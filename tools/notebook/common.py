# -*- coding: utf-8 -*-

################################################################################

import pandas as pd
import os
import matplotlib.dates as dates
import datetime
import moving

################################################################################


## Load stock prices history from CSV file to DataFame
#
# @param[in] file_path  -- path to CSV file. Example: "/history/ADBE.csv"
def load_history_dataframe(file_path):
	try:
		fname = os.path.basename(file_path)
		if not fname.lower().endswith('.csv'):
			print('Invalid file extension "%s", ".csv" expected' % file_path)
			return pd.DataFrame()
		df = pd.read_csv(file_path, index_col=0)
		df.index = pd.to_datetime(df['date'])
		del df['date']
		df['datenum'] = dates.date2num(df.index)
		return df.sort_index()
	except Exception as exc:
		print('Failed to load file "%s": %r' % (file_path, exc))
		return pd.DataFrame()


## Load stock prices history from all CSV files in target directory to DataFrames
#
# @param[in] file_path  -- path to CSV file. Example: "/history"
def load_history(history_dir):
	history_files = sorted([os.path.join(history_dir, f) for f in os.listdir(history_dir) if os.path.isfile(os.path.join(history_dir, f)) and f.lower().endswith('.csv')])
	print('%i files with prices hoistory found' % len(history_files))
	histories = [*filter(lambda h : len(h), [load_history_dataframe(path) for path in history_files])]
	print('%i files with prices hoistory loaded' % len(history_files))
	print('%i items totaly since %s to %s' % (sum([len(h) for h in histories]), min([h.index.min() for h in histories]), max([h.index.max() for h in histories])))
	history = []
	for h in histories:
		symbol = h['symbol'][0]
		del h['symbol']
		history.append((symbol, h))
	
	# history = pd.concat(histories)
	return dict(history)


#-------------------------------------------------------------------------------


## Returns symbol histories started after specified border date
#
# @param[in] history -- dictionary Symbol -> Price History DataFrame. See function load_history(history_dir)
# @param[in] date    -- border date. Default: 2016.01.01
def younger_than(history, date = datetime.datetime(2016,1,1)):
	return dict(filter(lambda item: item[1].index.min() > date, history.items()))


## Returns symbol histories started before specified border date
#
# @param[in] history -- dictionary Symbol -> Price History DataFrame. See function load_history(history_dir)
# @param[in] date    -- border date. Default: 2016.01.01
def older_than(history, date = datetime.datetime(2016,1,1)):
	return dict(filter(lambda item: item[1].index.min() <= date, history.items()))


#-------------------------------------------------------------------------------


## Returns list of price ratio values for specified prices history.
# Price ratio value for current date is a ratio of current close price to 
# first open price in symbol history.
#
# @param[in] h -- prices history DataFrame. See function load_history_dataframe(file_path)
def values__price_ratio(h):
	return h['close'] / h['open'].iloc[0]

## Append 'price-ratio' column to all symbols history. 
# See function values__price_ratio.
#
# @param[in,out] history -- dictionary Symbol -> Price History DataFrame. See function load_history(history_dir)
def append_price_ratio_column(history):
    for (symbol, h) in history.items():
        h['price-ratio'] = values__price_ratio(h)


## Returns list of max price ratio values for specified prices history.
# Max price ratio value for current date is a maximum price ratio since 
# begin of symbol history to current date inclusivle.
#
# @param[in] h -- prices history DataFrame. See function load_history_dataframe(file_path)
def values__max_prev(h):
	mp = []
	for price_ration in h['price-ratio']:
		if mp:
			mp.append(max(price_ration, mp[-1]))
		else:
			mp.append(price_ration)
	return mp

## Append 'max-prev' column to all symbols history. 
# See function values__max_prev.
#
# @param[in,out] history -- dictionary Symbol -> Price History DataFrame. See function load_history(history_dir)
def append_max_prev_column(history):
    for (symbol, h) in history.items():
        h['max-prev'] = values__max_prev(h)

## Returns list of price ratio values for specified prices history.
# Price drop value for current date is ratio of current price ratio 
# to current max price ratio. It shows depth of price fall since 
# last price maximum. If price grow then price drop is 1.
#
# @param[in] h -- prices history DataFrame. See function load_history_dataframe(file_path)
def values__price_drop(h):
	return h['price-ratio'] / h['max-prev']

## Append 'price-drop' column to all symbols history. 
# See function values__price_drop.
#
# @param[in,out] history -- dictionary Symbol -> Price History DataFrame. See function load_history(history_dir)
def append_price_drop_column(history):
    for (symbol, h) in history.items():
        h['price-drop'] = values__price_drop(h)


## Returns list of price drop period values for specified prices history.
# Price drop period  for current date is number of days passed since 
# last price maximum.
#
# @param[in] h -- prices history DataFrame. See function load_history_dataframe(file_path)
def values__price_drop_period(h):
	last_max_price_date = h.index[0]
	price_dorp = h['price-drop']
	pdp = [0]
	for date_n in range(1, len(h)):
		date = h.index[date_n]
		if price_dorp[date_n] == 1.:
			last_max_price_date = date
		pdp.append((date - last_max_price_date).days)
	return pdp

## Append 'drop-period' column to all symbols history. 
# See function values__price_drop_period.
#
# @param[in,out] history -- dictionary Symbol -> Price History DataFrame. See function load_history(history_dir)
def append_drop_period_column(history):
	for (symbol, h) in history.items():
		h['drop-period'] = values__price_drop_period(h)


## Returns list of average price growth ratio values for specified prices history.
# Average price growth ratio value for current date is ratio of current 
# close price to open price at begin of time window averaged for specified period.
#
# @param[in] h         -- prices history DataFrame. See function load_history_dataframe(file_path)
# @param[in] window_size -- time window size in days. Defautl: 365
# @param[in] avg_period  -- averaging period in days. Defautl: 365
def values__price_growth_ratio(h, window_size = 365, avg_period = 365):
	avg_growth_ratio__closure = lambda history, begin, end, closed, avg_period = avg_period: \
		moving.avg_growth_ratio(history, begin, end, closed, avg_period)
	return moving.moving_f(avg_growth_ratio__closure, h, window_size = window_size)

## Append 'price-growth-[YEARS]y' column to all symbols history. 
# See function values__price_growth_ratio.
#
# @param[in,out] history -- dictionary Symbol -> Price History DataFrame. See function load_history(history_dir)
# @param[in] windows     -- list windows sizes in years. Default: [1,2,3,4,5]
def append_price_grouth_column(history, windows = range(1,6)):
	for (symbol, h) in history.items():
		for years in windows:			
			h['price-growth-%iy'%years] = values__price_growth_ratio(h, window_size = 365 * years, avg_period = 365)


#-------------------------------------------------------------------------------


## Returns copy of prices history for specified relative period
#
# @param[in] history -- dictionary Symbol -> Price History DataFrame. See function load_history(history_dir)
# @param[in] since   -- begin of period - float between 0.0 and 1.0. Default: 0.0
# @param[in] to      -- end of period - float between 0.0 and 1.0. Default: 1.0
def prepare_history_period(history, since = 0.,  to = 1.):
	res = {}
	for (symbol, h) in history.items():
		begin_n = int(len(h) * since)
		end_n = int(len(h) * to)
		begin = h.index[begin_n]
		end = h.index[end_n - 1]
		res[symbol] = h.loc[begin:end].copy()
	return res

## Returns copy of prices history for specified absolute period
#
# @param[in] history -- dictionary Symbol -> Price History DataFrame. See function load_history(history_dir)
# @param[in] since   -- begin of period - pandas.datetime
# @param[in] to      -- end of period - pandas.datetime
def prepare_history_abs_period(history, since,  to):
	res = {}
	for (symbol, h) in history.items():
		hp = h.loc[since:to].copy()
		if (hp.index[0] - since).days <= 31:
			res[symbol] = hp
	return res
	
################################################################################
