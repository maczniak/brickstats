#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# TODO: make BrickLink show US $ at all times

from datetime import datetime
import json
import re
import urllib
from bs4 import BeautifulSoup
from Design import Design, make_design
from rebrickable_color_to_bricklink import rebrickable_color_to_bricklink
import util

import sys

_loaded_parts = {}
_price_pattern = re.compile("Qty Avg Price:</td><td><b>US [$]([0-9.,]*)</b>")

def make_part(id, color):
	key = '%s+%s' % (id, color)
	if key in _loaded_parts:
		return _loaded_parts[key]
	part = Part(id, color)
	part.read()
	if part.design is None: return None
	_loaded_parts[key] = part
	return part

class Part:
	api_key = None
	cursor = None
	debug = False

	# members - "id", "color", design, sets, qty, abundance_updated,
	#           new_sold_price, used_sold_price, new_lots_price, used_lots_price,
	#             price_updated

	def __init__(self, id, color):
		self.id = id
		self.color = color
		# class init
		Design.api_key = Part.api_key
		Design.cursor = Part.cursor

	def __repr__(self):
		format = '%s %s: %s (%s) %s in %s at %s\n' \
				+ '  new sold %s, used sold %s, new lots %s, used lots %s at %s'
		ret = format % (self.id, rebrickable_color_to_bricklink[self.color][1],
				self.design.name if self.design else 'None',
				self.design.category if self.design else 'None',
				self.sets, self.qty, self.abundance_updated,
				self.new_sold_price, self.used_sold_price,
				self.new_lots_price, self.used_lots_price, self.price_updated)
		return ret.encode('utf-8')

	def read(self):
		self.design = make_design(self.id)
		if self.design is None:
			return

		(self.sets, self.qty, self.abundance_updated, self.new_sold_price,
				self.used_sold_price, self.new_lots_price, self.used_lots_price,
				self.price_updated) = self._query_db()
		if not self.abundance_updated:
			params = urllib.urlencode({'key': Part.api_key, 'format': 'json',
							'part_id': self.id, 'inc_rels': 0, 'inc_ext': 0, 'inc_colors': 1})
			f = util.urlopen('http://rebrickable.com/api/get_part?%s' % params)
			res = f.read()
			f.close()
			info = json.loads(res)
			for color_entry in info['colors']:
				if self.color == int(color_entry['ldraw_color_id']):
					self.sets = int(color_entry['num_sets'])
					self.qty = int(color_entry['num_parts'])
					self.abundance_updated = datetime.now()
					break

			if Part.debug: print util.line_wrap('new part: %s %s (%s) BL-%s' % (
						self.design.id, util.to_ascii_safe(self.design.name),
						rebrickable_color_to_bricklink[self.color][1],
						self.design.bricklink_id),
					1)
			if self.design.bricklink_id is None: # not in bricklink database
				self.new_sold_price = self.used_sold_price = None
				self.new_lots_price = self.used_lots_price = None
				self.price_updated = datetime.now()
				return

			params = urllib.urlencode({'P': self.design.bricklink_id,
										'colorID': rebrickable_color_to_bricklink[self.color][0]})
			f = util.urlopen('http://www.bricklink.com/catalogPG.asp?%s' % params)
			res = f.read()
			f.close()
			start = res.find('<TR BGCOLOR="#C0C0C0">')
			soup = BeautifulSoup(res[start:])
			if soup.tr is None: # no price info yet 
				# ex) http://www.bricklink.com/catalogPG.asp?P=3004&colorID=158
				self.new_sold_price = self.used_sold_price = None
				self.new_lots_price = self.used_lots_price = None
				self.price_updated = datetime.now()
				return
			tds = soup.tr.contents
			self.new_sold_price = self._parse_price(str(tds[0]))
			self.used_sold_price = self._parse_price(str(tds[1]))
			self.new_lots_price = self._parse_price(str(tds[2]))
			self.used_lots_price = self._parse_price(str(tds[3]))
			self.price_updated = datetime.now()

	def save(self):
		if self.design:
			self.design.save()

		(sets, qty, abundance_updated, new_sold_price, used_sold_price,
				new_lots_price, used_lots_price, price_updated) = self._query_db()
		if abundance_updated:
			if sets != self.sets or qty != self.qty \
					or abundance_updated != self.abundance_updated \
					or new_sold_price != self.new_sold_price \
					or used_sold_price != self.used_sold_price \
					or new_lots_price != self.new_lots_price \
					or used_lots_price != self.used_lots_price \
					or price_updated != self.price_updated:
				Part.cursor.execute("UPDATE part_detail SET "
					+ "sets = ?, qty = ?, abundance_updated = ?, new_sold_price = ?, "
					+ "used_sold_price = ?, new_lots_price = ?, used_lots_price = ?, "
					+ "price_updated = ? WHERE id = ? and color = ?",
					(self.sets, self.qty, self.abundance_updated, self.new_sold_price,
						self.used_sold_price, self.new_lots_price, self.used_lots_price,
						self.price_updated, self.id, self.color) )
		else:
			Part.cursor.execute("INSERT INTO part_detail "
				+ "(id, color, sets, qty, abundance_updated, new_sold_price, "
				+ " used_sold_price, new_lots_price, used_lots_price, price_updated) "
				+ "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
				(self.id, self.color, self.sets, self.qty, self.abundance_updated,
					self.new_sold_price, self.used_sold_price, self.new_lots_price,
					self.used_lots_price, self.price_updated) )
		
	def _query_db(self):
		rows = Part.cursor.execute(
				"SELECT * FROM part_detail WHERE id = ? and color = ?",
				(self.id, self.color) )
		for row in rows:
			sets = (row['sets'])
			qty = (row['qty'])
			abundance_updated = row['abundance_updated']
			new_sold_price = \
					float(row['new_sold_price']) if row['new_sold_price'] else None
			used_sold_price = \
					float(row['used_sold_price']) if row['used_sold_price'] else None
			new_lots_price = \
					float(row['new_lots_price']) if row['new_lots_price'] else None
			used_lots_price = \
					float(row['used_lots_price']) if row['used_lots_price'] else None
			price_updated = row['price_updated']
			return (sets, qty, abundance_updated, new_sold_price, used_sold_price,
							new_lots_price, used_lots_price, price_updated)
		return (None, None, None, None, None, None, None, None)

	def _parse_price(self, str):
		match = _price_pattern.search(str)
		if match:
			return float(match.group(1))
		return None

if __name__ == "__main__":
	import sqlite3
	import sys
	
	Part.api_key = util.get_api_key()

	conn = sqlite3.connect('lego_parts.db')
	conn.row_factory = sqlite3.Row
	Part.cursor = conn.cursor()

	if len(sys.argv) > 1:
		args = sys.argv[1:]
	else:
		args = [ 99781, 0 ] # example
		# or unicode example [ 54200, 143 ]

	for (part_id, color) in [ args[i:i+2] for i in xrange(0, len(args), 2) ]:
		part = make_part(part_id, color)
		print part
		#part.price_updated = datetime.now()
		part.save()
		conn.commit()

# Rebrickable API:
#   api/get_part
#     part_id, name, year1, year2, category
#     related_parts (optional)
#       related_to
#         part_id, rel_type
#     external_part_ids (optional)
#       lego_element_ids
#         color, element_id
#     colors (optional)
#       ldraw_color_id, color_name, num_sets, num_parts
#
# BrickLink price guide
#   http://www.bricklink.com/catalogPG.asp?P={part_id}&colorID={color_id}
