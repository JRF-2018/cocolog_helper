#!/usr/bin/perl
our $VERSION = "0.0.3"; # Time-stamp: <2024-08-28T09:03:38Z>";

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
use Time::Piece;
use CGI;

our $WAIT = 5;
our $SERVER_URL = "http://jrf.cocolog-nifty.com/";
our $ARCHIVES_URL = "http://jrf.cocolog-nifty.com/statuses/archives.html";
our $DBM_MODULE = "SDBM_File";
our $DBM = "id2url.sdb";
our $CSS = "id2url.css";

our %DB_TABLE;

our $CGI = CGI->new;
binmode(STDOUT, ":utf8");

our $DIE_1 = sub {
  my $message = shift;
  $message = escape_html($message);

  print $CGI->header(-type => 'text/html',
		     -charset => 'utf-8',
		     -status => '500 Internal Server Error');
  print <<"EOT";
<\!DOCTYPE html>
<html>

<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta http-equiv="Content-Language" content="ja">
<meta name="robots" content="noindex,nofollow" />
<meta name="viewport" content="width=device-width,initial-scale=1" />

<title>id2url.cgi Error</title>
<!-- id2url.cgi version $VERSION .
     You can get the source from https://github.com/JRF-2018/cocolog_helper .
-->
<link rel="stylesheet" href="$CSS" type="text/css" />
</head>
<body lang="ja">
<div id="container">
<div id="banner">
<h1>500 Internal Server Error</h1>
</div>
<div id="center">
<div class="content">
<p>Die: $message</p>
</div>
</div>
</div>
</body>
</html>
EOT
  exit(1);
};

$SIG{__DIE__} = $DIE_1;

sub bad_request {
  my $message = shift;
  $message = escape_html($message);
  print $CGI->header(-type => 'text/html',
		     -charset => 'utf-8',
		     -status => '400 Bad Request');
  print <<"EOT";
<\!DOCTYPE html>
<html>

<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta http-equiv="Content-Language" content="ja">
<meta name="robots" content="noindex,nofollow" />
<meta name="viewport" content="width=device-width,initial-scale=1" />

<title>id2url.cgi Error</title>
<!-- id2url.cgi version $VERSION .
     You can get the source from https://github.com/JRF-2018/cocolog_helper .
-->
<link rel="stylesheet" href="$CSS" type="text/css" />
</head>
<body lang="ja">
<div id="container">

<div id="banner">
<h1>400 Bad Request</h1>
</div>
<div id="center">
<div class="content">
<p>$message</p>
</div>
</div>
</div>
</body>
</html>
EOT
  exit(1);
}

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

sub print_html {
  my ($q, $r, $w) = @_;
  $q = escape_html($q);
  $r = escape_html(servered_url($r));
  if ($w) {
    $w = "お待たせしてます。";
  } else {
    $w = "";
  }

  print $CGI->header(-type => 'text/html',
		     -charset => 'utf-8');
  print <<"EOT";
<!DOCTYPE html>
<html lang="ja">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta http-equiv="Content-Language" content="ja">
<meta name="robots" content="noindex,nofollow" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<meta http-equiv="Refresh" content="$WAIT; url=$r" />

<title>転送</title>
<!-- id2url.cgi version $VERSION .
     You can get the source from https://github.com/JRF-2018/cocolog_helper .
-->
<link rel="stylesheet" href="$CSS" type="text/css" />


</head>
<body lang="ja">
<div id="container">

<div id="banner">
<h1>転送</h1>
</div>
<div id="center">
<div class="content">
<p>$q は <a href="$r">$r</a> です。</p>
<p>${w}転送中です。$WAIT 秒待っても転送されないときは<a href="$r">ここ</a>をクリックしてください。</p>
</div>
</div>
</div>
</body>
</html>
EOT
}

sub parse_archives {
  my ($s) = @_;
  #$s = decode('UTF-8', $s);

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
    #print "$mon -> $url\n";
    push(@r, [$mon, $url]);
  }
  return @r;
}

sub parse_month {
  my ($s) = @_;
  #$s = decode('UTF-8', $s);

  if ($s !~ /<h2 class="content-header">/) {
    die "Parse Error.";
  }
  $s = $';
  if ($s !~ /<div class="content-bottom"><\/div>/) {
    die "Parse Error.";
  }
  $s = $`;
  while ($s =~ /<h3 class="status-id"><a href="([^\"]*)">([^<]*)<\/a><\/h3>/) {
    $s = $';
    my $url = $1;
    my $id = $2;
    $url = unescape_html($url);
    $id = unescape_html($id);
    if ($url =~ /^\Q$SERVER_URL\E/) {
      $url = $';
    }
    #print "$id -> $url\n";
    $DB_TABLE{$id} = $url;
  }
}

sub update_table {
  my $last = $DB_TABLE{'last'};
  my $max = $last;
  require LWP::UserAgent;
  my $ua = LWP::UserAgent->new();
  my $rep = $ua->get($ARCHIVES_URL);
  if (! $rep->is_success()) {
    die "Fail. Can't access $ARCHIVES_URL.\n";
  }
  my @mon = parse_archives($rep->decoded_content());
  for my $l (@mon) {
    my ($mon, $url) = @$l;
    if ($mon >= $last) {
      if ($max <= $mon) {
	$max = $mon;
      }
      $rep = $ua->get($url);
      if (! $rep->is_success()) {
	die "Fail. Can't access $url.\n";
      }
      parse_month($rep->decoded_content());
    }
  }
  $DB_TABLE{'last'} = $max;
}

sub main {
  my $q = $CGI->param('q') || undef;
  bad_request("No query.\n") if ! defined $q;
  $q = decode('UTF-8', $q);
  if ($q =~ /(?:cocolog|aboutme)\:[01-9]+/
      && length($&) < 256) {
    $q = $&;
  } else {
    bad_request("Illegal query.\n");
  }
  my $w = 0;
  tie(%DB_TABLE, $DBM_MODULE, $DBM, O_RDONLY, 0666)
    or die "Couldn't tie $DBM_MODULE to $DBM: $!";
  my $r;
  if (exists $DB_TABLE{$q}) {
    $r = $DB_TABLE{$q};
  }
  untie(%DB_TABLE);
  if (! defined $r) {
    $w = 1;
    tie(%DB_TABLE, $DBM_MODULE, $DBM, O_RDWR, 0666)
      or die "Couldn't tie $DBM_MODULE to $DBM: $!";
    update_table();
    if (exists $DB_TABLE{$q}) {
      $r = $DB_TABLE{$q};
    }
    untie(%DB_TABLE);
  }
  if (defined $r) {
    print_html($q, $r, $w);
  } else {
    bad_request("No url for id $q.\n");
  }
}

main();
exit(0);
