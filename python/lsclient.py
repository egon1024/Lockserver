## Python API to Lockserver
##
## Interface:
## =============================================================== ##
##
## Creating a new lock
## -------------------
## l = lsclient( 
##				 host = "hostname",
##				 port = portnumber,
##				 key = "key",
##				 index = "index",
##				 owner = "owner",
##				 ttl = ttl,
##				 ttw = ttw,
##				 priority = priority 
##			   )
##
## l = lsclient( host = "hostname", port = portnumber )
##
## l = lsclient()     # defaults to localhost:8675
##

## Changing internal lock variables
## --------------------------------
## You can set a lock's internal variables upon creation.
## l = lsclient(
##				 host = "hostname",
##				 port = portnumber,
##				 key = "key",
##				 index = "index",
##				 owner = "owner"
##			   )
##
## Or, you can redefine them at a later time.
## l = lsclient()			# created with default values
## l["key"] = "FlightInv"	# redefine lock's key
## l["index"] = 1234		# redefine lock's index
## l["owner"] = "hacker"	# redefine lock's owner
##
## WARNING!  You CANNOT redefine a lsclient's server/port if it
## is already connected to a lockserver.  You must first
## disconnect from the current connection before redefining
## connection variables.

## Connecting to the server
## ------------------------
## l.connect()	# use host:port defined under new()
## l.connect( host = "hostname", port = portnumber )
##
## NOTE: You must call connect manually.   A new lsclient will
## not create the connection.
##
## RETURN VALUES:
## -1 => tcp/ip connection error or unknown response from lockserver
##  0 => our IP address was rejected by locksvr
##  1 => SUCCESS
##  2 => locksvr too busy, rejected
## NOTE: l["connstatus"] is set to this return value also.
## NOTE: l["connected"] is 1 of connected, 0 otherwise.

## Disconnecting from the server
## -----------------------------
## l.disconnect()
##
## RETURN VALUES:
## 0 => Failed to disconnect properly
## 1 => SUCCESS

## Requesting a new lock
## ---------------------
## l.request()       # use values supplied with new()
## l.request( key = "key", index = "index", owner = "owner",
##			  ttl = ttl, ttw = ttw, priority = priority )
##
## RETURN VALUES:
## -1 => not connected, tcp/ip error
##  0 => locksvr is shutting down, no new locks
##  1 => SUCCESS _AND_ we got the lock w/o waiting
##  2 => SUCCESS but we're first in wait queue
##  x => SUCCESS but we're x-1 in wait queue

## Finding out a lock owner
## ------------------------
## l.lockowner()     # use values supplied with new()
## l.lockowner( key = "key", index = "index" )
##
## RETURN VALUES:
## -1 => not connected, tcp/ip error
##  str => name of lock owner
## -none- => no lock owner for key/index

## Finding queue location
## ----------------------
## l.queueloc()      # use values supplied with new()
## l.queueloc( key = "key", index = "index", owner = "owner" )
##
## RETURN VALUES:
## -1 => error, not connected, tcp/ip error
##  1 => has the lock
##  2 => first in wait queue
##  x => x-1 in wait queue

## Renewing a lock
## ---------------
## l.renew()         # use values supplied with new()
## l.renew( key = "key", index = "index", owner = "owner" )
##
## RETURN VALUES:
## -1 => error, not connected, tcp/ip error
##  0 => couldn't renew the lock
##  1 => SUCCESS

## Release a lock
## --------------
## l.release()       # use values supplied with new()
## l.release( key = "key", index = "index", owner = "owner" )
##
## RETURN VALUES:
## -1 => error, not connected, tcp/ip error
##  x => SUCCESS, return number of locks released

## Release owned locks
## -------------------
## l.releaseowned()  # use values supplied with new()
## l.releaseowned( owner = "owner" )
##
## RETURN VALUES:
## -1 => error, not connected, tcp/ip error
##  x => SUCCESS, return number of locks released

## Debugging
## ---------
## dictionary = l.statdump()        # peek at lockserver's stats

