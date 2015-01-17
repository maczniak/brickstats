#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser
from pprint import pprint
import re
import sys
import time
import urllib

def get_api_key():
	config = ConfigParser.RawConfigParser()
	config.read('setting.ini')
	if config.has_option('main', 'api_key'):
		api_key = config.get('main', 'api_key')
		if api_key != '<YOUR REBRICKABLE API KEY HERE>':
			return api_key
	print >> sys.stderr, 'You need to write your Rebrickable API Key in setting.ini'
	sys.exit(-1)

def urlopen(url):
	# "IOError: [Errno socket error] [Errno -2] Name or service not known"
	# IOError('socket error', gaierror(-2, 'Name or service not known'))
	#         ^ errno         ^ strerror
	retry = 0
	while True:
		try:
			return urllib.urlopen(url)
		except IOError as e:
			if e.errno == 'socket error' and retry < 3:
				retry = retry + 1
				time.sleep(retry)
				continue
			raise e

html_entity_pattern = re.compile('&(?:amp;)?#([0-9]{2,3});')
def _decode_html_entity_chr(match):
	return chr(int(match.group(1)))

def decode_html_entity(s):
	s = html_entity_pattern.sub(_decode_html_entity_chr, s)
	s = s.replace('&amp;amp;', '&')
	s = s.replace('&amp;', '&')
	s = s.replace('&quot;', '"') # for &quot; and &amp;quot;
	# both &amp;amp; and &amp; exist in rebrickable database.
	return s

def to_ascii_safe(s):
	return ''.join([c for c in s if ord(c) < 0x80])

line_width = 80
indent_spaces = 2
further_indent_depth = 2

def line_wrap(s, indent_depth):
	ret = ''
	first = True
	while s:
		depth = indent_depth if first else (indent_depth + further_indent_depth)
		width = line_width - indent_spaces * depth
		indent = ' ' * indent_spaces * depth
		if len(s) <= width:
			ret = ret + '%s%s' % (indent, s)
			break
		idx = s[:width].rfind(' ')
		if idx > 0:
			ret = ret + '%s%s\n' % (indent, s[:idx])
			s = s[idx + 1:]
		else:
			idx = s.find(' ', width)
			if idx == -1:
				ret = ret + '%s%s' % (indent, s)
				break
			else:
				ret = ret + '%s%s\n' % (indent, s[:width])
				s = s[idx + 1:]
		first = False
	return ret
