import time, threading
from struct import pack
from ownerlist import OwnerList

class accountant( object ):
	def __init__( self, active = 1 ):
		self.startTS = time.time()
		self.lockRequests = 0
		self.unknownCommands = 0
		self.ownerLookups = 0
		self.contenderLookups = 0
		self.lockRenewals = 0
		self.specificReleases = 0
		self.generalReleases = 0
		self.lockDumps = 0
		self.statRequests = 0

		self.acceptedConnections = 0
		self.disallowedConnections = 0
		self.tooBusyConnections = 0
		
		self.activeConnections = 0

		self.active = active

		self.mutex = threading.Lock()

	def increment( self, item ):
		if not self.active:
			return

		if getattr( self, item, None ) == None:
			return None

		self.mutex.acquire()
		setattr( self, item, getattr( self, item ) + 1 )
		self.mutex.release()

		return

	def decrement( self, item ):
		if not self.active:
			return

		if item != "activeConnections": 
			return

		self.mutex.acquire()
		setattr( self, item, getattr( self, item ) - 1 )
		self.mutex.release()

		return

	def getStats( self, owner_list ):
		retval = []	

		# 1) uptime
		retval.append( int( time.time() - self.startTS ) )

		# 2) Unknown commands
		retval.append( self.unknownCommands )

		# 3) Owner Lookups
		retval.append( self.ownerLookups )

		# 4) Lock requests
		retval.append( self.lockRequests )

		# 5) Contender Lookups
		retval.append( self.contenderLookups )

		# 6) Lock renewal requests
		retval.append( self.lockRenewals )

		# 7) Specific lock releases
		retval.append( self.specificReleases )

		# 8) General lock releases
		retval.append( self.generalReleases )

		# 9) Lock dump requests
		retval.append( self.lockDumps )

		# 10) Statistics requests
		retval.append( self.statRequests )

		# 11) Accepted connections
		retval.append( self.acceptedConnections )

		# 12) Connections rejected due to not being in the hosts file
		retval.append( self.disallowedConnections )

		# 13) Connections rejected due to the server being too busy
		retval.append( self.tooBusyConnections )

		# Calculate number of owner/nonowner contenders
		owners = 0
		contenders = 0

		owner_list.lock()
		owners_list = owner_list.getOwners()
		owner_list.unlock()

		for owner in owners_list:
			owner_list.lock()
			data = owner_list.getData( owner )
			owner_list.unlock()

			if data is None:
				continue

			data.lock()
			lock_list = data.getList()
			data.unlock()

			for lock in lock_list:
				contenders += 1
				owners += lock.isOwner()

		# 14) Number of current lock owners
		retval.append( owners )

		# 15) Number of (non owner) contenders
		retval.append( contenders )

		# 16) active connections
		retval.append( self.activeConnections )

		return retval

	def statDump( self, owner_list ):
		retval = []
		if type( owner_list ) is not OwnerList:
			raise TypeError, "Expected an OwnerList instance"

		fourByteMask = 0xffffffff

		part = self.getStats( owner_list )

		# 1) uptime
		retval.append( pack( "!I", part[0] & fourByteMask ) )

		# 2) Unknown commands
		retval.append( pack( "!I", part[1] & fourByteMask ) )

		# 3) Owner Lookups
		retval.append( pack( "!I", part[2] & fourByteMask ) )

		# 4) Lock requests
		retval.append( pack( "!I", part[3] & fourByteMask ) )

		# 5) Contender Lookups
		retval.append( pack( "!I", part[4] & fourByteMask ) )

		# 6) Lock renewal requests
		retval.append( pack( "!I", part[5] & fourByteMask ) )

		# 7) Specific lock releases
		retval.append( pack( "!I", part[6] & fourByteMask ) )

		# 8) General lock releases
		retval.append( pack( "!I", part[7] & fourByteMask ) )

		# 9) Lock dump requests
		retval.append( pack( "!I", part[8] & fourByteMask ) )

		# 10) Statistics requests
		retval.append( pack( "!I", part[9] & fourByteMask ) )

		# 11) Accepted connections
		retval.append( pack( "!I", part[10] & fourByteMask ) )

		# 12) Connections rejected due to not being in the hosts file
		retval.append( pack( "!I", part[11] & fourByteMask ) )

		# 13) Connections rejected due to the server being too busy
		retval.append( pack( "!I", part[12] & fourByteMask ) )

		# 14) Number of current lock owners
		retval.append( pack( "!I", part[13] & fourByteMask ) )

		# 15) Number of (non owner) contenders
		retval.append( pack( "!I", part[14] & fourByteMask ) )

		# 16) active connections
		retval.append( pack( "!H", part[15] & 0xffff ) )

		return ''.join( retval )

	def stringDump( self, owner_list ):
		retval = []
		if type( owner_list ) is not OwnerList:
			raise TypeError, "Expected an OwnerList instance"

		fourByteMask = 0xffffffff

		part = self.getStats( owner_list )

		# 1) uptime
		retval.append( "Uptime: %s" % str( part[0] ) )

		# 2) Unknown commands
		retval.append( "Unknown commands: %s" % str( part[1] ) )

		# 3) Owner Lookups
		retval.append( "Owner lookups: %s" % str( part[2] ) )

		# 4) Lock requests
		retval.append( "Lock requests: %s" % str( part[3] ) )

		# 5) Contender Lookups
		retval.append( "Contender lookups: %s" % str( part[4] ) )

		# 6) Lock renewal requests
		retval.append( "Lock renewals: %s" % str( part[5] ) )

		# 7) Specific lock releases
		retval.append( "Specific lock releases: %s" % str( part[6] ) )

		# 8) General lock releases
		retval.append( "General lock releases: %s" % str( part[7] ) )

		# 9) Lock dump requests
		retval.append( "Lock dump requests: %s" % str( part[8] ) )

		# 10) Statistics requests
		retval.append( "Statistic requests: %s" % str( part[9] ) )

		# 11) Accepted connections
		retval.append( "Accepted connections: %s" % str( part[10] ) )

		# 12) Connections rejected due to not being in the hosts file
		retval.append( "Rejected hosts: %s" % str( part[11] ) )

		# 13) Connections rejected due to the server being too busy
		retval.append( "Too busy rejections: %s" % str( part[12] ) )

		# 14) Number of current lock owners
		retval.append( "Current lock owners: %s" % str( part[13] ) )

		# 15) Number of (non owner) contenders
		retval.append( "Total contenders: %s" % str( part[14] ) )

		# 16) active connections
		retval.append( "Active connections: %s" % str( part[15] ) )

		return "\n".join( retval )
