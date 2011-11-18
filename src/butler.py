import threading, types, socket
import keyList, indexList, contenderList, contender, accountant
from roster import roster
from ownerlist import OwnerList
from struct import pack, unpack

class disconnectedError( Exception ):
	pass

class butler( object ):
	commands = { 
		0x1 : "WHOOWNS", 	"WHOOWNS" 	: 0x1,
		0x2 : "GIMME", 	"GIMME" 	: 0x2,
		0x3 : "CONTLOC", 	"CONTLOC" 	: 0x3, 
		0x4 : "RENEW", 	"RENEW" 	: 0x4,
		0x5 : "RELSPEC", 	"RELSPEC" 	: 0x5,
		0x6 : "RELALL", 	"RELALL" 	: 0x6,
		0x7 : "SHOWCONT", "SHOWCONT" 	: 0x7,
		0x8 : "STATS", 	"STATS" 	: 0x8
	}

	# Initialization - expects a keylist and a roster to be passed in
	def __init__( self, masterKL, ac, rost, owner_list ):

		# Check for the master Key List
		if type( masterKL ) is not keyList.keyList:
			raise TypeError, "Invalid masterKL"

		# Check to make sure ac is an accoutant
		if type( ac ) is not accountant.accountant:
			raise TypeError, "Invalid ac"

		if type( owner_list ) is not OwnerList:
			raise TypeError, "Invalid owner_list"

		if type( rost ) is not roster:
			raise TypeError, "Invalid roster"

		self.p__masterKL = masterKL
		self.p__ac = ac
		self.p__owner_list = owner_list
		self.p__rost = rost
	
	def getCommand( self, dataStream ):
		try:
			command = dataStream.recv( 1 )
		except:
			raise disconnectedError
		if not command:
			raise disconnectedError
		command = int( unpack( "!B", command )[0] )

		return command

	def getkey( self, dataStream ):
		try:
			kLen = dataStream.recv( 1 )
		except:
			raise disconnectedError
		if not kLen:
			raise disconnectedError
		kLen = int( unpack( "!B", kLen )[0] )

		try:
			key = dataStream.recv( kLen )
		except:
			raise disconnectedError
		if not key:
			raise disconnectedError

		unpackString = "!" + `kLen` + "s"
		key = unpack( unpackString, key )[0]

		return key

	def getindex( self, dataStream ):
		try:
			index_listen = dataStream.recv( 1 )
		except:
			raise disconnectedError

		if not index_listen:
			raise disconnectedError
		index_listen = int( unpack( "!B", index_listen )[0] )

		try:
			index = dataStream.recv( index_listen )
		except:
			raise disconnectedError
		if not index:
			raise disconnectedError

		unpackString = "!" + `index_listen` + "s"
		index = unpack( unpackString, index )[0]

		return index

	def getowner( self, dataStream ):
		try:
			oLen = dataStream.recv( 1 )
		except:
			raise disconnectedError

		if not oLen:
			raise disconnectedError
		oLen = int( unpack( "!B", oLen )[0] )

		try:
			owner = dataStream.recv( oLen )
		except:
			raise disconnectedError

		if not owner:
			raise disconnectedError
		unpackString = "!" + `oLen` + "s"
		owner = ''.join( unpack( unpackString, owner ) )

		return owner

	def getTTL( self, dataStream ):
		try:
			TTL = dataStream.recv( 2 )
		except:
			raise disconnectedError

		if not TTL:
			raise disconnectedError
		TTL = int( unpack( "!H", TTL )[0] )

		return TTL

	def getTTW( self, dataStream ):
		try:
			TTW = dataStream.recv( 2 )
		except:
			raise disconnectedError
			
		if not TTW:
			raise disconnectedError
		TTW = int( unpack( "!H", TTW )[0] )

		return TTW

	def getPriority( self, dataStream ):
		try:
			priority = dataStream.recv( 1 )
		except:
			raise disconnectedError

		if not priority:
			raise disconnectedError
		priority = int( unpack( "!B", priority )[0] )

		return priority


	# This is where the action is
	def executeCommand( self, dataStream ):
		if type( dataStream ) is not socket.socket:
			raise TypeError, "Data must come from a pipe"

		# Get command from the dataStream
		command = self.getCommand( dataStream )

		if not self.commands.has_key( command ):
			self.p__ac.increment( "unknownCommands" )
			raise disconnectedError, "Unknown command: " + command

		# Make sure we have the number representation
		if type( command ) == str:
			command = self.getCommand[command]

		self.p__rost.register()

		try:
			# Now we need send control to appropriate function
			if command == self.commands["WHOOWNS"]:
				self.whoOwns( dataStream )

			elif command == self.commands["GIMME"]: 
				self.gimme( dataStream )

			elif command == self.commands["CONTLOC"]:
				self.contLoc( dataStream )

			elif command == self.commands["RENEW"]:
				self.renew( dataStream )

			elif command == self.commands["RELSPEC"]:
				self.relSpec( dataStream )

			elif command == self.commands["RELALL"]:
				self.relAll( dataStream )

			elif command == self.commands["SHOWCONT"]:
				self.showCont( dataStream )

			elif command == self.commands["STATS"]:
				self.stats( dataStream )
		except:
			self.p__rost.unregister()
			raise

		self.p__rost.unregister()

	def whoOwns( self, dataStream ):
		self.p__ac.increment( "ownerLookups" )
		key = self.getkey( dataStream )
		index = self.getindex( dataStream )

		continueFlag = 1
		retval = None

		# Do we have the key in the master key list?
		if continueFlag:
			self.p__masterKL.lock()
			index_list = self.p__masterKL.find( key )
			if index_list is None:
				continueFlag = 0
			self.p__masterKL.unlock()

		# Do we have the index in the index list?
		if continueFlag:
			index_list.lock()
			contender_list = index_list.find( index )
			if contender_list is None:
				continueFlag = 0
			index_list.unlock()

		# What about the contender?
		if continueFlag:
			contender_list.lock()
			contender = contender_list.getOwner()

			contender_list.unlock()

			if contender is not None:
				retval = contender.getOwner()

		if retval is not None:
			packstring = "!" + str( len( retval ) ) + "s"
			dataStream.send( pack( "!B", len( retval ) ) )
			dataStream.send( pack( packstring, retval ) )
		else:
			dataStream.send( pack( "!B", 0 ) )

	def gimme( self, dataStream ):
		self.p__ac.increment( "lockRequests" )
		key = self.getkey( dataStream )
		index = self.getindex( dataStream )
		owner = self.getowner( dataStream )
		TTL = self.getTTL( dataStream )
		TTW = self.getTTW( dataStream )
		priority = self.getPriority( dataStream )

		self.p__masterKL.lock()
		index_list = self.p__masterKL.setdefault( key )
		self.p__masterKL.unlock()

		index_list.lock()
		contender_list = index_list.setdefault( index )
		index_list.unlock()

		# Add the contender
		c = contender.contender( key = key, 
								 index = index, 
								 owner = owner,
								 TTL = TTL,
								 TTW = TTW,
								 priority = priority )
		contender_list.lock()
		retval = contender_list.add( c )
		contender_list.unlock()

		dataStream.send( pack( "!H", retval & 0xffff ) )


	def contLoc( self, dataStream ):
		self.p__ac.increment( "contenderLookups" )
		key = self.getkey( dataStream )
		index = self.getindex( dataStream )
		owner = self.getowner( dataStream )
		
		# Do we have the key in the master key list?
		self.p__masterKL.lock()
		index_list = self.p__masterKL.setdefault( key )
		self.p__masterKL.unlock()

		# Do we have the index in the index list?
		index_list.lock()
		contender_list = index_list.setdefault( index )
		index_list.unlock()

		# Where is this particular contender?
		c = contender.contender( key = key, 
							 index = index, 
							 owner = owner )
		contender_list.lock()
		retval = contender_list.getPosition( c, add = 1 )
		contender_list.unlock()

		dataStream.send( pack( "!H", retval & 0xffff ) )


	def renew( self, dataStream ):
		self.p__ac.increment( "lockRenewals" )
		key = self.getkey( dataStream )
		index = self.getindex( dataStream )
		owner = self.getowner( dataStream )

		continueFlag = 1
		retval = 0

		# Do we have the key in the master key list?
		self.p__masterKL.lock()
		index_list = self.p__masterKL.find( key )
		if index_list is None:
			continueFlag = 0
		self.p__masterKL.unlock()

		# Do we have the index in the index list?
		if continueFlag:
			index_list.lock()
			contender_list = index_list.find( index )
			if contender_list is None:
				continueFlag = 0
			index_list.unlock()

		# Where is this particular contender?
		if continueFlag:
			c = contender.contender( key = key, 
								 index = index, 
								 owner = owner)
			contender_list.lock()
			retval = contender_list.renew( c )
			contender_list.unlock()

		dataStream.send( pack( "!H", retval & 0xffff ) )

	def relSpec( self, dataStream ):
		self.p__ac.increment( "specificReleases" )
		key = self.getkey( dataStream )
		index = self.getindex( dataStream )
		owner = self.getowner( dataStream )

		retval = 0

		if index != '*':
			retval = self.p__killContender( key, index, owner )

		# The index is a '*', do the search through the owner list
		else:
			self.p__owner_list.lock()
			data = self.p__owner_list.getData( owner )
			self.p__owner_list.unlock()

			continueFlag = 1

			if data is None:
				continueFlag = 0

			if continueFlag:
				data.lock()
				cont_list = data.getList()
				data.unlock()

				for item in cont_list:
					if item.getKey() == key:
						retval += self.p__killContender( 
							item.getKey(), 
							item.getIndex(), 
							item.getOwner() )

		dataStream.send( pack( "!H", retval & 0xffff ) )


	def relAll( self, dataStream ):
		self.p__ac.increment( "generalReleases" )
		owner = self.getowner( dataStream )

		self.p__owner_list.lock()
		data = self.p__owner_list.getData( owner )
		self.p__owner_list.unlock()

		continueFlag = 1
		retval = 0

		if data is None:
			continueFlag = 0

		if continueFlag:
			data.lock()
			cont_list = data.getList()
			data.unlock()

			for item in cont_list:
				retval += self.p__killContender( 
					item.getKey(), 
					item.getIndex(), 
					item.getOwner() )


		dataStream.send( pack( "!H", retval & 0xffff ) )


	def showCont( self, dataStream ):
		self.p__ac.increment( "lockDumps" )
		key = self.getkey( dataStream )

		self.p__masterKL.lock()
		index_list = self.p__masterKL.find( key )
		self.p__masterKL.unlock()

		if index_list is None:
			dataStream.send( pack( "!H", 0 ) )
			return

		index_list.lock()

		total_contenders = 0
		contender_packed_data = []
		for contender_list in index_list.getList():
			contender_list.lock()
			val1, val2 = contender_list.streamOut()
			total_contenders += val1
			contender_packed_data.append( val2 )
			contender_list.unlock()

		index_list.unlock()

		dataStream.send( pack( "!H", total_contenders ) )
		dataStream.send( ''.join( contender_packed_data ) )

	def stats( self, dataStream ):
		self.p__ac.increment( "statRequests" )
		statdump = self.p__ac.statDump( self.p__owner_list )
		dataStream.send( statdump )
			

	def p__killContender( self, key, index, owner ):
		continueFlag = 1
		retval = 0

		# Do we have the key in the master key list?
		self.p__masterKL.lock()
		index_list = self.p__masterKL.find( key )
		if index_list is None:
			continueFlag = 0
		self.p__masterKL.unlock()

		# Do we have the index in the index list?
		if continueFlag:
			index_list.lock()
			contender_list = index_list.find( index )
			if contender_list is None:
				continueFlag = 0
			index_list.unlock()

		# Where is this particular contender?
		if continueFlag:
			c = contender.contender( key = key, 
								 index = index, 
								 owner = owner )
			contender_list.lock()
			retval = contender_list.release( c )
			contender_list.unlock()

		return retval
