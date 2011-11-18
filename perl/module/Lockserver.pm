## $Id: Lockserver.pm,v 1.1.1.1 2004/10/28 18:24:04 egon Exp $

## :set ts=2
##
## Perl API to Lockserver
## Usage: See the included "locktest.pl" script
##
## Interface:
## =============================================================== ##
##
## Creating a new lock
## -------------------
## $l = new Lockserver($host,$port,$key,$index,$owner,
##                     $ttl,$ttw,$priority);
##
## $l = new Lockserver($host,$port);
##
## $l = new Lockserver();     # defaults to localhost:8675
##
## RETURN VALUES:
## returns a new lock

## Changing internal lock variables
## --------------------------------
## You can set a lock's internal variables upon creation.
## $l = new Lockserver($host,$port,$key,$index,$owner);
##
## Or, you can redefine them at a later time.
## $l = new Lockserver();   # created with default values
## $l->key("FlightInv");    # redefine lock's key
## $l->index(1234);         # redefine lock's index
## $l->owner("hacker");     # redefine lock's owner
##
## WARNING!  You CANNOT redefine a lock's server/port if it
## is already connected to a lockserver.  You must first
## disconnect from the current connection before redefining
## connection variables.

## Connecting to the server
## ------------------------
## $l->connect;               # use host:port defined under new()
## $l->connect($otherserver,$otherport);
##
## NOTE: You must call connect manually.  new Lockserver() will
## not create the connection.
##
## RETURN VALUES:
## -1 => tcp/ip connection error or unknown response from lockserver
##  0 => our IP address was rejected by locksvr
##  1 => SUCCESS
##  2 => locksvr too busy, rejected
## NOTE: $l->connstatus is set to this return value also.
## NOTE: $l->connected is 1 of connected, 0 otherwise.

## Disconnecting from the server
## -----------------------------
## $l->disconnect;
##
## RETURN VALUES:
## 0 => Failed to disconnect properly
## 1 => SUCCESS

## Requesting a new lock
## ---------------------
## $l->request;       # use values supplied with new()
## $l->request($key,$ind,$own,$ttl,$ttw,$pr);
##
## RETURN VALUES:
## -1 => not connected, tcp/ip error
##  0 => locksvr is shutting down, no new locks
##  1 => SUCCESS _AND_ we got the lock w/o waiting
##  2 => SUCCESS but we're first in wait queue
##  x => SUCCESS but we're x-1 in wait queue

## Finding out a lock owner
## ------------------------
## $l->lockowner;     # use values supplied with new()
## $l->lockowner($key,$index);
##
## RETURN VALUES:
## -1 => not connected, tcp/ip error
##  str => name of lock owner
## -none- => no lock owner for $key/$index

## Finding queue location
## ----------------------
## $l->queueloc;      # use values supplied with new()
## $l->queueloc($key,$index,$owner);
##
## RETURN VALUES:
## -1 => error, not connected, tcp/ip error
##  1 => has the lock
##  2 => first in wait queue
##  x => x-1 in wait queue

## Renewing a lock
## ---------------
## $l->renew;         # use values supplied with new()
## $l->renew($key,$index,$owner);
##
## RETURN VALUES:
## -1 => error, not connected, tcp/ip error
##  0 => couldn't renew the lock
##  1 => SUCCESS

## Release a lock
## --------------
## $l->release;       # use values supplied with new()
## $l->release($key,$index,$owner);
##
## RETURN VALUES:
## -1 => error, not connected, tcp/ip error
##  x => SUCCESS, return number of locks released

## Release owned locks
## -------------------
## $l->releaseowned;  # use values supplied with new()
## $l->releaseowned($owner);
##
## RETURN VALUES:
## -1 => error, not connected, tcp/ip error
##  x => SUCCESS, return number of locks released

## Debugging
## ---------
## $double_hashref = $l->queuedump($key); # peek at lock queues
## $hashref = $l->statdump;        # peek at lockserver's stats

package Lockserver;
use strict;
use IO::Socket;
#use warnings;

