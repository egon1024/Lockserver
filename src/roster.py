import threading, time

class roster( object ):
	def __init__( self ):
		self.p__mutex = threading.Lock()
		self.p__activeCount = 0
		self.p__ready_to_clean = 0

	# This function is called by a butler when it wants to go do
	# some work
	def register( self ):
		while( 1 ):
			self.p__mutex.acquire()
			if self.p__ready_to_clean:
				self.p__mutex.release()
				time.sleep( 2 )
			else:
				self.p__activeCount += 1
				flag = 1
				self.p__mutex.release()
				break

	# Called by a butler having finished work
	def unregister( self ):
		self.p__mutex.acquire()
		self.p__activeCount -= 1
		self.p__mutex.release()

	def readyToClean( self ):
		self.p__mutex.acquire()
		self.p__ready_to_clean = 1
		self.p__mutex.release()

	def doneCleaning( self ):
		self.p__ready_to_clean = 0

	def getActiveCount( self ):
		return self.p__activeCount

	def getCleanStatus( self ):
		return self.p__ready_to_clean
