#!/usr/bin/perl
our $VERSION = "0.0.1"; # Time-stamp: <2022-01-02T14:27:56Z>";

##
## Author:
##
##   JRF ( http://jrf.cocolog-nifty.com/statuses/ )
##
## Repository:
##
##   https://github.com/JRF-2018/cocolog_helper
##
## License:
##
##   Public Domain.
##

use strict;
use warnings;
use utf8; # Japanese

use Encode qw(encode decode);
use Fcntl qw(:DEFAULT :flock :seek);
use SDBM_File;

our $SERVER_URL = "http://jrf.cocolog-nifty.com/";
our $ARCHIVES_URL = "http://jrf.cocolog-nifty.com/statuses/archives.html";
our $DBM_MODULE = "SDBM_File";
our $DBM = "date2url.sdb";

our %DB_TABLE;

sub escape_html {
  my ($s) = @_;
  $s =~ s/\&/\&amp\;/sg;
  $s =~ s/</\&lt\;/sg;
  $s =~ s/>/\&gt\;/sg;
#  $s =~ s/\'/\&apos\;/sg;
  $s =~ s/\"/\&quot\;/sg;
  return $s;
}

sub unescape_html {
  my ($s) = @_;
  $s =~ s/\&quot\;/\"/sg;
#  $s =~ s/\&apos\;/\'/sg;
  $s =~ s/\&gt\;/>/sg;
  $s =~ s/\&lt\;/</sg;
  $s =~ s/\&amp\;/\&/sg;
  return $s;
}

sub servered_url {
  my ($s) = @_;
  return $s if $s =~ /^https?:/;
  $s = $' if $s =~ /^\//;
  return $SERVER_URL . $s;
}

sub parse_archives {
  my ($s) = @_;
  #$s = decode('UTF-8', $s);

  my $max = 0;
  if ($s !~ /<h2>バックナンバー<\/h2>\s*<p>/) {
    die "Parse Error.";
  }
  $s = $';
  if ($s !~ /<\/p>/) {
    die "Parse Error.";
  }
  $s = $`;
  my @r;
  while ($s =~ /<a[^>]*href="([^>"]*)"[^>]*>([^<]*)年([^<]*)月<\/a>/) {
    my $url = $1;
    my $mon = sprintf("%d%02d", $2, $3);
    $s = $';
    $url = unescape_html($url);
    $DB_TABLE{$mon} = $url;
    print "$mon -> $url\n";
    if ($max <= $mon) {
      $max = $mon;
    }
  }
  return $max;
}

sub update_table {
  require LWP::UserAgent;
  my $ua = LWP::UserAgent->new();
  my $rep = $ua->get($ARCHIVES_URL);
  if (! $rep->is_success()) {
    die "Fail. Can't access $ARCHIVES_URL.\n";
  }
  my $max = parse_archives($rep->decoded_content());
  $DB_TABLE{'last'} = $max;
  print "last -> $max\n";
}

sub main {
  tie(%DB_TABLE, $DBM_MODULE, $DBM, O_RDWR | O_CREAT, 0666)
      or die "Couldn't tie $DBM_MODULE to $DBM: $!";
  update_table();
  untie(%DB_TABLE);
}

main();
exit(0);
