# -*- coding: utf-8 -*-

################################################################################

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import common

## Draws few curves on one chart showing history of specified symbol:
# - black color curve shows specified column values for all hisory
# - red color curve shows specified column values for target period (see 'period' parameter)
# - tiny black horizontal line show value 1 - first open price ratio in history
# - tiny red vertical lines show target period in all history period (see 'period' parameter)
# - light green and red strips show drop periods (see 'common.drop_periods' function and 'add' parameter)
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

	if 'periods' in add:
		draw_periods(h, p, ax, add)

	if 'drop-periods' in add:
		periods = common.drop_periods(h)
		ylim = ax.get_ylim()
		label_y_shift_step = 0
		height = ax.get_ylim()[1] - ax.get_ylim()[0]
		label_y_shift = height / 25
		for (begin_i, end_i, in_drop) in periods:
			color = 'red' if in_drop else 'green'
			start_x = begin_i-1
			width = end_i - begin_i
			p.bar(start_x, ax.get_ylim()[1], width, 0, align='edge', color=color, alpha=0.1)
			ax.set_ylim(ylim)
			if 'drop-periods-labels' in add:
				text_y = (ax.get_ylim()[0] + ax.get_ylim()[1])//2 + label_y_shift  * (label_y_shift_step % 3)
				p.text(start_x, text_y, '%i'%(end_i-begin_i))
				label_y_shift_step += 1
	
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
	else:
		title += '        growth ratio: %.2f' % (h['price-ratio'][-1]/h['price-ratio'][0])
			
	p.set_title(title)
	
	plt.show()

#-------------------------------------------------------------------------------

def draw_periods(h, picture, ax, add):
	periods = common.periods(h)
	ylim = ax.get_ylim()
	label_y_shift_step = 0
	height = ax.get_ylim()[1] - ax.get_ylim()[0]
	label_y_shift = height / 25
	for index, period in periods.iterrows():
		begin_i = h.index.get_loc(period['begin'])
		if period['type'] == 'growth':
			begin_i += 1
		end_i = h.index.get_loc(period['end']) + 1		
		color = 'red' if period['type'] == 'drop' else 'green'
		alpha = 0.1 if period['type'] in ['drop', 'growth'] else 0.175
		start_x = begin_i-1
		width = end_i - begin_i
		picture.bar(start_x, ax.get_ylim()[1], width, 0, align='edge', color=color, alpha=alpha)
		ax.set_ylim(ylim)
		
		extremum_i = h.index.get_loc(period['extremum-date'])
		picture.axes.axvline(extremum_i, color=color, linewidth=0.5)
		if 'periods-labels' in add:
			text_y = (ax.get_ylim()[0] + ax.get_ylim()[1])/2. + label_y_shift  * (label_y_shift_step % 3)
			picture.text(start_x, text_y, '%i'%(end_i - begin_i))
			label_y_shift_step += 1
		
################################################################################
