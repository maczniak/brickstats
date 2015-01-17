// This script requires PhantomJS.
var page = require('webpage').create();
var url = 'http://shop.lego.com/en-US/Whats-New-Category';
/*
	en-AU - Australia / English
	en-BE - Belgium / English, fr-BE - Belgique / Français
	en-CA - Canada / English, fr-CA - Canada / Français
	en-CZ - Czech Republic / English
	en-DK - Denmark / English
	en-DE - Germany / English, de-DE - Deutschland / Deutsch
	en-FI - Finland / English
	en-FR - France métropolitaine / English,
		fr-FR - France métropolitaine / Français
	en-HU - Hungary / English
	en-IE - Ireland / English
	en-IT - Italy / English, it-IT - Italia / Italiano
	en-LU - Luxemburg / English, fr-LU - Luxembourg / Français,
		de-LU - Luxemburg / Deutsch
	en-NL - Netherlands / English
	en-NZ - New Zealand / English
	en-NO - Norway / English
	en-PL - Poland / English
	en-PT - Portugal / English
	en-ES - Spain / English, es-ES - España / Español
	en-CH - Switzerland / English, de-CH - Schweiz / Deutsch,
		fr-CH - Suisse / Français
	en-SE - Sweden / English
	en-GB - United Kingdom / English
	en-US - United States / English
	en-AT - Austria / English, de-AT - Österreich / Deutsch
	ko-KR - 대한민국 / 한글
*/
var options = {
	'au': ['en'],
	'be': ['en', 'fr'],
	'ca': ['en', 'fr'],
	'cz': ['en'],
	'dk': ['en'],
	'de': ['en', 'de'],
	'fi': ['en'],
	'fr': ['en', 'fr'],
	'hu': ['en'],
	'ie': ['en'],
	'it': ['en', 'it'],
	'lu': ['en', 'fr', 'de'],
	'nl': ['en'],
	'nz': ['en'],
	'no': ['en'],
	'pl': ['en'],
	'pt': ['en'],
	'es': ['en', 'es'],
	'ch': ['en', 'de', 'fr'],
	'se': ['en'],
	'gb': ['en'],
	'us': ['en'],
	'at': ['en', 'de'],
	'kr': ['ko']
}

function array_contains(arr, e) {
	var i = 0;
	while (i < arr.length) {
		if (arr[i++] === e) return true;
	}
	return false;
}

var args = require('system').args;
if (array_contains(args, '-h') || array_contains(args, '--help')) {
		console.error(args[0] + ' [country [language]]\n' +
'    country - ISO 3166-1 two-letter country code (default: us)\n' +
'    language - ISO 639-1 two-letter language code (default:\n' +
'               the first language of country language list, mainly en)')
		phantom.exit(0);
}
if (args.length > 1) {
	if (!(args[1] in options)) {
		console.error('"' + args[1] +
									'" is not a valid ISO 3166-1 two-letter country code.');
		phantom.exit(-1);
	}
	var lang = options[args[1]][0]
	if (args.length > 2) {
		if (!array_contains(options[args[1]], args[2])) {
			console.error('"' + args[2] +
										'" is not a valid ISO 639-1 two-letter language code.');
			phantom.exit(-1);
		}
		lang = args[2]
	}
	url = 'http://shop.lego.com/' + lang + '-' + args[1].toUpperCase() +
				'/Whats-New-Category';
}

var product_pattern = new RegExp('<ul id="product-badges">(.*?)</ul>.*?<h4>.*?<a title="(.*?)" name="(.*?)" href="(.*?)">.*?<ul.*?<em>[$£€]?([0-9,.]*).*?(?:<em>[$£]?([0-9,.]*).*?</ul>|</ul>).*?<div.*?>(.*?)</div>', 'g');
// 1: badge, 2: title, 3: number, 4: url, 5: price, 6: sale price, 7: avaialable

var element_pattern = new RegExp('<[^>]*>', 'g'); // for HTML element removal
var number_sep_pattern = new RegExp(',', 'g'); // for number grouping separator

function print_all_products(status) {
	// STEP 3: parse a product list
	var body = page.content;
	var idx = body.indexOf('product-results');
	body = body.substr(idx);
	body = body.replace(/\n|\t/g, '');
	while (match = product_pattern.exec(body)) {
		var badge = match[1].trim().replace(element_pattern, '');
		var title = match[2];
		var number = match[3];
		var url = match[4];
		var price = match[5]; // match[5].replace(number_sep_pattern, '');
		var sale_price = (match[6] ? match[6] : price);
		var available = match[7].trim();
		console.log(badge + '|' + title + '|' + number + '|' + url + '|'
								+ price + '|' + sale_price + '|' + available);
	}
	phantom.exit();
}

page.open(url, function(status) {
	page.onLoadFinished = function(status) {
		// STEP 2 : click a No-Pagination link
		page.onLoadFinished = print_all_products;

		var ret = page.evaluate(function() {
			var view_all_link =
				document.getElementsByClassName('test-pagination-all')[0];
			var ev = document.createEvent('MouseEvent');
			ev.initMouseEvent(
				'click',
				true /* bubble */, true /* cancelabble */,
				window, null,
				0, 0, 0, 0, /* coordinates */
				false, false, false, false, /* modifier keys */
				0 /* button=left */, null
			);
			view_all_link.dispatchEvent(ev);
		});
	};
	var ret = page.evaluate(function() {
		// STEP 1: click a Clear-All-Filter button
		var clear_all_button = document.getElementsByClassName('clear-all')[0];
		var ev = document.createEvent('MouseEvent');
		ev.initMouseEvent(
			'click',
			true /* bubble */, true /* cancelabble */,
			window, null,
			0, 0, 0, 0, /* coordinates */
			false, false, false, false, /* modifier keys */
			0 /* button=left */, null
		);
		clear_all_button.dispatchEvent(ev);
	});
});

