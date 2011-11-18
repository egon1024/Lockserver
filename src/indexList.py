import threading
from contenderList import contenderList
from ownerlist import OwnerList

class indexList( object ):
	def __init__( self, owner_list = None ):
		if type( owner_list ) is not OwnerList:
			raise TypeError, "Invalid owner_list"

		self.p__mutex = threading.Lock()
		self.p__contenderLists = {}
		self.p__owner_list = owner_list

	# Find an contenderList based off a particular index
	def find( self, index ):
		if type( index ) != str:
			raise TypeError, "Unknown type passed to find()"

		return self.p__contenderLists.get( index, None )
	
	def getList( self ):
		return self.p__contenderLists.values()

	def lock( self ):
		self.p__mutex.acquire()

	def unlock( self ):
		self.p__mutex.release()

	def setdefault( self, index ):
		tmp = contenderList( self.p__owner_list )
		return self.p__contenderLists.setdefault( index, tmp )

	def cleanThySelf( self ):
		retval = 0

		for ( index, contender_list ) in self.p__contenderLists.items():
			retval += contender_list.cleanThySelf()
			if len( contender_list ) == 0:
				retval += 1
				del self.p__contenderLists[ index ]

		return retval

	def stringLockDump( self ):
		retval = []

		for ( key, index ) in self.p__contenderLists.items():
			retval.append( "    " + key + ":" )
			retval += index.stringLockDump()

		return retval

	# Length call
	def __len__( self ):
		return len( self.p__contenderLists )
