'''
Created on 18.09.2012

@author: ehe
'''

from collections import MutableSet
from sfsp.util.scollection import SortedCollection

class BucketSet(MutableSet):

    def __init__(self):
        self.buckets = {}
        self.bucketlist = SortedCollection()
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
            self.bucketlist.insert(bucket)
            self.buckets[bucket] = set()
        self.buckets[bucket].add(key)

    def discard(self, key):
        if key in self.map:
            self.buckets[self.map.pop(key)].pop(key)

    def __iter__(self):
        for bucket in self.bucketlist:
            for key in self.buckets[bucket]:
                yield key

    def __reversed__(self):
        for bucket in reversed(self.bucketlist):
            for key in reversed(self.buckets[bucket]):
                yield key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(map(lambda bucket: '%d: (%r)' % (bucket, self.buckets[bucket]), self.bucketlist)))

#    def __eq__(self, other):
#        if isinstance(other, OrderedSet):
#            return len(self) == len(other) and list(self) == list(other)
#        return set(self) == set(other)
