sub construction_mail_handler {

    #{{{ Def variables
    use Mail::Mailer;
    use sysinfo;
    my $sta    = undef;
    my $year   = undef;
    my $month  = undef;
    my $day    = undef;
    my $lddate = undef;
    my $elev   = undef;
    my $unit   = undef;
    my $lat    = undef;
    my $lon    = undef;
    my $epoch  = undef;
    my $yday   = undef;

    my $old_sta    = undef;
    my $old_elev   = undef;
    my $old_lat    = undef;
    my $old_lon    = undef;
    my $old_yday   = undef;
    my $old_lddate = undef;

    my $results   = undef;
    my $mailer    = undef;
    my $mail_body = undef;
    my $errors    = 0;
    my $update    = undef;
    my $record    = undef;
    my $mail_cc   = undef;
    my $mail_from = undef;
    my $mail_sub  = undef;
    my $mail_to   = undef;

    my $rq  = undef;
    my @hd  = undef;
    my @db  = undef;
    my $concat = ''; 
    #}}}

    my( $message, $pfarray ) = @_;

    #
    # Get all info from message
    #
    my $from = $message->get("From");
    my $subject = $message->head->get("Subject");
    my $date = $message->head->get("Date");
    my $type = $message->head->get("Content-Transfer-Encoding");
    my @body = @{$message->body()};
    $concat .= "$_" foreach @body;



    if ($type =~ /quoted-printable/ ) {
        #{{{ Fix quoted-printable text

        $concat =~ s/=\n//g;
        $concat =~ s/=0A/\n/g;
        $concat =~ s/=0D/\n/g;

        $concat =~ s/=0[0-9A-F]//g;

        $concat =~ s/=1[0-9A-F]/ /g;

        $concat =~ s/=20/ /g;
        $concat =~ s/=21/\!/g;
        $concat =~ s/=22/\"/g;
        $concat =~ s/=23/\#/g;
        $concat =~ s/=24/\$/g;
        $concat =~ s/=25/\%/g;
        $concat =~ s/=26/\&/g;
        $concat =~ s/=27/\'/g;
        $concat =~ s/=28/\(/g;
        $concat =~ s/=29/\)/g;
        $concat =~ s/=2A/\*/g;
        $concat =~ s/=2B/\+/g;
        $concat =~ s/=2C/\,/g;
        $concat =~ s/=2D/\-/g;
        $concat =~ s/=2E/\./g;
        $concat =~ s/=2F/\//g;

        $concat =~ s/=3A/\:/g;
        $concat =~ s/=3B/\;/g;
        $concat =~ s/=3C/\</g;
        $concat =~ s/=3D/\=/g;
        $concat =~ s/=3E/\>/g;
        $concat =~ s/=3F/\?/g;
        $concat =~ s/=3[0-9A-F]//g;

        $concat =~ s/=40/\@/g;
        $concat =~ s/=4[0-9A-F]//g;

        $concat =~ s/=5B/\[/g;
        $concat =~ s/=5C/\\/g;
        $concat =~ s/=5D/\]/g;
        $concat =~ s/=5E/\^/g;
        $concat =~ s/=5F/\_/g;
        $concat =~ s/=5[0-9A-F]//g;

        $concat =~ s/=60/\`/g;
        $concat =~ s/=6[0-9A-F]//g;

        $concat =~ s/=7B/\{/g;
        $concat =~ s/=7B/\{/g;
        $concat =~ s/=7C/\|/g;
        $concat =~ s/=7D/\}/g;
        $concat =~ s/=7E/\~/g;
        $concat =~ s/=7[0-9A-F]//g;

        $concat =~ s/=8[0-9A-F]//g;
        $concat =~ s/=9[0-9A-F]//g;
        $concat =~ s/=A[0-9A-F]//g;
        $concat =~ s/=B[0-9A-F]//g;
        $concat =~ s/=C[0-9A-F]//g;
        $concat =~ s/=D[0-9A-F]//g;
        $concat =~ s/=E[0-9A-F]//g;
        $concat =~ s/=F[0-9A-F]//g;

        #}}}
    }

    if ( %{$pfarray}->{verbose} ) {
        print "-------NEW---------\n";
        print "FROM: $from\n";
        print "DATE: $date\n";
        print "SUBJECT: $subject\n";
        print "TYPE: $type\n";
        print "$concat\n";
        print "-------END---------\n";
    }

    @body = split(/\n/,$concat);

    #
    # Build body of report
    #
    $mail_body  = "Report from $0 \n"; 
    $mail_body .= "Date: ". localtime(). "\n" ;
    $mail_body .= "On system: ". my_hostname(). "\n" ;
    $mail_body .= "Running OS: ". my_os(). "\n" ;
    $mail_body .= "\te-mail    from: $from \n" ;
    $mail_body .= "\te-mail    date: $date \n" ;
    $mail_body .= "\te-mail Subject: $subject \n";

    foreach(@body) {    
        if( /.*Station Code\s*(=|:)/i && ! $sta ) {
                $mail_body .= "Parsing line: $_" if %{$pfarray}->{verbose};
            if( /.*Station Code\s*(=|:)\s*(\w+).*/i ) {
                $sta= $2;
                $mail_body .= "\tsta => $sta\n" if %{$pfarray}->{verbose}; 
            }
        }
        elsif( /.*Date\s*(=|:)/i && (!$year || !$month || !$day) ) {
                $mail_body .= "Parsing line: $_" if %{$pfarray}->{verbose}; 
            if( /.*Date\s*(=|:)\s*(\d{2,4})\s(\d{1,2})\s(\d{1,2}).*/i ) {
                $year  = $2;
                $month = $3;
                $day   = $4;
                $mail_body .= "\tyear  => $year \n"  if %{$pfarray}->{verbose};
                $mail_body .= "\tmonth => $month\n"  if %{$pfarray}->{verbose};
                $mail_body .= "\tday   => $day  \n"  if %{$pfarray}->{verbose};
            }
        }
        elsif( /.*Elevation\s*(:|=)/i && ! $elev ) {
                $mail_body .= "Parsing line: $_"  if %{$pfarray}->{verbose};
            if( /.*Elevation\s*(:|=)\s*(-*\d+)\s?(\w{0,3}).*/i ) {
                $elev = $2;
                $unit = $3;
                $mail_body .= "\telev  => $elev\n"  if %{$pfarray}->{verbose};
                $mail_body .= "\tunits => $unit\n"  if %{$pfarray}->{verbose};
            }
        }
        elsif( /.*GPS\s*(=|:)/i && (!$lat || !$lon)  ) {
                $mail_body .= "Parsing line: $_"  if %{$pfarray}->{verbose};
            if( /(-?[0-9]{1,3}\.[0-9]{1,6})[^0-9]*(-?[0-9]{1,3}\.[0-9]{1,6})/i ) {
                $lat = $1;
                $lon = $2;
                $mail_body .= "\tlat => $lat\n"  if %{$pfarray}->{verbose};
                $mail_body .= "\tlon => $lon\n"  if %{$pfarray}->{verbose};
            }
        }
    }

    #
    #Fix sta name
    #force upper case
    #
    $sta = uc($sta);

    #
    #Fix elevation
    #
    $unit = uc($unit);
    if( $unit ne 'KM' ) {
        $elev = $elev/1000;
    }

    #
    #Fix GPS
    #
    $lat = $lat !~ /-/ ? $lat : -1 * $lat;
    $lon = $lon =~ /-/ ? $lon : -1 * $lon;
    
    #
    #Convert time
    #to yyyyjjj
    #
    if($year !~ /\d{4}/ || $month !~ /\d{1,2}/ || $day !~ /\d{1,2}/ ) {
        $date =~ /\w+, (\d{1,2}) (\w+) (\d{4})/;
                $year  = $3;
                $month = $2;
                $day   = $1;
                $mail_body. "There is an error with the date field.\n";
                $mail_body. "Using date on e-mail.\n";
                $mail_body. "Found year=$year , month=$month and day=$day\n";
        $epoch = str2epoch( "$day $month $year 0:00:00" );
    }
    else { 
        $year  = sprintf("%04d", $year);
        $month = sprintf("%02d", $month);
        $day   = sprintf("%02d", $day);
        $epoch = str2epoch( "$year-$month-$day 0:00:00" );
    }
    $yday  = yearday($epoch);
    $lddate= now();

    #
    #Check variables
    #
    if($lat !~ /-?\d{1,3}?\.\d*/) { 
        $mail_body .= "ERROR: Latitude not valid. ($lat)\n" ;
        $errors ++;
    }
    if(abs($lat) < 20 || 80 < abs($lat) || $lat =~ /-/ ) { 
        $mail_body .= "ERROR: Latitude out of bounds. ($lat)\n" ;
        $errors ++;
    }
    if($lon !~ /-?\d{1,3}?\.\d*/) { 
        $mail_body .= "ERROR: Longitude not valid. ($lon)\n" ;
        $errors ++;
    }
    if(abs($lon) < 50 || 180 < abs($lon) || $lon !~ /-/ ) { 
        $mail_body .= "ERROR: Longitude out of bounds. ($lon)\n" ;
        $errors ++;
    }
    if($elev !~ /-?\d{1,2}?\.*\d*/) { 
        $mail_body .= "ERROR: Eleveation not valid. ($elev)\n" ;
        $errors ++;
    }
    if($sta !~ /\w{1,9}/ ) { 
        $mail_body .= "ERROR: Station name not valid. ($sta)\n" ;
        $errors ++;
    }
    if($yday !~ /\d{7}/) { 
        $mail_body .= "ERROR: Ondate not valid. ($yday)\n" ;
        $errors ++;
    }



    $mail_body .= "\nFrom email: [ sta=$sta | yday=$yday | lat=$lat  | lon=$lon  | elev=$elev | lddate=$lddate ]\n" ;

    if (!$errors) {
#{{{
        #$mail_body .= "ADDING: [ $sta | $yday | $lat  | $lon  | $elev | $lddate ]\n" ;
        @db = dbopen( %{$pfarray}->{database}, "r+" );
        @db = dblookup( @db, "", "site", "", "" );
        $record = dbfind(@db, "sta =~ /$sta/", -1);
        if( '-1' == $record ) {
            $mail_body .= "\tERROR: Can't understand station name ($sta). \n";
            $errors ++;
        }
        elsif( '-2' == $record ) {
            $mail_body .= "\nADDING: [ $sta | $yday | $lat  | $lon  | $elev | $lddate ]\n" ;
            $results = dbaddv( @db, 
                "sta", $sta, 
                "ondate", $yday, 
                "lat", $lat, 
                "lon", $lon,
                "elev", $elev,
                "lddate", $lddate);
            $mail_body .= "\tNew line #".$results."\n";
        }
        else {
            $mail_body .= "\n\t**** Station $sta already in database line $record.**** \n";

            @db = dbsubset(@db, "sta=='$sta'" );
            @db[3]=0;
            ($old_sta,$old_yday,$old_lat,$old_lon,$old_elev,$old_lddate) = dbgetv(@db,qw/sta ondate lat lon elev lddate/);
            $mail_body .= "OLD: [ $old_sta | $old_yday | $old_lat  | $old_lon  | $old_elev | $old_lddate]\n" ;
            if ($yday >= $old_yday) {
                $mail_body .= "Updating!\n" ;
                $results = dbputv(@db, 
                    "ondate", $yday, 
                    "lat", $lat, 
                    "lon", $lon,
                    "elev", $elev,
                    "lddate", $lddate);
                $mail_body .= "UPDATE line# $results: [ $sta | $yday | $lat  | $lon  | $elev | $lddate ]\n" ;
            }
            else { 
                $mail_body .= "ERROR: Table values are more recent than email.\n";
            }
            $update = 1;
        }   
        dbclose( @db );

        @db = dbopen( %{$pfarray}->{database}, "r" );
        @db = dblookup( @db, "", "site", "", "" );
        @db = dbsubset(@db, "sta=='$sta'" );
        $rq = dbquery( @db, "dbRECORD_COUNT");
        @hd = dbquery( @db, "dbTABLE_FIELDS");
        $mail_body .= "\nVerifying entries in database for sta=='$sta'\n";
        $mail_body .= "\tFound $rq result(s):\n";
        $mail_body .= "\t";
        foreach (@hd) { $mail_body .= " $_ |"; }
        $mail_body .= "\n";
        for ( $db[3] = 0 ; $db[3] < $rq ; $db[3]++ ) {
            $mail_body .= "\t";
            foreach (@hd) { $mail_body .= " ".dbgetv (@db,$_)." |"; }
            $mail_body .= "\n";
        }
        dbclose( @db);

#}}}
    } 

    $mail_body .= "\n" ;
    $mail_body .= "--\n" ;
    $mail_body .= "Automatic E-mail Parser Script\n" ;
    $mail_body .= "Script Author: reyes\@ucsd.edu\n" ;

    #
    # Send report 
    #
    if( %{$pfarray}->{report_to} ) {
        #{{{
        if( %{$pfarray}->{report_to} ) { $mail_to = %{$pfarray}->{report_to};}
        else { $mail_to =  $message->get("From");}

        $mail_sub = %{$pfarray} ->{mail_subject};
        if( $errors ) { $mail_sub .= " - $errors ERROR(S)"; }
        if( $update ) { $mail_sub .= " - UPDATE"; }

        if( %{$pfarray}->{cc_sender} )   { $mail_cc  = $message->get("From"); }

        if( %{$pfarray}->{report_from} ) { $mail_from = %{$pfarray}->{report_from}; }
        else { $mail_from = $message->get("From"); }

        $mailer = Mail::Mailer->new();
        $mailer->open({ From    => $mail_from ,
                        To      => $mail_to,
                        Cc      => $mail_cc,
                        Subject => "$mail_sub - $sta",
                      }) or print "Can't open Mail::Mailer: $!\n";

        print $mailer $mail_body;
        $mailer->close();
        #}}}
    } 

    if( $errors ) { print " - $errors ERROR(S) in $sta"; }
    print "\t[ $sta | $yday | $lat  | $lon  | $elev | $lddate ]\n";
}

1; # Make require happy!
