#!/usr/bin/env python
# -*- coding: utf-8 -*-

if __name__ == "__main__":
	import getopt
	import sqlite3
	import sys
	from Set import Set, make_set
	import util
	
	bulk_value_type = Set.ALL

	opts, args = getopt.getopt(sys.argv[1:], 'hamM',
														['help', 'all', 'except-minifig', 'minifig-only'])
	for o, a in opts:
		if o in ('-h', '--help'):
			print >> sys.stderr, \
"""%s [--all] [--except-minifig] [--minifig-only] [SET]...
    -a, -all - include all parts
    -m, --minifig-only - include minifig-related parts only
    -M, --except-minifig - include parts except minifig-related parts""" % (
				sys.argv[0]
			)
			sys.exit()
		if o in ('-a', '--all'):
			bulk_value_type = Set.ALL
		if o in ('-m', '--minifig-only'):
			bulk_value_type = Set.MINIFIG_ONLY
		if o in ('-M', '--except-minifig'):
			bulk_value_type = Set.EXCEPT_MINIFIG

	Set.api_key = util.get_api_key()

	conn = sqlite3.connect('lego_parts.db')
	conn.row_factory = sqlite3.Row
	Set.cursor = conn.cursor()

	if len(args) > 0:
		set_nums = args
	else:
		set_nums = [ '31027' ]

	for set_num in set_nums:
		set = make_set(set_num)
		if set is None:
			print '%s|-1' % set_num
			continue

		v = set.bulk_value(bulk_value_type)
		if sys.stdout.isatty():
			print set.id, set.name, '$%s' % v['price']
			print v['warning']
		else:
			print '%s|%s' % (set_num, v['price'])
