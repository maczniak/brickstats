#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3

conn = sqlite3.connect('lego_parts.db')

c = conn.cursor()

c.execute('''
	CREATE TABLE sets (
		id text,
		name text,
		readable_id int,
		pieces int,
		theme text,
		year int,
		updated datetime
	)''')

c.execute('''
	CREATE TABLE parts (
		id text,
		name text,
		category text,
		first_year int,
		last_year int,
		bricklink_id int,
		updated datetime
	)''')

c.execute('''
	CREATE TABLE set_part (
		set_id text,
		part_id int,
		color int,
		qty int,
		spare int,
		updated datetime
	)''')

c.execute('''
	CREATE TABLE part_detail (
		id int,
		color int,
		sets int,
		qty int,
		abundance_updated datetime,
		new_sold_price numeric,
		used_sold_price numeric,
		new_lots_price numeric,
		used_lots_price numeric,
		price_updated datetime
	)''')

conn.commit()

conn.close()

