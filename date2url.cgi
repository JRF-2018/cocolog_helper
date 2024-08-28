#!/usr/bin/perl
our $VERSION = "0.0.3"; # Time-stamp: <2024-08-28T09:03:33Z>";

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

use URI::Escape;
use Encode qw(encode decode);
use Fcntl qw(:DEFAULT :flock :seek);
use SDBM_File;
use Time::Piece;
use CGI;

our $WAIT = 5;
our $SERVER_URL = "http://jrf.cocolog-nifty.com/";
our $ARCHIVES_URL = "http://jrf.cocolog-nifty.com/statuses/archives.html";
our $GOOGLE_URL = "http://www.google.com/search?hl=en\&safe=off\&lr=lang_ja\&pws=0\&q=";
our $DBM_MODULE = "SDBM_File";
our $DBM = "date2url.sdb";
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

<title>date2url.cgi Error</title>
<!-- date2url.cgi version $VERSION .
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

<title>date2url.cgi Error</title>
<!-- date2url.cgi version $VERSION .
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
<!-- date2url.cgi version $VERSION .
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

sub print_google_html {
  my ($q, $w) = @_;
  my $r;
  if ($q =~ /^([01-9]+)[-\/]([01-9]+)[-\/]([01-9]+)$/) {
    $r = "${1}年${2}月${3}日";
  } elsif ($q =~ /^([01-9]+)[-\/]([01-9]+)$/) {
    $r = "${1}年${2}月";
  } else {
    $r = $q;
  }
  $r = uri_escape_utf8($r);
  $r = escape_html($GOOGLE_URL . $r);

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
<!-- date2url.cgi version $VERSION .
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
<p>「$q」は見つからないので Google で検索するよう転送します。<p/>
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
  $DB_TABLE{'last'} = parse_archives($rep->decoded_content());
}

sub main {
  my $q = $CGI->param('q') || undef;
  bad_request("No query.\n") if ! defined $q;
  $q = decode('UTF-8', $q);
  my $origq = $q;
  if ($q =~ /^([01-9]+)[-\/]([01-9]+)[-\/]([01-9]+)$/) {
    $q = sprintf("%d%02d", $1, $2);
  } elsif ($q =~ /^([01-9]+)[-\/]([01-9]+)$/) {
    $q = sprintf("%d%02d", $1, $2);
  } else {
    $q = undef;
  }
  my $w = 0;
  my $r;
  my $last = 0;
  if (defined $q) {
    tie(%DB_TABLE, $DBM_MODULE, $DBM, O_RDONLY, 0666)
      or die "Couldn't tie $DBM_MODULE to $DBM: $!";
    if (exists $DB_TABLE{$q}) {
      $r = $DB_TABLE{$q};
    }
    $last = $DB_TABLE{'last'};
    untie(%DB_TABLE);
  }
  my $lt = localtime;
  $lt = $lt->strftime("%Y%m");
  if (defined $q && $q <= $lt && $q > $last && ! defined $r) {
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
    print_html($origq, $r, $w);
  } else {
    print_google_html($origq);
  }
}

main();
exit(0);