##
## constructor
##
sub new {
	my $proto    = shift;
	my $class    = ref($proto) || $proto;
	my $self     = {};
	my $host     = shift;
	my $port     = shift;
	my $key      = shift;
	my $index    = shift;
	my $owner    = shift;
	my $ttl      = shift;
	my $ttw      = shift;
	my $priority = shift;

	# the Lockserver attributes
	$self->{SERVER}     = undef; # lockserver host
	$self->{PORT}       = undef; # lockserver host's port
	$self->{CONNECTED}  = 0;     # 0=>not connected, 1=>connected
	$self->{CONNECTION} = undef; # socket file descriptor
	$self->{CONNSTATUS} = undef; # conn response from lockserver
	$self->{KEY}        = undef; # table
	$self->{INDEX}      = undef; # row id
	$self->{OWNER}      = undef; # username
	$self->{TTW}        = undef; # queue wait life time
	$self->{TTL}        = undef; # lock life time
	$self->{PRIORITY}   = undef; # lock priority

	if ($host) {
		$self->{SERVER} = $host;
	} else {
		$self->{SERVER}		= "localhost";
	}
	if ($port) {
		$self->{PORT}			= $port;
	} else {
		$self->{PORT}			= 8675;
	}
	if ($key) {
		$self->{KEY}			= $key;
	}
	if ($index) {
		$self->{INDEX}		= $index;
	}
	if ($owner) {
		$self->{OWNER}		= $owner;
	}
	if ($ttl) {
		$self->{TTL} 			= $ttl;
	} else {
		$self->{TTL} 			= 600;
	}
	if ($ttw) {
		$self->{TTW} 			= $ttw;
	} else {
		$self->{TTW} 			= 30;
	}
	if ($priority) {
		$self->{PRIORITY} = $priority;
	} else {
		$self->{PRIORITY} = 3;
	}
	bless($self,$class);
	return $self;
}

sub releaseowned {
	my $self   = shift;
	my $owner  = shift;
	my $commid = 0x06;
	my $buf; my $b1; my $b2;
	my $inst_owner = undef;

	if (defined $owner) {
		$inst_owner = $owner;
	} elsif (defined $self->{OWNER}) {
		$inst_owner = $self->{OWNER};
	} else {
		return -1;
	}

	# baal if we're not connected
	if (not defined $self->{CONNECTION} ||
      $self->{CONNSTATUS} != 1 ||
      $self->{CONNECTED} != 1) {
		return -1;
	}

	my $command = sprintf("%c%c%s",$commid,
		length $inst_owner, $inst_owner);
	my $wrote = syswrite($self->{CONNECTION},$command,length $command);
	if ($wrote != length $command) {
		return -1;
	}
	sysread($self->{CONNECTION},$buf,1);
	$b1 = ord($buf);
	sysread($self->{CONNECTION},$buf,1);
	$b2 = ord($buf);
	return (($b1 << 8) | $b2);
}

sub release {
	my $self   = shift;
	my $key    = shift;
	my $index  = shift;
	my $owner  = shift;
	my $commid = 0x05;
	my $buf; my $b1; my $b2;
	my $inst_key   = undef;
	my $inst_index = undef;
	my $inst_owner = undef;

	if (defined $key) {
		$inst_key = $key;
	} elsif (defined $self->{KEY}) {
		$inst_key = $self->{KEY};
	} else {
		return -1;
	}

	if (defined $index) {
		$inst_index = $index;
	} elsif (defined $self->{INDEX}) {
		$inst_index = $self->{INDEX};
	} else {
		return -1;
	}

	if (defined $owner) {
		$inst_owner = $owner;
	} elsif (defined $self->{OWNER}) {
		$inst_owner = $self->{OWNER};
	} else {
		return -1;
	}

	# baal if we're not connected
	if (not defined $self->{CONNECTION} ||
      $self->{CONNSTATUS} != 1 ||
      $self->{CONNECTED} != 1) {
		return -1;
	}

	my $command = sprintf("%c%c%s%c%s%c%s",$commid,
		length $inst_key, $inst_key,
		length $inst_index, $inst_index,
		length $inst_owner, $inst_owner);
	my $wrote = syswrite($self->{CONNECTION},$command,length $command);
	if ($wrote != length $command) {
		return -1;
	}
	sysread($self->{CONNECTION},$buf,1);
	$b1 = ord($buf);
	sysread($self->{CONNECTION},$buf,1);
	$b2 = ord($buf);
	return (($b1 << 8) | $b2);
}

