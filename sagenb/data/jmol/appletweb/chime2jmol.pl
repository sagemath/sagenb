use strict;
use HTML::Parser;
use Getopt::Std;
use File::Find;
use File::Copy;
use File::Path;
use Cwd;

sub handleEmbed;
sub handleEnd;
sub usage;

use vars qw/$opt_v $opt_a $opt_s $opt_c $opt_d $opt_b/;
getopts('va:s:cd:b:') or usage();

($opt_s && $opt_d) or usage();

my $pwd = cwd();
print "pwd is $pwd\n" if $opt_v;

my $fullsrcpath = $opt_s;
$fullsrcpath =~ s|(\./)+||;
$fullsrcpath = $pwd . "/" . $fullsrcpath unless $fullsrcpath =~ m|^/|;
$fullsrcpath = $fullsrcpath . "/" unless $fullsrcpath =~ m|/$|;

my $fulldstpath = $opt_d;
$fulldstpath =~ s|(\./)+||;
$fulldstpath = $pwd . "/" . $fulldstpath unless $fulldstpath =~ m|^/|;
$fulldstpath = $fulldstpath . "/" unless $fulldstpath =~ m|/$|;


print "source directory $fullsrcpath\n" if $opt_v;
(-d $fullsrcpath) or die "$fullsrcpath is not a directory";

if ($opt_c) {
    print "deleting directory tree $fulldstpath\n" if $opt_v;
    rmtree $fulldstpath;
}

if (-e $fulldstpath) {
    print "destination directory $fulldstpath exists\n" if $opt_v;
    -d $fulldstpath or die "$fulldstpath is not a directory";
} else {
    print "creating destination directory $fulldstpath\n" if $opt_v;
    mkdir($fulldstpath) or die "could not make directory $fulldstpath";
}

my $archive = "JmolApplet.jar";
$archive = $opt_a if $opt_a;
print "archive is $archive\n" if $opt_v;

my $codebase = $opt_b;
print "codebase is $codebase\n" if $codebase && $opt_v;

my $baseDirectory;
my @files;
my @directories;
sub accumulateFilename {
    if ($baseDirectory) {
	my $pathname = $File::Find::name;
	my $name = substr $pathname, length($baseDirectory);
	if (-f $pathname) {
	    print "$pathname is a file\n";
	    push @files, $name if -f $pathname;
	} elsif (-d $pathname) {
	    print "$pathname is a directory\n";
	    push @directories, $name if -d $pathname;
	} else {
	    print "$pathname is neither fish nor fowl?\n";
	    print "but it exists!\n" if -e $pathname;
	}

    } else {
	$baseDirectory = $File::Find::name . "/";
	print "baseDirectory=$baseDirectory\n" if $opt_v;
    }
}
find(\&accumulateFilename, $fullsrcpath);

for my $directory (@directories) {
    print "mkdir $fulldstpath$directory\n" if $opt_v;
    mkdir "$fulldstpath$directory";
}

for my $file (@files) {
    next if $file =~  /\~$/; # ignore emacs files
    print "processing $file\n" if $opt_v;
    processFile("$baseDirectory$file", "$fulldstpath$file");
}

exit();

sub processFile {
    my ($src, $dst) = @_;
    if ($src =~ /html?$/i) {
	processHtmlFile($src, $dst);
    } else {
	copyFile($src, $dst);
    }
}

sub copyFile {
    my ($src, $dst) = @_;
#    print "copyFile $src -> $dst\n";
    copy $src, $dst;
}

sub processHtmlFile {
    my ($src, $dst) = @_;
    open OUTPUT, ">$dst" or die "could not open $dst";

    my $p = HTML::Parser->new(start_h =>
			      [\&handleEmbed, 'skipped_text,text,tokens'],
			      end_document_h => [\&writePrevious,
						 'skipped_text']);
    $p->report_tags('embed');
    $p->parse_file($src) || die $!;
    close OUTPUT;
}

my ($previous, $embed, $tokens);
my $tokenCount;

# common to both plugins and buttons
my ($name, $width, $height, $bgcolor, $src, $script);
# plug-in specific
my ($preloadscript, $loadStructCallback, $messageCallback,
    $pauseCallback, $pickCallback);
# button-specific
my ($type, $button, $buttonCallback, $target, $altscript);

sub handleEmbed {
    ($previous, $embed, $tokens) = @_;
    $tokenCount = scalar @$tokens;

    $name = getUnquotedParameter('name');
    $width = getUnquotedParameter('width');
    $height = getUnquotedParameter('height');
    $bgcolor = getUnquotedParameter('bgcolor');
    $src = getUnquotedParameter('src');

    $loadStructCallback = getUnquotedParameter('LoadStructCallback');
    $messageCallback = getUnquotedParameter('MessageCallback');
    $pauseCallback = getUnquotedParameter('pauseCallback');
    $pickCallback = getUnquotedParameter('pickCallback');

    $type = getUnquotedParameter('type');
    $button = getUnquotedParameter('button');
    $buttonCallback = getUnquotedParameter('ButtonCallBack');
    $target = getUnquotedParameter('target');
    $preloadscript = checkPreloadScript();
    $script = getRawParameter('script');
    $script = convertSemicolonNewline($script);
    $altscript = convertSemicolonNewline(getRawParameter('altscript'));

    writePrevious($previous);
    writeCommentedEmbed();
#    dumpVars();
    writeJmolApplet() unless $button;
    writeButtonControl() if $button;
}

