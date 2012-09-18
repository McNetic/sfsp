'''
Created on 18.09.2012

@author: ehe
'''

import collections

class BucketSet(collections.MutableSet):

    def __init__(self):
        self.buckets = collections.OrderedDict()
        self.map = {}

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key, bucket):
        if key in self.map:
            self.buckets[bucket].remove(key)
        self.map[key] = bucket
        if bucket not in self.buckets:
            self.buckets[bucket] = set()
        self.buckets[bucket].add(key)

    def discard(self, key):
        if key in self.map:
            self.buckets[self.map.pop(key)].pop(key)

    def __iter__(self):
        end = self.end
        curr = end[NEXT]
        while curr is not end:
            yield curr[KEY]
            curr = curr[NEXT]

    def __reversed__(self):
        end = self.end
        curr = end[PREV]
        while curr is not end:
            yield curr[KEY]
            curr = curr[PREV]

    def pop(self, last = True):
        if not self:
            raise KeyError('set is empty')
        key = next(reversed(self)) if last else next(iter(self))
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)

    def __del__(self):
        self.clear()                    # remove circular references
