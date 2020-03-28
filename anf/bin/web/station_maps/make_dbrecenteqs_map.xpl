#
# make_dbrecenteqs_map
# script to make an Antelope dbrecenteqs or dbevents-style map
# Kent Lindquist
# Lindquist Consulting
# 2004
#

#require "getopts.pl" ;
use Getopt::Long;
require "dbrecenteqs.pm";
require "dbgmtgrid.pm";
require "winding.pm";
require "compass_from_azimuth.pm";
use Datascope;

elog_init( $0, @ARGV );
$Program = (parsepath( $0 ))[1];

$State{pf} = "make_dbrecenteqs_map";
$opt_v = 0;
$opt_l = 0;
$opt_f = 0;
$opt_F = 0;
$opt_t = 0;
$opt_s = 0;
$opt_c = 0;
$opt_r = 0;

$result = GetOptions ("p=s"=> \$State{pf},
                        "f=s"  => \$opt_f,
                        "F=s"  => \$opt_F,
                        "t=s"  => \$opt_t,
                        "l=s"  => \$opt_l,
                        "s=s"  => \$opt_s,
                        "c=s"  => \$opt_c,
                        "r=i"  => \$opt_r,
                        "v"  => \$opt_v);



if ( @ARGV != 1 ) {
    die ( "Usage: $Program [-v] [-p pffile] " .
        "[-f focus_station_expression | -F focus_station_regex] " .
        "[-t workdir] [-l log_script] " .
            "[-s stations_dbname] [-c lon:lat] [-r degrees] psfile\n" );

} else {

    $psfile = $ARGV[0];
    $psfile .= ".ps" unless $psfile =~ /\.ps$/;


}

$pf_change_time = "1162590875";

if( pfrequire( $State{pf}, $pf_change_time ) < 0 ) {

    elog_die( "Your parameter file '$State{pf}' is out of date. " .
          "Please update it before continuing.\n" );
}

if( $opt_l ) {

    set_scriptlog( $opt_l );
}

if( $opt_v ) {

    elog_notify( "Setting gmt PROJ_LENGTH_UNIT to inch\n" );
}

system( "gmt set PROJ_LENGTH_UNIT=inch" );

setup_State();

if( $opt_t ) {

    $State{workdir} = $opt_t;
    mkdir( $State{workdir}, 0755 );

    if( ! -e $State{workdir} || ! -d $State{workdir} ) {

        die( "$State{workdir} doesn't exist or isn't a directory! Bye." );
    }
}

$hashref = pfget( $State{pf}, "mapspec" );
%Mapspec = %{$hashref};

if( $opt_c ) {

    ( $Mapspec{lonc}, $Mapspec{latc} ) = split( /:/, $opt_c );
}

if( $opt_f ) {

    $Mapspec{focus_sta_expr} = $opt_f;

} elsif( $opt_F ) {

    $Mapspec{focus_sta_expr} = "sta =~ /^$opt_F\$/";
}

if( $opt_r ) {

    $Mapspec{right_dellon} = $opt_r;
    $Mapspec{up_dellat} = $opt_r;
    $Mapspec{down_dellat} = -1 * $opt_r;
    $Mapspec{left_dellon}  = -1 * $opt_r;
}

if( $opt_s ) {

    $Mapspec{stations_dbname} = $opt_s;
}

%Mapspec = %{setup_index_Mapspec( \%Mapspec )};

$Mapspec{psfile} = "$psfile";
$Mapspec{pixfile} = "$psfile";
$Mapspec{pixfile} =~ s/.ps$/.$Mapspec{format}/;

$Mapspec{mapname} = (parsepath($Mapspec{psfile}))[1];
$Mapspec{source} = "dynamic";
$Mapspec{contour_mode} = "grddb";
$Mapspec{mapclass} = "index";

plot_basemap( \%Mapspec, "first" );
plot_contours( \%Mapspec, "middle" );
plot_coastlines( \%Mapspec, "middle" );
plot_lakes( \%Mapspec, "middle" );
plot_rivers( \%Mapspec, "middle" );
plot_national_boundaries( \%Mapspec, "middle" );
plot_state_boundaries( \%Mapspec, "middle" );
plot_linefiles( \%Mapspec, "middle" );
plot_basemap( \%Mapspec, "middle" );
if( $opt_s ) {
    plot_stations( \%Mapspec, "middle" );
}
plot_cities( \%Mapspec, "last" );

if( $State{pixfile_conversion_method} ne "none" ) {

    %Mapspec = %{pixfile_convert( \%Mapspec )};
    write_pixfile_pffile( \%Mapspec );
}

if( ( ! $opt_t ) && $State{"workdir"} && $State{"workdir"} ne "" ) {
        system( "/bin/rm -rf $State{workdir}" );
}