sub renew {
	my $self   = shift;
	my $key    = shift;
	my $index  = shift;
	my $owner  = shift;
	my $commid = 0x04;
	my $buf;
	my $inst_key   = undef;
	my $inst_index = undef;
	my $inst_owner = undef;

	if (defined $key) {
		$inst_key = $key;
	} elsif (defined $self->{KEY}) {
		$inst_key = $self->{KEY};
	} else {
		return -1;
	}

	if (defined $index) {
		$inst_index = $index;
	} elsif (defined $self->{INDEX}) {
		$inst_index = $self->{INDEX};
	} else {
		return -1;
	}

	if (defined $owner) {
		$inst_owner = $owner;
	} elsif (defined $self->{OWNER}) {
		$inst_owner = $self->{OWNER};
	} else {
		return -1;
	}

	# baal if we're not connected
	if (not defined $self->{CONNECTION} ||
      $self->{CONNSTATUS} != 1 ||
      $self->{CONNECTED} != 1) {
		return -1;
	}

	my $command = sprintf("%c%c%s%c%s%c%s",$commid,
		length $inst_key, $inst_key,
		length $inst_index, $inst_index,
		length $inst_owner, $inst_owner);
	my $wrote = syswrite($self->{CONNECTION},$command,length $command);
	if ($wrote != length $command) {
		return -1;
	}
	sysread($self->{CONNECTION},$buf,1);

	return ord($buf);
}

sub lockowner {
	my $self  = shift;
	my $key   = shift;
	my $index = shift;
	my $commid = 0x01;
	my $buf;
	my $inst_key   = undef;
	my $inst_index = undef;

	if (defined $key) {
		$inst_key = $key;
	} elsif (defined $self->{KEY}) {
		$inst_key = $self->{KEY};
	} else {
		return -1;
	}

	if (defined $index) {
		$inst_index = $index;
	} elsif (defined $self->{INDEX}) {
		$inst_index = $self->{INDEX};
	} else {
		return -1;
	}

	# baal if we're not connected
	if (not defined $self->{CONNECTION} ||
      $self->{CONNSTATUS} != 1 ||
      $self->{CONNECTED} != 1) {
		return -1;
	}

	my $command = sprintf("%c%c%s%c%s",$commid,
		length $inst_key, $inst_key,
		length $inst_index, $inst_index);
	my $wrote = syswrite($self->{CONNECTION},$command,length $command);
	if ($wrote != length $command) {
		return -1;
	}
	sysread($self->{CONNECTION},$buf,1);
	my $sizeown = ord($buf);
	if ($sizeown == 0) { return; }  # no owner, i.e. not a lock
	my $read = sysread($self->{CONNECTION},$buf,$sizeown);
	if ($read != $sizeown) {
		return -1;
	}

	return $buf;
}

sub queueloc {
	my $self  = shift;
	my $key   = shift;
	my $index = shift;
	my $owner = shift;
	my $commid = 0x03;
	my $buf; my $b1; my $b2;
	my $inst_key   = undef;
	my $inst_index = undef;
	my $inst_owner = undef;

	if (defined $key) {
		$inst_key = $key;
	} elsif (defined $self->{KEY}) {
		$inst_key = $self->{KEY};
	} else {
		return -1;
	}

	if (defined $index) {
		$inst_index = $index;
	} elsif (defined $self->{INDEX}) {
		$inst_index = $self->{INDEX};
	} else {
		return -1;
	}

	if (defined $owner) {
		$inst_owner = $owner;
	} elsif (defined $self->{OWNER}) {
		$inst_owner = $self->{OWNER};
	} else {
		return -1;
	}

	# baal if we're not connected
	if (not defined $self->{CONNECTION} ||
      $self->{CONNSTATUS} != 1 ||
      $self->{CONNECTED} != 1) {
		return -1;
	}

	my $command = sprintf("%c%c%s%c%s%c%s",$commid,
		length $inst_key, $inst_key,
		length $inst_index, $inst_index,
		length $inst_owner, $inst_owner);

	my $wrote = syswrite($self->{CONNECTION},$command,length $command);
	if ($wrote != length $command) {
		return -1;
	}
	sysread($self->{CONNECTION},$buf,1);
	$b1 = ord($buf);
	sysread($self->{CONNECTION},$buf,1);
	$b2 = ord($buf);
	return (($b1 << 8) | $b2);
}

