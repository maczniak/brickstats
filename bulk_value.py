#!/usr/bin/env python
# -*- coding: utf-8 -*-

if __name__ == "__main__":
	import sqlite3
	import sys
	from Set import Set, make_set
	import util
	
	Set.api_key = util.get_api_key()

	conn = sqlite3.connect('lego_parts.db')
	conn.row_factory = sqlite3.Row
	Set.cursor = conn.cursor()

	if len(sys.argv) > 1:
		set_nums = sys.argv[1:]
	else:
		set_nums = [ '31027' ]

	for set_num in set_nums:
		set = make_set(set_num + '-1', int(set_num))
		v = set.bulk_value()
		print set.id, set.name, '$%s' % v['price']
		print v['warning']

