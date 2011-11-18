import time
from struct import pack, unpack

class contender( object ):

	defaultPriority = 3
	defaultTTL 		= 300
	defaultTTW 		= 300

	def __hash__( self ):
		return hash( ( self.p__owner, self.p__key, self.p__index ) )

	def __init__( self, key, index, owner, priority = None, TTL = None, TTW = None ):
		if type( key ) is not str:
			raise TypeError, "Invalid type of key"
		else:
			self.p__key = key

		if type( index ) is not str:
			raise TypeError, "Invalid type of index"
		else:
			self.p__index = index

		if type( owner ) is not str:
			raise TypeError, "Invalid type of owner"
		else:
			self.p__owner = owner

		if priority is None:
			self.p__priority = self.defaultPriority
		else:
			try:
				priority = int( priority )
				self.p__priority = priority
			except:
				raise TypeError, "Invalid type of priority"

		if TTL is None:
			self.p__TTL = self.defaultTTL
		else:
			try:
				TTL = int( TTL )
				self.p__TTL = TTL
			except:
				raise TypeError, "Invalid type of TTL"

		if TTW is None:
			self.p__TTW = self.defaultTTW
		else:
			try:
				TTW = int( TTW )
				self.p__TTW = TTW
			except:
				raise TypeError, "Invalid type of TTW"

		
		self.p__am_owner = 0
		self.p__obtain_ts = 0
		self.p__request_ts = int( time.time() )
		self.p__last_update_ts = int( time.time() )

	def getKey( self ):
		return self.p__key

	def getIndex( self ):
		return self.p__index

	def getOwner( self ):
		return self.p__owner

	def getPriority( self ):
		return self.p__priority

	def getTTW( self ):
		return self.p__TTW

	def getTTL( self ):
		return self.p__TTL

	# Refresh - let the contender know it hasn't been forgotten
	def refresh( self ):
		self.p__last_update_ts = int( time.time() )

	# Let the contender know it is now the lock owner
	def youAreTheOwner( self ):
		if not self.p__am_owner:
			self.p__last_update_ts = int( time.time() )
			self.p__obtain_ts = int( time.time() )
			self.p__am_owner = 1

	# am I the owner?
	def isOwner( self ):
		return self.p__am_owner

	# function returns a value suitable for sending out a socket
	def streamOut( self ):
		priority = pack( "!B", self.p__priority )

		TTL = pack( "!H", self.p__TTL )

		TTW = pack( "!H", self.p__TTW )

		index = pack( "!B", len( self.p__index ) )
		index+= self.p__index

		owner = pack( "!B", len( self.p__owner ) )
		owner+= self.p__owner

		am_owner = pack( "!B", self.isOwner() )

		retval = priority + TTL + TTW + index + owner + am_owner

		return retval


	# Should I be deleted?
	def deletable( self ):
		if self.isOwner():
			return ( int( time.time() ) - self.p__last_update_ts ) > self.p__TTL
		else:
			return ( int( time.time() ) - self.p__last_update_ts ) > self.p__TTW

	# Object comparison
	def __lt__( self, other ):
		if type( other ) is not contender:
			return 0

		if self.p__index == other.getIndex() and \
		self.p__key == other.getKey() and \
		self.p__owner == other.getOwner() and \
		self.p__priority < other.getPriority():
			return 1
		else:
			return 0

	def __gt__( self, other ):
		if type( other ) is not contender:
			return 0

		if self.p__index == other.getIndex() and \
		self.p__key == other.getKey() and \
		self.p__owner == other.getOwner() and \
		self.p__priority > other.getPriority():
			return 1
		else:
			return 0

	def __eq__( self, other ):
		if type( other ) is not contender:
			return 0

		if self.p__index == other.getIndex() and \
		self.p__key == other.getKey() and \
		self.p__owner == other.getOwner():
			return 1
		else:
			return 0

	def __ne__( self, other ):
		if type( other ) is not contender:
			return 0

		if self == other:
			return 0
		else:
			return 1

	# Conversion to a string
	def __repr__( self ):
		if self.isOwner():
			seconds = self.p__TTL - ( int( time.time() ) - self.p__last_update_ts )
		else:
			seconds = self.p__TTW - ( int( time.time() ) - self.p__last_update_ts )
		
		return "Index: " + self.p__index + " " + \
			   "Key: " + self.p__key + " " + \
			   "Owner: " + self.p__owner + " " + \
			   "Deletable in: " + str( seconds ) + " seconds"
