import threading
from indexList import indexList
from ownerlist import OwnerList

class keyList( object ):
	def __init__( self, owner_list = None ):
		if type( owner_list ) is not OwnerList:
			raise TypeError, "Invalid owner_list"

		self.p__mutex = threading.Lock()
		self.p__indexLists = {}
		self.p__owner_list = owner_list

	# Find an indexList based off a particular key
	def find( self, key ):
		if type( key ) != str:
			raise TypeError, "Unknown type passed to find()"

		return self.p__indexLists.get( key, None )

	def lock( self ):
		self.p__mutex.acquire()

	def unlock( self ):
		self.p__mutex.release()

	def setdefault( self, key ):
		tmp = indexList( self.p__owner_list )
		return self.p__indexLists.setdefault( key, tmp )

	def cleanThySelf( self ):
		retval = 0

		for ( key, index ) in self.p__indexLists.items():
			retval += index.cleanThySelf()
			if len( index ) == 0:
				retval += 1
				del self.p__indexLists[ key ]

		return retval

	def stringLockDump( self ):
		retval = []

		for ( key, index ) in self.p__indexLists.items():
			retval.append( key + ":" )
			retval += index.stringLockDump()

		return retval

	# Length call
	def __len__( self ):
		return len( self.p__indexLists )
