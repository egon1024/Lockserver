import threading
from contender import contender
from ownerlist import OwnerList

class contenderList( object ):
	def __init__( self, owner_list = None ):
		if type( owner_list ) is not OwnerList:
			raise TypeError, "Invalid owner_list"

		self.p__mutex = threading.Lock()
		self.p__contenders = []
		self.p__owner_list = owner_list

	def __len__( self ):
		self.p__expireStuff()
		return len( self.p__contenders )

	def lock( self ):
		self.p__mutex.acquire()

	def unlock( self ):
		self.p__mutex.release()

	def getOwner( self ):
		if len( self ) == 0:
			return None
		else:
			return self.p__contenders[0]

	def add( self, cont ):
		if type( cont ) is not contender:
			raise TypeError, "Invalid cont"

		self.p__expireStuff()

		self.p__owner_list.lock()
		own_data = self.p__owner_list.setdefault( cont.getOwner() )
		self.p__owner_list.unlock()
		own_data.lock()

		# Handle the case where there are no pre-existing contenders.
		# In this event, just add the contender as the owner.
		#
		if not self.p__contenders:
			own_data.add( cont )
			self.p__contenders.append( cont )
			own_data.unlock()
			cont.youAreTheOwner()
			return 1

		# If the contender already exists as the owner, just refresh it.
		#
		elif self.p__contenders[0] == cont:
			item = self.p__contenders[0]
			own_data.unlock()
			item.refresh()
			return 1

		# If none of the above cases match the current situation, iterate
		# through all the non-owning contenders and find out (1) if the
		# contender already exists in the list, or (2) where the new
		# contender should be inserted.
		#
		else:
			new_loc = 1
			for i in range( 1, len( self.p__contenders ) ):
				item = self.p__contenders[i]
				if item == cont:
					own_data.unlock()
					item.refresh()
					return i + 1

				if item.getPriority() <= cont.getPriority():
					new_loc = i + 1

			own_data.add( cont )
			self.p__contenders.insert( new_loc, cont )
			own_data.unlock()

			return new_loc + 1

	def getPosition( self, cont, add = 0 ):
		if add:
			return self.add( cont )

		if type( cont ) is not contender:
			raise TypeError, "Invalid cont"

		self.p__expireStuff()

		for i in range( len( self.p__contenders ) ):
			item = self.p__contenders[i]
			if item == cont:
				return i + 1

	def renew( self, cont ):
		if type( cont ) is not contender:
			raise TypeError, "Invalid cont"

		self.p__expireStuff()

		retval = 0
		for item in self.p__contenders:
			if item == cont:
				item.refresh()
				retval = 1
				break

		return retval

	def release( self, cont ):
		if type( cont ) is not contender:
			raise TypeError, "Invalid cont"

		self.p__owner_list.lock()
		own_data = self.p__owner_list.setdefault( cont.getOwner() )
		self.p__owner_list.unlock()

		retval = 0
		for i in range( len( self.p__contenders ) ):
			item = self.p__contenders[i]
			if item == cont:
				retval = 1
				own_data.lock()
				own_data.remove( cont )
				del self.p__contenders[i]
				own_data.unlock()
				break

		self.p__expireStuff()

		return retval

	def streamOut( self ):
		self.p__expireStuff()

		retval = []

		how_many = len( self.p__contenders )
		for item in self.p__contenders:
			retval.append( item.streamOut() )

		return ( how_many, ''.join( retval ) )

	def p__expireStuff( self ):
		retval = 0

		indexes = range( len( self.p__contenders ) )
		indexes.reverse()

		for i in indexes:
			item = self.p__contenders[i]
			if item.deletable():
				self.p__owner_list.lock()
				own_data = self.p__owner_list.setdefault( item.getOwner() )
				self.p__owner_list.unlock()
				own_data.lock()
				own_data.remove( item )
				del self.p__contenders[i]
				own_data.unlock()
				retval += 1

		if self.p__contenders:
			self.p__contenders[0].youAreTheOwner()

		return retval

	# This is mostly like p__expireStuff, but without the locking as it
	# only gets called by the maid
	def cleanThySelf( self ):
		retval = 0

		indexes = range( len( self.p__contenders ) )
		indexes.reverse()

		for i in indexes:
			item = self.p__contenders[i]
			if item.deletable():
				own_data = self.p__owner_list.setdefault( item.getOwner() )
				own_data.remove( item )
				del self.p__contenders[i]
				retval += 1

		if self.p__contenders:
			self.p__contenders[0].youAreTheOwner()

		return retval


	def stringLockDump( self ):
		retval = []
		for item in self.p__contenders:
			s = "        "
			s += item.getOwner()
			if item.isOwner():
				s+= " *"
			retval.append( s )

		return retval
