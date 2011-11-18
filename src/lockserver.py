#!/usr/bin/python2.2

import keyList
import maid
import accountant
from roster import roster
from ownerlist import OwnerList

from clientHandler import clientHandler

import threading
import time
import socket

from select import select

PORTNUM = 8675
MAXCONQUEUE = 500
HOST = ''

readsocks = []

portsock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )

# Cause socket to be reusable
portsock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )

bound = 0
while( not bound ):
	try:
		portsock.bind( ( HOST, PORTNUM ) )
	except socket.error:
		print "Waiting to bind."
		time.sleep( 5 )
	else:
		print "Bound to port " + `PORTNUM`
		bound = 1


portsock.listen( MAXCONQUEUE )

readsocks.append( portsock )

import os
import sys

#if os.fork():
#	print "Lockserver appears to have started successfully"
#	sys.stdin.close()
#	sys.stdout.close()
#	sys.stderr.close()
#	os._exit( 0 ) # Parent should die
#
#os.setsid()
#os.umask( 0 )
#sys.stdin.close()
#sys.stdout.close()
#sys.stderr.close()

owner_list = OwnerList()

masterKL = keyList.keyList( owner_list = owner_list )
lew = accountant.accountant()

rost = roster()

m = maid.maid( masterKL = masterKL, 
			   ac = lew, 
			   owner_list = owner_list, 
			   rost = rost )
m.start()

import traceback

while 1:
	readables, writeables, exceptions = select( readsocks, [], [] )
	for sockobj in readables:
		newsock, address = sockobj.accept()
		lew.increment( "acceptedConnections" )
		c = clientHandler( masterKL = masterKL, 
						   sock = newsock,
						   ac = lew,
						   rost = rost, 
						   owner_list = owner_list )
		c.start()
