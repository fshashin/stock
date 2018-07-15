# -*- coding: utf-8 -*-

################################################################################

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

## Draws few curves on one chart showing history of specified symbol:
# - black color curve shows specified column values for all hisory
# - red color curve shows specified column values for target period (see 'period' parameter)
# - tiny black horizontal line show value 1 - first open price ratio in history
# - tiny red vertical lines show target period in all history period (see 'period' parameter)
# - light green and red strips show drop periods (see '__drop_periods' function and 'add' parameter)
#
# Also it shows average price growth ratio per year for target period and for 
# last year. One can see it in char title.
#
# @param[in] history -- dictionary Symbol -> Price History DataFrame. See function load_history(history_dir)
# @param[in] symbol  -- target symbol
# @param[in] company -- full company name for taget symbol
# @paran[in] column  -- DataFrame column name to draw. Default: 'price-ratio'
# @param[in] period  -- pair of dates to draw the period larger on the same chart. Example: ('2016', '2100'). Defaut: None
# @paran[in] add     -- list of additional things to draw on the same chart. Can contain values 'drop-periods'. Default: []
def draw_column(history, symbol, company, column = 'price-ratio', period = None, add = []):
	h = history[symbol]
	
	fig, ax = plt.subplots()
	fig.set_size_inches(16, 6)

	p = sns.pointplot(x='datenum', y=column, data=h, ax=ax, color='black', scale=0.5, markers='', linestyles='-')	
	p.axes.axhline(1, color='black', linewidth=0.5)
	p.axes.set_xlabel('')
	index_size = h.index.unique().size
	x_locs = np.arange(index_size - 1, -1, -12)[::-1]
	plt.xticks(x_locs, h.index.take(x_locs).map(lambda x: x.strftime('%Y-%m-%d')), rotation=90)
	title = '{} ({})'.format(company, symbol)
	
	if 'drop-periods' in add:
		periods = __drop_periods(h)
		ylim = ax.get_ylim()
		for (begin_i, end_i, in_drop) in periods:
			color = 'red' if in_drop else 'green'
			p.bar(begin_i-1, ax.get_ylim()[1], end_i - begin_i, 0, align='edge', color=color, alpha=0.1)
			ax.set_ylim(ylim)
	
	if period:		
		(begin, end) = period
		begin_date = max(pd.to_datetime(begin), h.index.min())
		end_date = min(pd.to_datetime(end), h.index.max())
		growth_ratio = (h['price-ratio'].loc[begin:end][-1] / h['price-ratio'].loc[begin:end][0])
		period_in_years = (end_date - begin_date).days / 365.
		avg_growth_ratio = growth_ratio ** (1./period_in_years)
		title += '        avg growth ratio: %.2f (%.2f for last year)' % (avg_growth_ratio, h['price-growth-1y'][-1])
		if begin in h.index:
			p.axes.axvline(h.index.get_loc(begin).start, color='red', linewidth=0.5)
		if end in h.index:
			p.axes.axvline(h.index.get_loc(end).start, color='red', linewidth=0.5)
		with plt.rc_context({'xtick.color':'red', 'ytick.color':'red'}):
			ax = ax.twiny()
			period_h = h.loc[begin:end]
			p = sns.pointplot(x='datenum', y=column, data=period_h, ax=ax, color='red', scale=0.5, markers='', linestyles='-')		
			p.axes.set_xlabel('')
			index_size = period_h.index.unique().size
			x_locs = np.arange(index_size - 1, -1, -4)[::-1]
			plt.xticks(x_locs, period_h.index.take(x_locs).map(lambda x: x.strftime('%Y-%m-%d')), rotation=90)	
			
	p.set_title(title)
	
	plt.show()

################################################################################


## Compres 'drop-period' column values to list of triplets (begin_i, end_i, in_drop)
# and returns this list.
# begin_i - first period index.
# last_i - last period index plus one.
# All entries in range [begin_i, last_i) have 'drop-period' value equal 0 or less 0.
# in_drop - equals ('drop-period' < 0) for target period.
#
# @param[in] h -- prices history DataFrame. See function common.load_history_dataframe(file_path)
def __drop_periods(h):
	in_drop = h['drop-period'] > 0
	drop_intervals = []
	last_i = 0
	for i in range(1, len(in_drop)):
		it_is_last_i = i == len(in_drop)-1
		if in_drop[last_i] != in_drop[i]:
			drop_intervals.append((last_i, i, in_drop[last_i]))
			last_i = i
	drop_intervals.append((last_i, len(h), in_drop[last_i]))
	return drop_intervals 
	
################################################################################
