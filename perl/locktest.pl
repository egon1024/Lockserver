#!/usr/bin/perl -I./module
use strict;

# append to our module search path so we can use Lockserver
# OR can use the -Ipath switch above
#BEGIN {
#	push(@INC,"/home/eric/perl/Lockserver",
#            "/usr/home/ej/scripting/perl/modules");
#}

##
## Test script for Perl API to Lockserver
##

use Lockserver;
my $k; my $j;

printf("=> TESTING STARTED. Expected return values in [brackets]\n");
printf("=> Creating lock object\n");
my $l = new Lockserver();

print("=> Attempting to connect\n");
$l->connect();

if ($l->connected) {
	printf("=> Connected! Connection status [1]: %s\n",$l->connstatus);

	# no internal lock variables defined, this next call should fail
	printf("=> Requesting a new lock [-1]: %s\n", $l->request());

	# create a lock in the lockserver
	printf("=> Request a new lock on \"FooBar-103334-ej\" [1]: %s\n",
		$l->request("FooBar",103334,"ej"));

	# create a queue in the lockserver
	printf("=> Request a new lock on \"FooBar-103334-eric\" [2]: %s\n",
		$l->request("FooBar",103334,"eric"));

	# should get "ej"
	printf("=> Who owns lock \"FooBar-103334\" [ej]: %s\n",
		$l->lockowner("FooBar",103334));

	# should get no one
	printf("=> Who owns the lock \"FooBar-103333\" []: %s\n",
		$l->lockowner("FooBar",103333));

	# should get 2
	printf("=> Queue location for \"FooBar-103334-eric\" [2]: %s\n",
		$l->queueloc("FooBar",103334,"eric"));

	# should succeed
	printf("=> Renew lock \"FooBar-103334-ej\" [1]: %s\n",
		$l->renew("FooBar",103334,"ej"));

	# no such lock, no success
	printf("=> Renew lock \"FooBar-103334-emj\" [0]: %s\n",
		$l->renew("FooBar",103334,"emj"));

	printf("=> Create a few queues [1 2 3 1 2 1]: %s %s %s %s %s %s\n",
		$l->request("FooBar",555,"emj1"),
		$l->request("FooBar",555,"emj2"),
		$l->request("FooBar",555,"emj3"),
		$l->request("FooBar",556,"emj1"),
		$l->request("FooBar",556,"emj2"),
		$l->request("FooBar",557,"emj2"));

	# queuedump returns hashref to double hash
	printf("=> Queue dump \"FooBar\":\n");
	my $q_href = $l->queuedump("FooBar");
	foreach $k (sort keys %$q_href) {
		my $v = $q_href->{$k};
		foreach $j (sort keys %$v) {
			printf("   %-14s %s\n",$k."->".$j.":",$v->{$j});
		}
	}

	# release one lock
	printf("=> Release \"FooBar-555-emj1\" [1]: %s\n",
		$l->release("FooBar",555,"emj1"));

	# release two locks
	printf("=> Release locks owned by \"emj2\" [3]: %s\n",
		$l->releaseowned("emj2"));

	# statdump returns a hashref
	printf("=> Stat dump command:\n");
	my $stat_href = $l->statdump;
	foreach $k (sort keys %$stat_href) {
		printf("   %-14s %s\n",$k.":",$stat_href->{$k});
	}

	# empty lockserver
	printf("=> Cleaning up [1 0 0 1 0 1]: %s %s %s %s %s %s\n",
		$l->releaseowned("ej"),
		$l->releaseowned("eric"),
		$l->releaseowned("emj"),
		$l->releaseowned("emj1"),
		$l->releaseowned("emj2"),
		$l->releaseowned("emj3"));

	# disconnect
	if ($l->disconnect) {
		printf("=> Closed connection successfully\n");
	} else {
		printf("=> Failed trying to disconnect...\n");
	}

} else {
	printf("=> FAILED TO CONNECT!\n");
}

printf("=> TESTING COMPLETE!\n");

exit;

