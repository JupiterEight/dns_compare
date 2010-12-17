#!/usr/bin/python
#
# dns_compare.py - Compare the data in a BIND zone file to the data being returned
#                  by an authoritative DNS server.
#
# Purpose:
#   Use this tool to verify the data being returned by an authoritative DNS server
#   matches the data in a zone file.
#
# Use case:
#   This is useful, for example, when you are migrating from one DNS server to another and
#   need to verify that all the records imported correctly.
#
#   In my case, I used this tool to help me during a migration of multiple domains from
#   Windows 2000 DNS and GoDaddy DNS (which can both export BIND zone files) into Amazon's
#   Route53 DNS service.  With this tool, I could confidently prove that all records
#   properly imported into Route53.
#
# Example usage:
#       $ dns_compare.py -z example.com --file example.com.zone --server 10.1.1.1
#       ....X...X..done
#       Results:
#       9 passed / 2 fail
#
#   NOTE: use -v to get a very verbose view of each dns record as it is checked
#
# Author:
#   joe miller, <joeym@joeym.net>, 12/16/2010
#

from optparse import OptionParser

import sys
from pprint import pprint

try:
	import dns.resolver, dns.zone
	from dns.exception import DNSException
	from dns.rdataclass import *
	from dns.rdatatype import *
except ImportError:
	print "Please install dnspython:"
	print "$ sudo easy_install dnspython"
	sys.exit(-1)

parser = OptionParser()
# required options
parser.add_option("-z", "--zone", dest="zone", metavar="DOMAIN",
					help="name of the domain we're checking (eg: domain.com)")
parser.add_option("-f", "--file", dest="zonefile", metavar="FILE",
					help="zone file to load records from")
parser.add_option("-s", "--server", dest="nameserver", metavar="IP_ADDRESS",
					help="DNS server to compare zone file against (must be IP, not hostname)")
# optional .. options
parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False,
					help="print detailed results of each action")				
parser.add_option("-a","--soa", dest="compare_soa", action="store_true", default=False,
					help="compare SOA records (default: false)")					
parser.add_option("-n","--ns", dest="compare_ns", action="store_true", default=False,
					help="compare NS records (default: false)")					
					
(opts, remaining_args) = parser.parse_args()

# check for required options, since optparse doesn't support required options
if opts.zone == None or opts.zonefile == None or opts.nameserver == None:
	print "Error: required arguments: --zone, --file, --server"
	sys.exit(-1)

z = dns.zone.from_file(opts.zonefile, origin=opts.zone, relativize=False)

r = dns.resolver.Resolver(configure=False)
r.nameservers = [opts.nameserver]

matches=0
mismatches=0
for (name, ttl, rdata) in z.iterate_rdatas():
	if rdata.rdtype == SOA and opts.compare_soa == False:
		continue
	if rdata.rdtype == NS and opts.compare_ns == False:
		continue
			
	match = False
	result = ''
	try:
		ans = r.query(name, rdata.rdtype, rdata.rdclass)
		for rd in ans:
			result = rd
			if rd == rdata:
				match = True
	except DNSException, e:
	 	result = e.__class__
		pass
		
	if opts.verbose:
		description = ''
		if match:
			description = '[Match]'
		else:
			description = '[MIS-MATCH]'
		print "----"
		print "%s querying %s: name='%s' type='%s' class='%d' ..." % (description, opts.nameserver, name, rdata.rdtype, rdata.rdclass)
		print "Expected: ", rdata
		print "Got     : ", rd
	
	if match:
		if opts.verbose == False:
			sys.stdout.write('.')
			sys.stdout.flush()
		matches += 1
	else:
		if opts.verbose == False:
			sys.stdout.write('X')
			sys.stdout.flush()
		mismatches += 1
print "done"

print "\nResults:"
print "Matches:     ", matches
print "Mis-matches: ", mismatches

if opts.verbose == False and mismatches > 0:
	print " (re-run with --verbose to see details of the mis-matches )"