sub request {
	my $self     = shift;
	my $key      = shift;
	my $index    = shift;
	my $owner    = shift;
	my $ttl      = shift;
	my $ttw      = shift;
	my $priority = shift;
	my $inst_key   = undef;
	my $inst_index = undef;
	my $inst_owner = undef;
	my $inst_ttl   = undef;
	my $inst_ttw   = undef;
	my $inst_prity = undef;

	if (defined $key) {
		$inst_key = $key;
	} elsif (defined $self->{KEY}) {
		$inst_key = $self->{KEY};
	} else {
		return -1;
	}

	if (defined $index) {
		$inst_index = $index;
	} elsif (defined $self->{INDEX}) {
		$inst_index = $self->{INDEX};
	} else {
		return -1;
	}

	if (defined $owner) {
		$inst_owner = $owner;
	} elsif (defined $self->{OWNER}) {
		$inst_owner = $self->{OWNER};
	} else {
		return -1;
	}

	if (defined $ttl) {
		$inst_ttl = $ttl;
	} elsif (defined $self->{TTL}) {
		$inst_ttl = $self->{TTL};
	} else {
		return -1;
	}

	if (defined $ttw) {
		$inst_ttw = $ttw;
	} elsif (defined $self->{TTW}) {
		$inst_ttw = $self->{TTW};
	} else {
		return -1;
	}

	if (defined $priority) {
		$inst_prity = $priority;
	} elsif (defined $self->{PRIORITY}) {
		$inst_prity = $self->{PRIORITY};
	} else {
		return -1;
	}

	# baal if we're not connected
	if (not defined $self->{CONNECTION} ||
      $self->{CONNSTATUS} != 1 ||
      $self->{CONNECTED} != 1) {
		return -1;
	}

	# build up our request lock command
	my $comid = 0x02;
	my $ttl1 = ($inst_ttl >> 8) & 0x00ff;
	my $ttl2 = $inst_ttl & 0x00ff;
	my $ttw1 = ($inst_ttw >> 8) & 0x00ff;
	my $ttw2 = $inst_ttw & 0x00ff;
	my $command = sprintf("%c%c%s%c%s%c%s%c%c%c%c%c",$comid,
		length $inst_key, $inst_key,
		length $inst_index, $inst_index,
		length $inst_owner, $inst_owner,
		$ttl1,$ttl2,$ttw1,$ttw2,$inst_prity);
	my $wrote = syswrite($self->{CONNECTION},$command,length $command);
	if ($wrote != length $command) {
		print "Request Lock: wrote bytes != written bytes\n";
		return -1;
	}
	my $buf;
	sysread($self->{CONNECTION},$buf,1);
	my $b1 = ord($buf);
	sysread($self->{CONNECTION},$buf,1);
	my $b2 = ord($buf);
	$retval = ((($b1 << 8) & 0xff00) | $b2);
	if ($retval == 0) {
		close($self->{CONNECTION});
		$self->{CONNECTION} = undef;
		$self->{CONNECTED}  = 0;
		$self->{CONNSTATUS} = 3;
	}
	return $retval;
}

