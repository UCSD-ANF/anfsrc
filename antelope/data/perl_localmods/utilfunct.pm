package utilfunct ;

require Exporter;   
@ISA = ('Exporter');

@EXPORT=qw(prettyprint dbdebug check_tables getparam check_lock df_avail) ;

use strict ;
use sysinfo ; 
use Datascope ;

sub prettyprint {
	my $val = shift;
	my $prefix = "";
	if (@_) { $prefix = shift ; }

	if (ref($val) eq "HASH") {
		my @keys = sort ( keys  %$val );
		my %hash = %$val;
		foreach my $key (@keys) {
			my $newprefix = $prefix . "{". $key . "}" ;
			prettyprint ($hash{$key}, $newprefix) ;
		}
	} elsif (ref($val) eq "ARRAY") {
		my $i = 0;
		my @arr = @$val;
		foreach my $entry ( @$val ) {
			my $newprefix = $prefix . "[". $i . "]" ;
			prettyprint ($arr[$i], $newprefix) ;
			$i++;
		}
	} else {
#		print $prefix, " = ", $val, "\n";
        elog_notify("	$prefix  =  $val");
	}
}


sub dbdebug { #dbdebug(@db)
    my(@db) = @_;
    my($key,$field) ;
    my(@fields) ;
    my(%table) ;
    
    @fields = dbquery(@db,"dbTABLE_FIELDS");
    
    foreach $field (@fields) {
        elog_notify(sprintf("%s	%s",$field,dbgetv(@db,$field)));
    }
}


sub check_tables { # $problems = &check_tables($db,$problems,@tables);
    my ($db,$problems,@tables) = @_ ;
    my @db ; 
    my $table;

    @db = dbopen($db,"r") ;

    foreach $table (@tables) {
        @db      = dblookup(@db,0,$table,0,0);
        if ($db[1] < 0) {
            $problems++;
            elog_complain("$table not defined in schema") ;
        }        
        if (! dbquery(@db,"dbTABLE_PRESENT")) {
            $problems++;
            elog_complain("Problem $problems -	No records in $table table of $db") ;
        }
    }
    dbclose(@db);
    return($problems);
}

sub getparam { # %pf = getparam($Pf, $verbose, $debug);
    my ($Pf, $verbose, $debug) = @_ ;
    my ($subject,$ref);
#     my (@keys);
    my (%pf) ;
    
    $ref = pfget($Pf, "");
    %pf = %$ref ;

    elog_notify("\n Parameter file	$Pf\n") if $verbose;
    elog_notify("$Pf	ref($ref)") if $debug;
    
#     @keys = sort( keys %pf);

    &prettyprint(\%pf) if $verbose;
        
    elog_notify("\n ") if $verbose;
            
    return (%pf) ;
}

sub check_lock { # &check_lock($prog_name,$vebose)
    my ($prog_name,$verbose) = @_ ;
    my ($lockfile);

    elog_notify("check_lock ( $prog_name )") if $verbose;
    $lockfile = ".$prog_name" ;
    open ( LOCK, ">$lockfile" ) ;
    if ( flock(LOCK, 6 ) != 1 ) {
        elog_complain ( "Can't lock file '$lockfile'.\n\n");
        elog_die("$prog_name or another process which locks $prog_name already running" ) ;
    }
    print LOCK "$$\n" ;
    return();
}

sub df_avail { # ( $Mb_avail, $Mb_total ) = &df_avail($db) ; 
    my ( $db ) = @_ ;
    my ($device,$Mb_avail,$Mb_total,$datadir);
    my (@db);
    
    @db       = dbopen  ( $db, "r");
    @db       = dblookup( @db,"","wfdisc","","");
    $datadir  = dbquery(@db,"dbTABLE_DIRNAME");
    dbclose (@db) ;
    

    if ( -e $datadir ) {
        my %statvfs = statvfs($datadir) ; 
        $device   = $statvfs{id} ; 
        $Mb_avail = $statvfs{Mb_avail} ;
        $Mb_total = $statvfs{Mb_total} ;
    } else { 
        $device    = "df fails" ; 
        $Mb_avail     = 0 ;
        $Mb_total  = 0 ;
    }
    return ( $Mb_avail, $Mb_total ) ;
}

