#coding=utf-8

import memcache

mc = memcache.Client(['127.0.0.1:12111'],debug=0)
mc.set("foo", "bar")
value = mc.get("foo")
print value