sub queuedump {
	my $self = shift;
	my $key  = shift;
	my $inst_key   = undef;

	if (defined $key) {
		$inst_key = $key;
	} elsif (defined $self->{KEY}) {
		$inst_key = $self->{KEY};
	} else {
		return -1;
	}

	# baal if we're not connected
	if (not defined $self->{CONNECTION} ||
      $self->{CONNSTATUS} != 1 ||
      $self->{CONNECTED} != 1) {
		return -1;
	}

	my %hash = ();
	my $commid = 0x07;
	my $b1; my $b2; my $buf; my $tmp; my $i;

	my $command = sprintf("%c%c%s",$commid,
		length $inst_key, $inst_key);
	my $wrote = syswrite($self->{CONNECTION},$command,length $command);
	if ($wrote != length $command) {
		return -1;
	}
	sysread($self->{CONNECTION},$buf,1);
	$b1 = ord($buf);
	sysread($self->{CONNECTION},$buf,1);
	$b2 = ord($buf);
	my $num = (($b1 << 8) | $b2);
	for ($i=0; $i < $num; $i++) {
		sysread($self->{CONNECTION},$buf,1);
		$b1 = ord($buf);
		$hash{$i}{"priority"} = $b1;

		sysread($self->{CONNECTION},$buf,1);
		$b1 = ord($buf);
		sysread($self->{CONNECTION},$buf,1);
		$b2 = ord($buf);
		$tmp = (($b1 << 8) | $b2);
		$hash{$i}{"ttl"} = $tmp;

		sysread($self->{CONNECTION},$buf,1);
		$b1 = ord($buf);
		sysread($self->{CONNECTION},$buf,1);
		$b2 = ord($buf);
		$tmp = (($b1 << 8) | $b2);
		$hash{$i}{"ttw"} = $tmp;

		sysread($self->{CONNECTION},$buf,1);
		$b1 = ord($buf);
		sysread($self->{CONNECTION},$buf,$b1);
		$hash{$i}{"index"} = $buf;

		sysread($self->{CONNECTION},$buf,1);
		$b1 = ord($buf);
		sysread($self->{CONNECTION},$buf,$b1);
		$hash{$i}{"owner"} = $buf;

		sysread($self->{CONNECTION},$buf,1);
		$b1 = ord($buf);
		$hash{$i}{"haslock"} = $b1;
		$hash{$i}{"key"} = $inst_key;
	}
	return \%hash;

}

