# brickstats
Lego product info utilities

Refer to [this blog post](http://www.linkedbigdata.com/2015/01/lego-bulk-index.html).

TODO:
* lego shop stock & price tracker
* updated information processing
* exception handling and notification for daemon-like execution
* web ui
* avoid complex commands like these:

`(cut -f 3 -d '|' us_list | xargs ./bulk_value.py) | paste -d '|' - us_list | awk -F '|' '{ printf "%.1f%% set %s, bulk $%.2f, price $%.2f\n", 100 * $2 / $7, $1, $2, $7 }' | sort -nr`

`phantomjs list_lego_shop.js kr | tee kr_list | cut -f 3 -d '|' | xargs ./Set.py`

`(cut -f 3 -d '|' kr_list | xargs ./bulk_value.py) | paste -d '|' - kr_list | awk -F '|' '{ price = $7; sub(",", "", price); printf "%.1f%% set %d, bulk $%.2f, price %d WON\n", 100 * $2 * 1088.00 / price, $1, $2, price }' | sort -nr`
