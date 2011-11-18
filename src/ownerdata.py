import threading
import contender

class OwnerData( object ):
	def __init__( self, owner ):
		self.p__owner = ''
		self.p__mutex = threading.Lock()
		self.p__contenders = {}

	def add( self, contend ):
		if type( contend ) is not contender.contender:
			raise TypeError

		self.p__contenders[ contend ] = 1

	def remove( self, contend ):
		if type( contend ) is not contender.contender:
			raise TypeError

		if self.p__contenders.has_key( contend ):
			del self.p__contenders[ contend ]

	def getList( self ):
		return self.p__contenders.keys()

	def __len__( self ):
		return len( self.p__contenders )

	def lock( self ):
		self.p__mutex.acquire()

	def unlock( self ):
		self.p__mutex.release()

	def stringLockDump( self ):
		retval = []
		for key in self.p__contenders.keys():
			retval.append( "    ( %s, %s )" % ( key.getKey(), key.getIndex() ) )

		return retval