# write stats to hash and return hashref
sub statdump {
	my $self = shift;
	my %hash = ();
	my $commid;
	my $command;
	my $wrote;
	my $b1; my $b2; my $b3; my $b4; my $n1; my $n2; my $num;
	my $days; my $hours; my $mins; my $secs;
	if ($self->connstatus) {
		my $commid = 0x08;
		my $command = sprintf("%c",$commid);
		my $wrote = syswrite($self->{CONNECTION},$command,length $command);
		if ($wrote != length $command) {
			print STDERR "Write error in statdump\n";
		}
		# uptime
		sysread($self->{CONNECTION},$b1,1);
		$b1 = ord($b1);
		sysread($self->{CONNECTION},$b2,1);
		$b2 = ord($b2);
		sysread($self->{CONNECTION},$b3,1);
		$b3 = ord($b3);
		sysread($self->{CONNECTION},$b4,1);
		$b4 = ord($b4);
		$n1 = (($b1 << 8) & 0xff00) | $b2;
		$n2 = (($b3 << 8) & 0xff00) | $b4;
		$num = (($n1 << 16) | $n2);
		$hash{uptime} = $num;
		# Unknown command
		sysread($self->{CONNECTION},$b1,1);
		$b1 = ord($b1);
		sysread($self->{CONNECTION},$b2,1);
		$b2 = ord($b2);
		sysread($self->{CONNECTION},$b3,1);
		$b3 = ord($b3);
		sysread($self->{CONNECTION},$b4,1);
		$b4 = ord($b4);
		$n1 = (($b1 << 8) & 0xff00) | $b2;
		$n2 = (($b3 << 8) & 0xff00) | $b4;
		$hash{unknown} = (($n1 << 16) | $n2);
		# Owner command
		sysread($self->{CONNECTION},$b1,1);
		$b1 = ord($b1);
		sysread($self->{CONNECTION},$b2,1);
		$b2 = ord($b2);
		sysread($self->{CONNECTION},$b3,1);
		$b3 = ord($b3);
		sysread($self->{CONNECTION},$b4,1);
		$b4 = ord($b4);
		$n1 = (($b1 << 8) & 0xff00) | $b2;
		$n2 = (($b3 << 8) & 0xff00) | $b4;
		$hash{owner} = (($n1 << 16) | $n2);
		# Request Lock
		sysread($self->{CONNECTION},$b1,1);
		$b1 = ord($b1);
		sysread($self->{CONNECTION},$b2,1);
		$b2 = ord($b2);
		sysread($self->{CONNECTION},$b3,1);
		$b3 = ord($b3);
		sysread($self->{CONNECTION},$b4,1);
		$b4 = ord($b4);
		$n1 = (($b1 << 8) & 0xff00) | $b2;
		$n2 = (($b3 << 8) & 0xff00) | $b4;
		$hash{requests} = (($n1 << 16) | $n2);
		# Queue loc
		sysread($self->{CONNECTION},$b1,1);
		$b1 = ord($b1);
		sysread($self->{CONNECTION},$b2,1);
		$b2 = ord($b2);
		sysread($self->{CONNECTION},$b3,1);
		$b3 = ord($b3);
		sysread($self->{CONNECTION},$b4,1);
		$b4 = ord($b4);
		$n1 = (($b1 << 8) & 0xff00) | $b2;
		$n2 = (($b3 << 8) & 0xff00) | $b4;
		$hash{queueloc} = (($n1 << 16) | $n2);
		# Renew lock
		sysread($self->{CONNECTION},$b1,1);
		$b1 = ord($b1);
		sysread($self->{CONNECTION},$b2,1);
		$b2 = ord($b2);
		sysread($self->{CONNECTION},$b3,1);
		$b3 = ord($b3);
		sysread($self->{CONNECTION},$b4,1);
		$b4 = ord($b4);
		$n1 = (($b1 << 8) & 0xff00) | $b2;
		$n2 = (($b3 << 8) & 0xff00) | $b4;
		$hash{renew} = (($n1 << 16) | $n2);
		# Release lock
		sysread($self->{CONNECTION},$b1,1);
		$b1 = ord($b1);
		sysread($self->{CONNECTION},$b2,1);
		$b2 = ord($b2);
		sysread($self->{CONNECTION},$b3,1);
		$b3 = ord($b3);
		sysread($self->{CONNECTION},$b4,1);
		$b4 = ord($b4);
		$n1 = (($b1 << 8) & 0xff00) | $b2;
		$n2 = (($b3 << 8) & 0xff00) | $b4;
		$hash{release} = (($n1 << 16) | $n2);
		# Release all
		sysread($self->{CONNECTION},$b1,1);
		$b1 = ord($b1);
		sysread($self->{CONNECTION},$b2,1);
		$b2 = ord($b2);
		sysread($self->{CONNECTION},$b3,1);
		$b3 = ord($b3);
		sysread($self->{CONNECTION},$b4,1);
		$b4 = ord($b4);
		$n1 = (($b1 << 8) & 0xff00) | $b2;
		$n2 = (($b3 << 8) & 0xff00) | $b4;
		$hash{releaseowned} = (($n1 << 16) | $n2);
		# Queue dump
		sysread($self->{CONNECTION},$b1,1);
		$b1 = ord($b1);
		sysread($self->{CONNECTION},$b2,1);
		$b2 = ord($b2);
		sysread($self->{CONNECTION},$b3,1);
		$b3 = ord($b3);
		sysread($self->{CONNECTION},$b4,1);
		$b4 = ord($b4);
		$n1 = (($b1 << 8) & 0xff00) | $b2;
		$n2 = (($b3 << 8) & 0xff00) | $b4;
		$hash{queuedump} = (($n1 << 16) | $n2);
		# Stat dump
		sysread($self->{CONNECTION},$b1,1);
		$b1 = ord($b1);
		sysread($self->{CONNECTION},$b2,1);
		$b2 = ord($b2);
		sysread($self->{CONNECTION},$b3,1);
		$b3 = ord($b3);
		sysread($self->{CONNECTION},$b4,1);
		$b4 = ord($b4);
		$n1 = (($b1 << 8) & 0xff00) | $b2;
		$n2 = (($b3 << 8) & 0xff00) | $b4;
		$hash{statdump} = (($n1 << 16) | $n2);
		# Total accepts
		sysread($self->{CONNECTION},$b1,1);
		$b1 = ord($b1);
		sysread($self->{CONNECTION},$b2,1);
		$b2 = ord($b2);
		sysread($self->{CONNECTION},$b3,1);
		$b3 = ord($b3);
		sysread($self->{CONNECTION},$b4,1);
		$b4 = ord($b4);
		$n1 = (($b1 << 8) & 0xff00) | $b2;
		$n2 = (($b3 << 8) & 0xff00) | $b4;
		$hash{accepted} = (($n1 << 16) | $n2);
		# Total baddies
		sysread($self->{CONNECTION},$b1,1);
		$b1 = ord($b1);
		sysread($self->{CONNECTION},$b2,1);
		$b2 = ord($b2);
		sysread($self->{CONNECTION},$b3,1);
		$b3 = ord($b3);
		sysread($self->{CONNECTION},$b4,1);
		$b4 = ord($b4);
		$n1 = (($b1 << 8) & 0xff00) | $b2;
		$n2 = (($b3 << 8) & 0xff00) | $b4;
		$hash{badipaddr} = (($n1 << 16) | $n2);
		# Total busy
		sysread($self->{CONNECTION},$b1,1);
		$b1 = ord($b1);
		sysread($self->{CONNECTION},$b2,1);
		$b2 = ord($b2);
		sysread($self->{CONNECTION},$b3,1);
		$b3 = ord($b3);
		sysread($self->{CONNECTION},$b4,1);
		$b4 = ord($b4);
		$n1 = (($b1 << 8) & 0xff00) | $b2;
		$n2 = (($b3 << 8) & 0xff00) | $b4;
		$hash{busyrejects} = (($n1 << 16) | $n2);
		# Num owners
		sysread($self->{CONNECTION},$b1,1);
		$b1 = ord($b1);
		sysread($self->{CONNECTION},$b2,1);
		$b2 = ord($b2);
		sysread($self->{CONNECTION},$b3,1);
		$b3 = ord($b3);
		sysread($self->{CONNECTION},$b4,1);
		$b4 = ord($b4);
		$n1 = (($b1 << 8) & 0xff00) | $b2;
		$n2 = (($b3 << 8) & 0xff00) | $b4;
		$hash{numowners} = (($n1 << 16) | $n2);
		# Num contenders
		sysread($self->{CONNECTION},$b1,1);
		$b1 = ord($b1);
		sysread($self->{CONNECTION},$b2,1);
		$b2 = ord($b2);
		sysread($self->{CONNECTION},$b3,1);
		$b3 = ord($b3);
		sysread($self->{CONNECTION},$b4,1);
		$b4 = ord($b4);
		$n1 = (($b1 << 8) & 0xff00) | $b2;
		$n2 = (($b3 << 8) & 0xff00) | $b4;
		$hash{numcontenders} = (($n1 << 16) | $n2);
		# current connects
		sysread($self->{CONNECTION},$b1,1);
		$b1 = ord($b1);
		sysread($self->{CONNECTION},$b2,1);
		$b2 = ord($b2);
		$num = (($b1 << 8) & 0xff00) | $b2;
		$hash{numconnected} = $num;
	}
	return \%hash;	
}

