sub calibration_mail_handler {
    use Mail::Mailer;
    use sysinfo;
    use archive;

    my @stations= undef;
    my $sta     = undef;
    my $mailer  = undef;
    my $mail_body= undef;
    my $record  = undef;
    my $mail_cc = undef;
    my $mail_from= undef;
    my $mail_sub= undef;
    my $mail_to = undef;
    my $run     = undef;
    my $error   = undef;

    my $subset  = undef;
    my @db      = undef;
    my @dbsubset= undef;
    my @hd      = undef;

    my( $message, $pfarray ) = @_;

    @db = dbopen( %{$pfarray}->{database}, "r+" );
    @db = dblookup( @db, "", %{$pfarray}->{table}, "", "" );
    @hd = dbquery( @db, "dbTABLE_FIELDS");

    my( @body ) = @{$message->body()};
    my $subject = $message->head->get("Subject");
    my $from = $message->get("From");
    my $date = $message->head->get("Date");

    if ( %{$pfarray}->{log} ) {
        print "-------NEW---------\n";
        print $from;
        print $date;
        print $subject;
        print @body;
        print "-------END---------\n";
    }

    #
    #Start body of 
    #report e-mail
    #
    $mail_body  = "Report from $0 \n"; 
    $mail_body .= "Date: ". localtime(). "\n" ;
    $mail_body .= "On system: ". my_hostname(). "\n" ;
    $mail_body .= "Running OS: ". my_os(). "\n" ;
    $mail_body .= "original e-mail    from: $from " ;
    $mail_body .= "original e-mail    date: $date " ;
    $mail_body .= "original e-mail Subject: $subject ";

    foreach(@body) {    
        if( /^(#|=|%|>).*/i ) { next; }
        if( /^<html>/i ) { last; }
        elsif( /^(\w{4},?\s+)+$/i ) {
            $_ =~ s/,//g;
            $_ =~ s/;//g;
            push(@stations,split(/\s+/) );
        }
    }

    #get unique
    @stations = get_unique(@stations);

    for ($i=0; $i<=$#stations; $i++) {
        $sta = uc(@stations[$i]);
        if( ! $sta ) { delete @stations[$i]; }
        if( $sta =~ /^\s+$/ ) { delete @stations[$i]; }
        elsif( %{$pfarray}->{exclude} =~ /$sta/ ) {
            $mail_body .= "\tStation ($sta) in exclude parameter".%{$pfarray}->{exclude}.".\n";
            delete @stations[$i];
            next;
        }
        $sta =~ s/\s+$//;
        $stations[$i] = $sta;


        $mail_body .= "Verify database for station: [ $sta ]\n" ;

        $subset = "sta =~ /$sta/ && (endtime == NULL || endtime > ".now().")";
        @dbsubset = dbsubset(@db,$subset);
        $rq = dbquery( @dbsubset, "dbRECORD_COUNT");

        $mail_body .= "--$sta-------------------------------\n";
        if ( $rq > 0 ) {
            for ( $dbsubset[3] = 0 ; $dbsubset[3] < $rq ; $dbsubset[3]++ ) {
                foreach (@hd) { $mail_body .= " ".dbgetv (@dbsubset,$_)." |"; }
                $mail_body .= "\n";
            }
        }
        else {
            delete @stations[$i];
            $subset = "sta =~ /$sta/";
            @dbsubset = dbsubset(@db,$subset);
            $rq = dbquery( @dbsubset, "dbRECORD_COUNT");
            if ( $rq > 0 ) { $mail_body .= "\n\tERROR: Station is offline ($sta).\n\n"; }
            else { $mail_body .= "\n\tERROR: Can't find station ($sta).\n\n";}
        }
        $mail_body .= "-------------------------------------\n\n";
    }

    dbclose( @db );

    if ( @stations ) {
        $run .= " /opt/antelope/4.11/bin/q330_calibration -m ".%{$pfarray}->{mail}." ".%{$pfarray}->{orb}." ".%{$pfarray}->{db}." @stations &";
        $mail_body .= "\n\t$run\n\n";
        system($run);
    }
    else {
        $error .= "ERROR:";
        $mail_body .= "\n\t$error\n\t\tNo stations selected \n\n";
    }

    if(%{$pfarray}->{include_body}) {
        $mail_body .= "----------------------\n" ;
        $mail_body .= "Original Message:\n" ;
        $mail_body .= "----------------------\n" ;
        foreach (@body) { 
            $mail_body .= ">$_";
        }
        $mail_body .= "----------------------\n";
    }


    $mail_body .= "\n" ;
    $mail_body .= "--\n" ;
    $mail_body .= "Automatic E-mail Parser Script\n" ;
    $mail_body .= "Admin: ".%{$pfarray}->{admin_mail}."\n" ;

    #
    # Send report 
    #
    if( %{$pfarray}->{report_to} ) { $mail_to = %{$pfarray}->{report_to};}
    else { $mail_to =  $message->get("From");}

    $mail_sub = %{$pfarray} ->{mail_subject};
    if ( $error ) { $mail_sub = $error . $mail_sub; }

    if( %{$pfarray}->{cc_sender} )   { $mail_cc  = $message->get("From"); }

    if( %{$pfarray}->{report_from} ) { $mail_from = %{$pfarray}->{report_from}; }
    else { $mail_from = $message->get("From"); }

    $mailer = Mail::Mailer->new();
    $mailer->open({ From    => $mail_from ,
                    To      => $mail_to,
                    Cc      => $mail_cc,
                    Subject => $mail_sub,
                    })
        or print "Can't open: $!\n";
    print $mailer $mail_body;
    $mailer->close();

    if( %{$pfarray}->{log} ) { print $mail_body; }
    else{print "CALIBRATION FOR: [ @stations ]\n";}
}

1; # Make require happy!
