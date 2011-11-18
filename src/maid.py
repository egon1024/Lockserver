import threading, time, os, syslog
from roster import roster
from keyList import keyList
from accountant import accountant
from ownerlist import OwnerList
from mx import DateTime

class TooBusyError( Exception ):
	pass

class maid( threading.Thread ):

	def __init__( self, masterKL, ac, owner_list, rost ):

		# Check for the master Key List
		if type( masterKL ) is not keyList:
			raise TypeError, "Invalid masterKL"

		# Check for the roster
		if type( rost ) is not roster:
			raise TypeError, "Invalid rost"

		# Check for the accountant
		if type( ac ) is not accountant:
			raise TypeError, "Invalid ac"

		# Check for the owner list
		if type( owner_list ) is not OwnerList:
			raise TypeError, "Invalid owner_list"


		self.p__last_run = DateTime.now()
		self.p__need_to_run = 0

		self.p__master_kl = masterKL
		self.p__accountant = ac
		self.p__owner_list = owner_list
		self.p__rost = rost

		threading.Thread.__init__( self )

	def run( self ):
		trigger_file = "/tmp/.runmaid"
		stat_file = "/tmp/.lockstat"
		dump_file = "/tmp/.lockdump"
		owner_file = "/tmp/.ownerdump"
		while( 1 ):
			# Provide lock statistics, if appropriate
			if os.path.exists( stat_file ) and \
			not os.path.getsize( stat_file ) and \
			not os.path.islink( stat_file ) and \
			os.access( stat_file, os.W_OK ):
				f = open( stat_file, "w" )
				data = self.p__accountant.stringDump( self.p__owner_list )
				if data:
					f.write( data )
					f.write( "\n" )
				f.close()

			# Provide lock dump, if appropriate
			if os.path.exists( dump_file ) and \
			not os.path.getsize( dump_file ) and \
			not os.path.islink( dump_file ) and \
			os.access( dump_file, os.W_OK ):
				f = open( dump_file, "w" )
				data = "\n".join( self.p__master_kl.stringLockDump() )
				if data:
					f.write( data )
					f.write( "\n" )
				f.close()

			# Provide owner dump, if appropriate
			if os.path.exists( owner_file ) and \
			not os.path.getsize( owner_file ) and \
			not os.path.islink( owner_file ) and \
			os.access( owner_file, os.W_OK ):
				f = open( owner_file, "w" )
				data =  "\n".join( self.p__owner_list.stringLockDump() ) 
				if data:
					f.write( data )
					f.write( "\n" )
				f.close()

			# Run the maid today?
			t = DateTime.now()
			if DateTime.Date( t.year, t.month, t.day ) > self.p__last_run and \
			t.hour >= 6:
				self.p__need_to_run = 1

			# Another test - if "trigger_file" exists, we should clean
			if os.path.exists( trigger_file ):
				self.p__need_to_run = 1
				try:
					os.unlink( trigger_file )
				except:
					pass

			if self.p__need_to_run == 1:
				self.p__need_to_run = 0
				try: 
					self.doClean()
					self.p__last_run = DateTime.now()
				except TooBusyError:
					self.p__need_to_run = 1
					import syslog
					syslog.openlog( "lockserver", 
									syslog.LOG_PID, 
									syslog.LOG_DAEMON )
					syslog.syslog( syslog.LOG_WARNING, 
								   "Lockserver too active to clean" )
					syslog.closelog()

			time.sleep( 10 )

	def doClean( self ):
		max_tries = 10

		self.p__rost.readyToClean()
		
		tries = 0
		while tries < max_tries and self.p__rost.getActiveCount() > 0:
			time.sleep( 1 )
			tries += 1 

		if self.p__rost.getActiveCount() > 0:
			self.p__rost.doneCleaning()
			raise TooBusyError

		starttime = time.time()

		# Now we do the cleaning
		cleancount = self.p__master_kl.cleanThySelf()
		cleancount+= self.p__owner_list.cleanThySelf()

		self.p__rost.doneCleaning()
		t = time.time() - starttime

		syslog.openlog( "lockserver",
						syslog.LOG_PID,
						syslog.LOG_DAEMON )
		syslog.syslog( syslog.LOG_NOTICE,
					   "Maid took %f seconds to clean %d nodes" % 
					   	( t, cleancount ) )
		syslog.closelog()
