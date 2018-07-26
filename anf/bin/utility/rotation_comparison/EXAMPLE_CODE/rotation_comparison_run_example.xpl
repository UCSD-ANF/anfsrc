#   Copyright (c) 2016 Boulder Real Time Technologies, Inc.
#
#   Written by Rebecca Rodd
#
#   This software may be used freely in any way as long as
#   the copyright statement above is not removed.

use Cwd;
use Datascope ;
use File::Path;

#
# SIMPLE SCRIPT TO RUN DEMO CODE FOR ROTATION_COMPARISON
#

$path = "$ENV{ANF}/example/rotation_comparison/";
$need_link = 0;

print "\nRUN ROTATION_COMPARISON DEMO\n";


# TEST FOR GLOBAL SETTINGS
if ( exists($ENV{ANF}) ) {
    print "\nANTELOPE VERSION: $ENV{ANF}\n" ;
} else {
    die "\nNO ANTELOPE CONFIGURED IN ENVIRONMENT\n" ;
}

# ALTERNATIVE DIRECTORY TO USE FOR TEST
if ( scalar @ARGV ) {
    $path = abspath($ARGV[0]) ;
    $need_link = 1 ;
    makedir($path) unless -d $path ;
}


# TEST FOR EXAMPLE DIRECTORY
#die "\nNO DIRECTORY FOR EXAMPLE: [$path]\n"  unless -d $path;


# GO TO DIR
print "\nCHANGE TO DIRECTORY: [$path]\n";
chdir $path or die "Could not change to directory '$path' $!";


# CLEAN DIRECTORY
#foreach ( "$path/rotation_comparison_results") {
#    if ( -e $_ ) {
#        print "\nREMOVE TEMP FOLDER: [$_]\n";
#        rmtree $_;
#    }
#}


# RUN EXAMPLES
foreach (1) {
    print "\nSTART EXAMPLE $_\n";
    $newpath = "$path/EXAMPLE_$_";
    chdir $newpath or die "Could not change to directory '$path' $!";
    print "\nrotation_comparison -v -o example 1\n";
    $return_value = system( "rotation_comparison -v -o example 1" );

    print "\nDONE WITH EXAMPLE\n";
}
print "\nDONE ROTATION_COMPARISON DEMO!\n";
