#!/usr/bin/perl
#
# $RCSfile$
# $Author: michaelthoward $
# $Date: 2003-08-19 20:44:26 +0200 (mar., 19 août 2003) $
# $Revision: 1299 $
#
# Copyright (C) 2003  The Jmol Development Team
#
# Contact: jmol-developers@lists.sf.net
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
#  02111-1307  USA.
#
use English;
use CGI;
use CGI::Carp;
use LWP;
use LWP::UserAgent;
use strict;

my $cgi = new CGI;
my $url = $cgi->param('url');
if (! $url) {
    print $cgi->header(-type=>'text/plain' -status=>'404 Not Found');
}
my $userAgent = LWP::UserAgent->new;
$userAgent->agent("JmolAppletProxy/1.0");

my $request = HTTP::Request->new(GET => $url);
my $response = $userAgent->request($request);
if ($response->is_success()) {
    print $cgi->header(-type=>'text/plain'), $response->content();
} else {
    print $cgi->header(-type=>'text/plain' -status=>$response->status_line);
    print $response->status_line;
}