sub checkPreloadScript {
    my $spinX = getUnquotedParameter('spinx');
    my $spinY = getUnquotedParameter('spiny');
    my $spinZ = getUnquotedParameter('spinz');
    my $startspin = getUnquotedParameter('startspin');
    my $frank = getUnquotedParameter('frank');
    my $debugscript = getUnquotedParameter('debugscript');

    my $preloadscript = getUnquotedParameter('preloadscript');
    $preloadscript = convertSemicolonNewline($preloadscript);

    $preloadscript .= "set spin x $spinX;" if $spinX;
    $preloadscript .= "set spin y $spinY;" if $spinY;
    $preloadscript .= "set spin z $spinZ;" if $spinZ;
    $preloadscript .= "set spin on;" if $startspin =~ /true|yes|on/i;
    $preloadscript .= "set frank $frank;" if $frank;
    $preloadscript .= "set debugscript $debugscript;" if $debugscript;
    return $preloadscript;
}

sub dumpVars {
    print <<END;
    name=$name
    width=$width
    height=$height
    bgcolor=$bgcolor
    src=$src
    type=$type
    button=$button
    buttonCallback=$buttonCallback
    target=$target
    script=$script
    altscript=$altscript
    
END
}

sub writePrevious {
    print OUTPUT convertNewline(@_[0]);
}

sub writeCommentedEmbed {
    $embed = convertNewline($embed);
    print OUTPUT "<!-- $embed -->\n";
}

sub writeJmolApplet {
    print OUTPUT
	"  <applet name='$name' code='JmolApplet' archive='$archive'\n"
	if $name;
    print OUTPUT
	"  <applet code='JmolApplet' archive='$archive'\n"
	unless $name;
    print OUTPUT
	"          codebase='$codebase'\n" if $codebase;
    print OUTPUT
	"          width='$width' height='$height' mayscript='true' >\n";
    print OUTPUT
	"    <param name='emulate' value='chime' />\n";
    print OUTPUT
	"    <param name='bgcolor' value='$bgcolor' />\n" if $bgcolor;
    print OUTPUT
	"    <param name='load'    value='$src' />\n" if $src;
    print OUTPUT
	"    <param name='preloadscript'\n",
	"           value='$preloadscript' />\n" if $preloadscript;
    print OUTPUT
	"    <param name='script'  value=$script />\n" if $script;
    print OUTPUT
	"    <param name='LoadStructCallback' value='$loadStructCallback' />\n"
	if $loadStructCallback;
    print OUTPUT
	"    <param name='MessageCallback'    value='$messageCallback' />\n"
	if $messageCallback;
    print OUTPUT
	"    <param name='PauseCallback'      value='$pauseCallback' />\n"
	if $pauseCallback;
    print OUTPUT
	"    <param name='PickCallback'       value='$pickCallback' />\n"
	if $pickCallback;
    print OUTPUT
	"  </applet>\n";
}

sub writeButtonControl {
    my ($controlType, $group);
    if ($button =~ /push/i) {
	$controlType = "chimePush";
    } elsif ($button =~ /toggle/i) {
	$controlType = "chimeToggle";
    } elsif ($button =~ /radio(\d+)/i) {
	$controlType = "chimeRadio";
	$group = $1;
    }
    my $buttonScript = $script || $src;
    print OUTPUT
	"  <applet name=$name code='JmolAppletControl' archive='$archive'\n"
	if $name;
    print OUTPUT
	"  <applet code='JmolAppletControl' archive='$archive'\n"
	unless $name;
    print OUTPUT
	"          codebase='$codebase'\n" if $codebase;
    print OUTPUT
	"          width='$width' height='$height' mayscript='true' >\n";
    print OUTPUT
	"    <param name='target' value='$target' />\n".
	"    <param name='type'   value='$controlType' />\n";
    print OUTPUT
	"    <param name='group'  value='$group' />\n"
	if $group;
    print OUTPUT
	"    <param name='script' value=$buttonScript />\n"
	if $buttonScript;
    print OUTPUT
	"    <param name='altscript' value=$altscript />\n"
	if $altscript;
    print OUTPUT
	"    <param name='ButtonCallback' value=$buttonCallback />\n"
	if $buttonCallback;
    print OUTPUT
	"  </applet>\n";
}

sub getRawParameter {
    my ($tag) = @_;
    for (my $i = 0; $i < $tokenCount; ++$i) {
	my $token = $tokens->[$i];
	return $tokens->[$i + 1] if ($token =~ /$tag/i);
    }
    return undef;
}

sub getUnquotedParameter {
    my $value = getRawParameter(@_);
    return undef unless $value;
    $value =~ s/^[\'\"]//;
    $value =~ s/[\'\"]$//;
    return $value;
}

sub convertNewline {
    my ($text) = @_;
    $text =~ s/\r\n/\n/g;
    $text =~ s/\r/\n/g;
    return $text;
}

sub convertSemicolonNewline {
    my ($text) = @_;
    $text = convertNewline($text);
    $text =~ s/\n/;\n/g;
    return $text;
}

sub usage {
    print <<END;
    perl chime2jmol.pl -s <src> -d <dst> {-c} {-a <archive>}

    -s <source directory>
    -d <destination directory>
    -c Clear destination directory
    -a <archive> specify alternate archive name
    -b <path> specify codebase
    -v Verbose
END
    exit;
}
