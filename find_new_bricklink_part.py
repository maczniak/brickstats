#!/usr/bin/env python
# -*- coding: utf-8 -*-

if __name__ == "__main__":
	import sqlite3
	import urllib
	from Design import Design, make_design
	from rebrickable_id_to_bricklink import rebrickable_id_to_bricklink
	import util
	
	Design.api_key = util.get_api_key()

	conn = sqlite3.connect('lego_parts.db')
	conn.row_factory = sqlite3.Row
	Design.cursor = conn.cursor()

	for (rebrickable_id, bricklink_id) in rebrickable_id_to_bricklink.iteritems():
		if bricklink_id is None:
			design = make_design(rebrickable_id, True)

			params = urllib.urlencode({'P': design.bricklink_id})
			f = util.urlopen('http://www.bricklink.com/catalogItem.asp?%s' % params)
			res = f.read()
			f.close()

			if res.find('No Item(s) were found.  Please try again!') == -1:
				print 'This part looks promising: %s' % design

