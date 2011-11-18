import threading
from ownerdata import OwnerData

class OwnerList( object ):
	def __init__( self ):
		self.p__map = {}
		self.p__mutex = threading.Lock()

	def stringLockDump( self ):
		retval = []
		for ( owner, data ) in self.p__map.items():
			retval.append( owner + ":" )
			retval += data.stringLockDump()

		return retval
	
	def setdefault( self, owner ):
		tmp = OwnerData( owner )
		return self.p__map.setdefault( owner, tmp )

	def lock( self ):
		self.p__mutex.acquire()

	def unlock( self ):
		self.p__mutex.release()
	
	def getData( self, owner ):
		return self.p__map.get( owner, None )

	def getOwners( self ):
		return self.p__map.keys()

	def cleanThySelf( self ):
		retval = 0
		for ( key, data ) in self.p__map.items():
			if len( data ) == 0:
				del self.p__map[key]
				retval += 1

		return retval
