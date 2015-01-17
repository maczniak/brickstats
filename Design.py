#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import json
import re
import urllib
from rebrickable_id_to_bricklink import rebrickable_id_to_bricklink
import util

_loaded_designes = {}
_bricklink_id_pattern = re.compile(
	"<a href='http://www[.]bricklink[.]com/catalogItem[.]asp[?]P=.*?'>(.*?)</a>")

def make_design(id, force = False):
	if id in _loaded_designes:
		return _loaded_designes[id]
	design = Design(id)
	design.read(force)
	if design.name is None: return None
	_loaded_designes[id] = design
	return design

class Design:
	api_key = None
	cursor = None

	# members - "id", name, category, first_year, last_year, bricklink_id, updated

	def __init__(self, id):
		self.id = id

	def __repr__(self):
		ret = '%s: %s (%s) %s~%s BL:%s at %s' % (self.id, self.name, self.category,
							self.first_year, self.last_year, self.bricklink_id, self.updated)
		return ret.encode('utf-8')

	def read(self, force = False):
		(self.name, self.category, self.first_year, self.last_year,
				self.bricklink_id, self.updated) = self._query_db()
		if (not self.name) or force:
			if (self.id in rebrickable_id_to_bricklink) and not force:
				self.bricklink_id = rebrickable_id_to_bricklink[self.id]
			else:
				f = util.urlopen('http://rebrickable.com/parts/%s' % self.id)
				res = f.read()
				f.close()
				match = _bricklink_id_pattern.search(res)
				if match is None: # like part 79015-1 of collection set 5004261-1 
					print 'part %s does not exist.' % self.id
					return
				self.bricklink_id = match.group(1)

			params = urllib.urlencode({'key': Design.api_key, 'format': 'json',
							'part_id': self.id, 'inc_rels': 0, 'inc_ext': 0, 'inc_colors': 1})
			f = util.urlopen('http://rebrickable.com/api/get_part?%s' % params)
			res = f.read()
			f.close()
			info = json.loads(res)
			self.name = util.decode_html_entity(info['name'])
			self.category = info['category']
			self.first_year = int(info['year1'])
			self.last_year = int(info['year2'])
			self.updated = datetime.now()

	def save(self):
		(name, category, first_year, last_year, bricklink_id, updated) = \
																													self._query_db()
		if name:
			if name != self.name or category != self.category \
					or first_year != self.first_year or last_year != self.last_year \
					or bricklink_id != self.bricklink_id or updated != self.updated:
				Design.cursor.execute("UPDATE parts SET "
					+ "name = ?, category = ?, first_year = ?, last_year = ?, "
					+ "bricklink_id = ?, updated = ? WHERE id = ?",
					(self.name, self.category, self.first_year, self.last_year,
						self.bricklink_id, self.updated, self.id) )
		else:
			Design.cursor.execute("INSERT INTO parts "
				+ "(id, name, category, first_year, last_year, bricklink_id, updated) "
				+ "values (?, ?, ?, ?, ?, ?, ?)",
				(self.id, self.name, self.category, self.first_year, self.last_year,
					self.bricklink_id, self.updated) )
		
	def _query_db(self):
		rows = Design.cursor.execute("SELECT * FROM parts WHERE id = ?", (self.id, ) )
		for row in rows:
			name = row['name']
			category = row['category']
			first_year = row['first_year']
			last_year = row['last_year']
			bricklink_id = row['bricklink_id']
			updated = row['updated']
			return (name, category, first_year, last_year, bricklink_id, updated)
		return (None, None, None, None, None, None)

if __name__ == "__main__":
	import sqlite3
	import sys

	Design.api_key = util.get_api_key()

	conn = sqlite3.connect('lego_parts.db')
	conn.row_factory = sqlite3.Row
	Design.cursor = conn.cursor()

	if len(sys.argv) > 1:
		design_ids = sys.argv[1:]
	else:
		design_ids = [ 99781 ] # example

	for design_id in design_ids:
		design = make_design(design_id)
		print design
		#design.updated = datetime.now()
		design.save()
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
# Rebrickable part information:
#   http://rebrickable.com/parts/{part_id}
#     BrickLink ID: <a href='http://www.bricklink.com/catalogItem.asp?P=X'>X</a>