sub disconnect {
	my $self = shift;
	if (defined $self->{CONNECTION}) {
		if (close($self->{CONNECTION})) {
			$self->{CONNECTION} = undef;
			$self->{CONNSTATUS} = undef;
			$self->{CONNECTED}  = 0;
		} else {
			return 0;
		}
	}
	# unset everything
	$self->{SERVER}     = undef; # lockserver host
	$self->{PORT}       = undef; # lockserver host's port
	$self->{CONNECTED}  = 0;     # 0=>not connected, 1=>connected
	$self->{CONNECTION} = undef; # socket file descriptor
	$self->{CONNSTATUS} = undef; # conn response from lockserver
	$self->{KEY}        = undef; # table
	$self->{INDEX}      = undef; # row id
	$self->{OWNER}      = undef; # username
	$self->{TTW}        = undef; # queue wait life time
	$self->{TTL}        = undef; # lock life time
	$self->{PRIORITY}   = undef; # lock priority
	return 1;
}

sub connect {
	my $self = shift;
	my $host = shift;
	my $port = shift;
	my $inst_host = undef;
	my $inst_port = undef;

	if (defined $host) {
		$inst_host = $host;
	} elsif (defined $self->{SERVER}) {
		$inst_host = $self->{SERVER};
	} else {
		return -1;
	}

	if (defined $port) {
		$inst_port = $port;
	} elsif (defined $self->{PORT}) {
		$inst_port = $self->{PORT};
	} else {
		return -1;
	}

	# make sure we're not already connected
	if (defined $self->{CONNECTION}) {
		if ($self->{CONNECTED}) {
			# looks like we really are connected, let's return
			# our connection status and hope it's accurate...
			return $self->{CONNSTATUS};
		} else {
			# looks like we're not really connected so let's just
			# set our internals accordingly and pretend we weren't
			# connected...
			$self->{CONNECTION} = undef;
			$self->{CONNSTATUS} = undef;
			return -1;
		}
	}

	# make a connection attempt
	$self->{CONNECTION} = IO::Socket::INET->new(
		PeerAddr => $inst_host,
		PeerPort => $inst_port,
		Proto    => "tcp",
		Type     => SOCK_STREAM);

	if (defined $self->{CONNECTION}) {
		# read one-byte from server
		my $response;
		my $read = sysread($self->{CONNECTION},$response,1);
		$response = ord($response);
		if ($response == 0) {
			# our IP was rejected
			close($self->{CONNECTION});
			$self->{CONNSTATUS} = 0;
			$self->{CONNECTION} = undef;
			$self->{CONNECTED}  = 0;
		} elsif ($response == 2) {
			# server too busy
			close($self->{CONNECTION});
			$self->{CONNSTATUS} = 2;
			$self->{CONNECTION} = undef;
			$self->{CONNECTED}  = 0;
		} elsif ($response == 1) {
			# good connection
			$self->{CONNECTED}  = 1;
			$self->{CONNSTATUS} = 1;
			return 1;
		} else {
			# unknown response
			$self->{CONNECTED}  = 1;
			$self->{CONNSTATUS} = -1;
			return -1;
		}
	} else {
		# failed to make tcp/ip connection
		$self->{CONNECTED}  = 0;
		$self->{CONNSTATUS} = undef;
		return -1;
	}
}

