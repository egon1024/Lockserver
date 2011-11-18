import threading, traceback, socket, sys
import butler
import accountant
import keyList
from roster import roster
from ownerlist import OwnerList
from socket import AF_INET, SOCK_STREAM
from select import select
from struct import pack, unpack
from butler import disconnectedError

class clientHandler( threading.Thread ):
	def __init__( self, masterKL, sock, rost, ac, owner_list ):
		# Check for the master Key List
		if type( masterKL ) is not keyList.keyList:
			raise TypeError, "Invalid masterKL"

		# check to make sure sock is a socket
		if type( sock ) is not socket.socket:
			raise TypeError, "Invalid sock"

		# Check to make sure ac is an accountant
		if type( ac ) is not accountant.accountant:
			raise TypeError, "Invalid ac"

		if type( rost ) is not roster:
			raise TypeError, "Invalid rost"

		if type( owner_list ) is not OwnerList:
			raise TypeError, "Invalid owner_list"

		self.masterKL = masterKL
		self.sock = sock
		self.ac = ac
		self.rost = rost
		self.owner_list = owner_list

		threading.Thread.__init__( self )

	def run( self ):
		# First thing - we need to welcome the new client
		self.sock.send( pack( "!B", 1 ) )

		self.ac.increment( "activeConnections" )

		# We'll need a butler, let's appropriate one
		b = butler.butler( masterKL = self.masterKL,
						   rost = self.rost,
						   owner_list = self.owner_list,
						   ac = self.ac )
		
		readsocks = [ self.sock ]

		while 1:
			try:
				readables, writeables, exceptions = select( readsocks, [], [] )
				s = readables[0]
				b.executeCommand( s )
			except disconnectedError:
				self.ac.decrement( "activeConnections" )
				self.sock.close()
				break
#			except:
#				tracebackLog = '/home/admin/lockserver.traceback.log'
#				fileHandle = open( tracebackLog, 'w+' );
#				if hasattr( sys, "last_type" ):
#					traceback.print_exception( sys.last_type, 
#											   sys.last_value, 
#											   sys.last_traceback, 
#											   file = fileHandle )
#				else:
#					fileHandle.write( "Unknown exception\n" )
#					fileHandle.write( str( dir( sys ) ) )
#					fileHandle.write( "\n\n" )
#				fileHandle.close()
#				break