class lsclient:
	import types, time, socket

	defaultPriority =	3
	defaultTTL		=	600
	defaultTTW		=	30

	defaultHost		=	"localhost"
	defaultPort		=	8675

	wrongType = "wrongTypeError"

	def __init__( self, **args ):
		if args.has_key( "host" ) and \
		type( args["host"] ) == self.types.StringType:
			self.host = args["host"]
		elif args.has_key( "host" ):
			raise wrongType, "value for \"host\" was not a String"
		else:
			self.host = self.defaultHost

		if args.has_key( "port" ) and \
		( type( args["port"] ) == self.types.IntType or \
		  type( args["port"] ) == self.types.LongType ):
			self.port = args["port"]
		elif args.has_key( "port" ):
			raise wrongType, "value for \"port\" was not a valid type"
		else:
			self.port = self.defaultPort

		if args.has_key( "key" ) and \
		type( args["key"] ) == self.types.StringType:
			self.key = args["key"]
		elif args.has_key( "key" ):
			raise wrongType, "value for \"key\" was not a String"
		else:
			self.key = ""

		if args.has_key( "index" ) and \
		type( args["index"] ) == self.types.StringType:
			self.index = args["index"]
		elif args.has_key( "index" ):
			raise wrongType, "value for \"index\" was not a String"
		else:
			self.index = ""
			
		if args.has_key( "owner" ) and \
		type( args["owner"] ) == self.types.StringType:
			self.owner = args["owner"]
		elif args.has_key( "owner" ):
			raise wrongType, "value for \"owner\" was not a String"
		else:
			self.owner = ""

		if args.has_key( "ttl" ) and \
		( type( args["ttl"] ) == self.types.IntType or \
		  type( args["ttl"] ) == self.types.LongType ):
		  	self.ttl = args["ttl"]
		elif args.has_key( "port" ):
			raise wrongType, "value for \"ttl\" was not a valid type"
		else:
			self.ttl = self.defaultTTL

		if args.has_key( "ttw" ) and \
		( type( args["ttw"] ) == self.types.IntType or \
		  type( args["ttw"] ) == self.types.LongType ):
		  	self.ttw = args["ttw"]
		elif args.has_key( "port" ):
			raise wrongType, "value for \"ttw\" was not a valid type"
		else:
			self.ttw = self.defaultTTW

		if args.has_key( "priority" ) and \
		( type( args["priority"] ) == self.types.IntType or \
		  type( args["priority"] ) == self.types.LongType ):
		  	self.priority = args["priority"]
		elif args.has_key( "port" ):
			raise wrongType, "value for \"priority\" was not a valid type"
		else:
			self.priority = self.defaultPriority

		self.sockobj = None
		self.CONNSTATUS = 0

		self.commands = { 
						  "WHOOWNS" 	: 0x1,
						  "GIMME" 		: 0x2,
						  "CONTLOC" 	: 0x3, 
						  "RENEW" 		: 0x4,
						  "RELSPEC" 	: 0x5,
						  "RELALL" 		: 0x6,
						  "SHOWCONT"	: 0x7,
						  "STATS" 		: 0x8
						}

	def connect( self, **args ):
		if args.has_key( "host" ) and \
		type( args["host"] ) == self.types.StringType:
			self.host = args["host"]
		elif args.has_key( "owner" ):
			raise wrongType, "value for \"owner\" was not a String"

		if args.has_key( "port" ) and \
		( type( args["port"] ) == self.types.IntType or \
		  type( args["port"] ) == self.types.LongType ):
		  	self.port = args["port"]
		elif args.has_key( "port" ):
			raise wrongType, "value for \"priority\" was not a valid type"


		# Check to make sure port is something valid
		if type( self.port ) != self.types.IntType and \
		type( self.port ) != self.types.LongType:
			raise wrongType, "value for \"owner\" was not a String"

		if type( self.sockobj ) == self.socket.SocketType: 
			# Already connected
			return -1

		self.sockobj = socket( AF_INET, SOCK_STREAM )
		connected = self.sockobj.connect_ex( ( self.host, self.port ) )

		if not connected:
			self.sockobj = None
			return -1

		# If connected, get a response from the server
		response = unpack( "!B", self.sockobj.recv( 1 ) )[0]

		# response == 0: Our IP was rejected
		# response == 2: Server was too busy
		if response == 0 or \
		response == 2:
			self.sockobj.close()
			self.sockobj = None
			self.CONNSTATUS = response
			return response

		# Unknown response
		elif response != 1:
			self.sockobj.close()
			self.sockobj = None
			self.CONNSTATUS = -1
			return -1

		# Connected!
		elif response == 1:
			return 1

	def disconnect( self ):
		if type( self.sockobj ) == self.socket.SocketType:
			self.sockobj.close()
			self.sockobj = None
			self.CONNSTATUS = 0

			# Clean stuff out
			self.host = ""
			self.port = 0
			self.key = ""
			self.index = ""
			self.owner = ""
			self.ttl = 0
			self.ttw = 0
			self.priority = 0

			return 1
		else:
			return 0

	def connstatus( self ):
		return self.CONNSTATUS

	def connected( self ):
		if type( self.sockobj ) == self.socket.SocketType:
			return 1
		else:
			return 0

	def request( self, **args ):
		if args.has_key( "key" ) and \
		type( args["key"] ) == self.types.StringType:
			localkey = args["key"]
		elif args.has_key( "key" ):
			raise wrongType, "value for \"key\" was not a String"
		else:
			localKey = self.key

		if args.has_key( "index" ) and \
		type( args["index"] ) == self.types.StringType:
			localIndex = args["index"]
		elif args.has_key( "index" ):
			raise wrongType, "value for \"index\" was not a String"
		else:
			localIndex = self.index
			
		if args.has_key( "owner" ) and \
		type( args["owner"] ) == self.types.StringType:
			localOwner = args["owner"]
		elif args.has_key( "owner" ):
			raise wrongType, "value for \"owner\" was not a String"
		else:
			localOwner = self.owner

		if args.has_key( "ttl" ) and \
		( type( args["ttl"] ) == self.types.IntType or \
		  type( args["ttl"] ) == self.types.LongType ):
		  	localTTL = args["ttl"]
		elif args.has_key( "port" ):
			raise wrongType, "value for \"ttl\" was not a valid type"
		else:
			localTTL = self.ttl

		if args.has_key( "ttw" ) and \
		( type( args["ttw"] ) == self.types.IntType or \
		  type( args["ttw"] ) == self.types.LongType ):
		  	localTTW = args["ttw"]
		elif args.has_key( "port" ):
			raise wrongType, "value for \"ttw\" was not a valid type"
		else:
			localTTW = self.ttw

		if args.has_key( "priority" ) and \
		( type( args["priority"] ) == self.types.IntType or \
		  type( args["priority"] ) == self.types.LongType ):
		  	localPriority = args["priority"]
		elif args.has_key( "port" ):
			raise wrongType, "value for \"priority\" was not a valid type"
		else:
			localPriority = self.priority

		if not self.connected() or self.connstatus() != 1:
			return -1

		# Build up our request lock command
		twoByteMask = 0xffff
		fourByteMask = 0xffffffff
		
		# Command
		transmission += pack( "!B", self.command[ "GIMME" ] )

		# Key
		transmission += pack( "!B", len( localKey ) )
		packString = "!" + `len( localKey )` + "s"
		transmission += pack( packString, localKey )

		# Index
		transmission += pack( "!B", len( localIndex ) )
		packString = "!" + `len( localIndex )` + "s"
		transmission += pack( packString, localIndex )

		# Owner
		transmission += pack( "!B", len( localOwner ) )
		packString = "!" + `len( localOwner )` + "s"
		transmission += pack( packString, localOwner )

		# TTL
		transmission += pack( "!H", localTTL )

		# TTW
		transmission += pack( "!H", localTTW )

		# Priority
		transmission += pack( "!B", localPriority )

		bytesSent = self.sockobj.send( transmission )
		if( bytesSent < len( transmission ) ):
			# Do some kind of error handling dance here
			pass