sub connstatus {
	# query connection status
	my $self = shift;
	return $self->{CONNSTATUS};
}

sub connected {
	# query connection status
	my $self = shift;
	return $self->{CONNECTED};
}

sub port {
	# set/query internval variable
	# don't overwrite if we're already connected
	my $self = shift;
	if (defined $self->{CONNSTATUS}) {
		return $self->{PORT};
	}
	if (@_) { $self->{PORT} = shift }
	return $self->{PORT};
}

sub server {
	# set/query internval variable
	# don't overwrite if we're already connected
	my $self = shift;
	if (defined $self->{CONNSTATUS}) {
		return $self->{SERVER};
	}
	if (@_) { $self->{SERVER} = shift }
	return $self->{SERVER};
}

sub key {
	# set/query internval variable
	my $self = shift;
	if (@_) { $self->{KEY} = shift }
	return $self->{KEY};
}

sub index {
	# set/query internval variable
	my $self = shift;
	if (@_) { $self->{INDEX} = shift }
	return $self->{INDEX};
}

sub owner {
	# set/query internval variable
	my $self = shift;
	if (@_) { $self->{OWNER} = shift }
	return $self->{OWNER};
}

sub ttl {
	# set/query internval variable
	my $self = shift;
	if (@_) { $self->{TTL} = shift }
	return $self->{TTL};
}

sub ttw {
	# set/query internval variable
	my $self = shift;
	if (@_) { $self->{TTW} = shift }
	return $self->{TTW};
}

sub priority {
	# set/query internval variable
	my $self = shift;
	if (@_) { $self->{PRIORITY} = shift }
	return $self->{PRIORITY};
}

sub DESTROY {
	# $obj has been reaped by Perl's Garbage-collector,
	# close our connection if it exists
	my $self = shift;
	if (defined $self->{CONNECTION}) {
		if (close($self->{CONNECTION})) {
			$self->{CONNECTION} = undef;
			$self->{CONNSTATUS} = undef;
			$self->{CONNECTED}  = 0;
		}
	}
	$self->{SERVER}     = undef; # lockserver host
	$self->{PORT}       = undef; # lockserver host's port
	$self->{CONNECTED}  = 0;     # 0=>not connected, 1=>connected
	$self->{CONNECTION} = undef; # socket file descriptor
	$self->{CONNSTATUS} = undef; # conn response from lockserver
	$self->{KEY}        = undef; # table
	$self->{INDEX}      = undef; # row id
	$self->{OWNER}      = undef; # username
	$self->{TTW}        = undef; # queue wait life time
	$self->{TTL}        = undef; # lock life time
	$self->{PRIORITY}   = undef; # lock priority
	return;
}

# always need to return true in perlmods...
1;

