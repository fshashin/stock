# -*- coding: utf-8 -*-

################################################################################

import numpy as np
import sys

################################################################################

## Returns list of windows for target prices history and window size.
# Every window represented by triplet (begin_date, end_date, window_is_closed).
#
# @param[in] history	 -- DataFrame with prices history
# @param[in] window_size -- window size in days
def get_windows(history, window_size):
	return __get_windows([*history.index], window_size)

def __get_windows(history_index, window_size):
	opened_windows = []	
	closed_windows_cnt = 0
	windows = []
	for row_n in range(len(history_index) - 1, -1, -1):
		current_date = history_index[row_n]
		opened_windows.append(current_date)

		prev_date = history_index[row_n-1] if row_n > 0 else current_date		
		for window_end in opened_windows[closed_windows_cnt:]:
			if (window_end - prev_date).days < window_size:
				break

			closed_windows_cnt += 1
			days_from_current_date_to_window_end = abs((window_end - current_date).days - window_size)
			days_from_prev_date_to_window_end = abs((window_end - prev_date).days - window_size)

			if days_from_current_date_to_window_end < days_from_prev_date_to_window_end:
				windows.append((current_date, window_end, True))
			else:
				windows.append((prev_date, window_end, True))


	for window_end in opened_windows[closed_windows_cnt:]:
		windows.append((history_index[0], window_end, False))
	
	windows.reverse()
	return windows


## Applies target function to moving windows on prices history.
# Returns list of result values. 
#
# @param[in] f		   -- function to apply. Example: see function growth_ratio 
# @param[in] history	 -- DataFrame with prices history
# @param[in] window_size -- window size in days. Default: 365
def moving_f(f, history, window_size = 365):
	return [f(history, begin, end, closed) for (begin, end, closed) in get_windows(history, window_size)]


## Returns growth ratio for target moving window. 
# See function get_windows.
#
# @param[in] history -- DataFrame with prices history
# @param[in] begin   -- first date inside the window
# @param[in] end	 -- last date inside the window
# @param[in] closed  -- defines if history contains enough items for filling entire window
def growth_ratio(history, begin, end, closed):
	if not closed:
		return np.nan
	if abs(history['open'][begin]) < sys.float_info.epsilon:
		return np.nan
	return history['close'][end] / history['open'][begin]

## Returns average growth ratio for target moving window and target averaging period.
# See function get_windows.
#
# @param[in] history    -- DataFrame with prices history
# @param[in] begin      -- first date inside the window
# @param[in] end	    -- last date inside the window
# @param[in] closed     -- defines if history contains enough items for filling entire window
# @param[in] avg_period -- averaging period in days. Defautl: 365
def avg_growth_ratio(history, begin, end, closed, avg_period = 365):
	if not closed:
		return np.nan
	if abs(history['open'][begin]) < sys.float_info.epsilon:
		return np.nan	
	ratio = history['close'][end] / history['open'][begin]
	period_in_years = (end - begin).days / float(avg_period)
	return ratio ** (1./period_in_years) 

################################################################################
