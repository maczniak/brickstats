#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import json
import urllib
from Part import Part, make_part
import util

_loaded_sets = {}

def make_set(id, readable_id):
	if id in _loaded_sets:
		return _loaded_sets[id]
	set = Set(id, readable_id)
	if not set.read():
		return None
	_loaded_sets[id] = set
	return set

class Set:
	api_key = None
	cursor = None

	# members - "id", name, readable_id, pieces, theme, year, updated, blocks
	#   blocks is tuple of (Part, qty, spare, updated).
	#   spare is one of 0 (required to build) or 1 (spare).

	def __init__(self, id, readable_id):
		self.id = id
		self.readable_id = int(readable_id)
		# class init
		Part.api_key = Set.api_key
		Part.cursor = Set.cursor

	def __repr__(self):
		ret = '%s: %s (%s, %s) %s pieces at %s' % (self.id, self.name, self.theme,
																					self.year, self.pieces, self.updated)
		return ret.encode('utf-8')

	def read(self):
		(self.name, readable_id, self.pieces, self.theme, self.year,
				self.updated) = self._query_db()
		if self.name:
			self.readable_id = readable_id # prevent overwriting
			self.blocks = self._read_blocks()
		else:
			params = urllib.urlencode({'key': Set.api_key, 'format': 'json',
																	'set': self.id})
			f = util.urlopen('http://rebrickable.com/api/get_set_parts?%s' % params)
			res = f.read()
			f.close()
			if res == 'NOSET':
				return False
			info = json.loads(res)[0]
			now = datetime.now()
			self.blocks = [ ( make_part(i['part_id'], int(i['ldraw_color_id'])),
						int(i['qty']), int(i['type']) - 1, now )
					for i in info['parts'] ]

			params = urllib.urlencode({'key': Set.api_key, 'format': 'json',
																	'set_id': self.id})
			f = util.urlopen('http://rebrickable.com/api/get_set?%s' % params)
			res = f.read()
			f.close()
			info = json.loads(res)[0]
			self.name = util.decode_html_entity(info['descr'])
			self.pieces = int(info['pieces'])
			self.theme = info['theme']
			self.year = int(info['year'])
			self.updated = datetime.now()
		return True

	def save(self):
		(name, readable_id, pieces, theme, year, updated) = self._query_db()
		if name:
			for b in self.blocks:
				self._save_block(b)

			if name != self.name or readable_id != self.readable_id \
					or pieces != self.pieces or theme != self.theme or year != self.year \
					or updated != self.updated:
				Set.cursor.execute("UPDATE sets SET "
					+ "name = ?, readable_id = ?, pieces = ?, theme = ?, year = ?, "
					+ "updated = ? WHERE id = ?",
					(self.name, self.readable_id, self.pieces, self.theme, self.year,
						self.updated, self.id) )
		else:
			for b in self.blocks:
				b[0].save()

				Set.cursor.execute("INSERT INTO set_part "
					+ "(set_id, part_id, color, qty, spare, updated) "
					+ "values (?, ?, ?, ?, ?, ?)",
					(self.id, b[0].id, b[0].color, b[1], b[2], b[3]) )

			Set.cursor.execute("INSERT INTO sets "
				+ "(id, name, readable_id, pieces, theme, year, updated) "
				+ "values (?, ?, ?, ?, ?, ?, ?)",
				(self.id, self.name, self.readable_id, self.pieces, self.theme,
					self.year, self.updated) )
		
	def _query_db(self):
		rows = Set.cursor.execute("SELECT * FROM sets WHERE id = ?", (self.id,) )
		for row in rows:
			name = row['name']
			readable_id = row['readable_id']
			pieces = row['pieces']
			theme = row['theme']
			year = row['year']
			updated = row['updated']
			return (name, readable_id, pieces, theme, year, updated)
		return (None, None, None, None, None, None)

	def _read_blocks(self):
		rows = Set.cursor.execute(
												"SELECT * FROM set_part WHERE set_id = ?", (self.id,) )
		# it does not work because make_part() does database query by itself.
		#ret = [ ( make_part(i['part_id'], int(i['color'])), int(i['qty']),
		#														int(i['spare']), i['updated'] ) for i in rows]
		ret = [ ( i['part_id'], int(i['color']), int(i['qty']),
																int(i['spare']), i['updated'] ) for i in rows]
		ret = [ ( make_part(i[0], i[1]), i[2], i[3], i[4] ) for i in ret]
		return ret

	def _save_block(self, b):
		b[0].save()

		rows = Set.cursor.execute(
				"SELECT * FROM set_part WHERE set_id = ? and part_id = ? and color = ?",
				(self.id, b[0].id, b[0].color) )
		for row in rows:
			qty = row['qty']
			spare = row['spare']
			updated = row['updated']
			break
		if qty != b[1] or spare != b[2] or updated != b[3]:
			Set.cursor.execute("UPDATE set_part SET "
				+ "qty = ?, spare = ?, updated = ? "
				+ "WHERE set_id = ? and part_id = ? and color = ?",
			(b[1], b[2], b[3], self.id, b[0].id, b[0].color) )

	def bulk_value(self):
		sum = 0
		warning = ''
		for b in self.blocks:
			if b[0].new_sold_price is not None:
				sum += b[0].new_sold_price * b[1]
			elif b[0].used_sold_price is not None:
				sum += b[0].used_sold_price * b[1]
				warning = warning + '%s used_sold_price used\n' % b[0].id
			elif b[0].new_lots_price is not None:
				sum += b[0].new_lots_price * b[1]
				warning = warning + '%s new_lots_price used\n' % b[0].id
			elif b[0].used_lots_price is not None:
				sum += b[0].used_lots_price * b[1]
				warning = warning + '%s used_lots_price used\n' % b[0].id
			else:
				warning = warning + '%s no price\n' % b[0].id
		return { 'price': sum, 'warning': warning }

if __name__ == "__main__":
	import sqlite3
	import sys
	
	Part.debug = True

	Set.api_key = util.get_api_key()

	conn = sqlite3.connect('lego_parts.db')
	conn.row_factory = sqlite3.Row
	Set.cursor = conn.cursor()

	if len(sys.argv) > 1:
		set_nums = sys.argv[1:]
	else:
		set_nums = [ '31031' ] # example

	for set_num in set_nums:
		set = make_set(set_num + '-1', int(set_num))
		if not set:
			print 'set %s-1 does not exist in database.' % set_num
			continue
		print util.line_wrap('new set: %s %s (%s, %s) %s pieces' % (set.id,
						util.to_ascii_safe(set.name), set.theme, set.year, set.pieces), 0)
		print
		#set.updated = datetime.now()
		set.save()
		conn.commit()

# Rebrickable API:
#   api/get_set
#     set_id, type, pieces, descr, theme, year, img_tn, img_sm, img_big
#
#   api/get_set_parts
#     parts
#       part_name, qty, part_img_url, color_name, part_id, ldraw_color_id,
#       element_img_url, element_id, type (1, 2)
#     descr, set_id, set_img_url
