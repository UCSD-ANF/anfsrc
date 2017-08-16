%-----------------------------------------------------
%  Make a text archive of the best reg and tel events found
%-----------------------------------------------------
%
% A Matlab script for plotting events in polar plots
% reyes@ucsd.edu
%
%-----------------------------------------------------

function info_pf( event_list )

    global station ;
    global imgdir ;
    global latitude ;
    global longitude ;


    workdir = [ imgdir '/' station '/' ] ;
    if ~exist(workdir, 'dir')
        % Folder does not exist so create it.
        mkdir( workdir );
    end

    file = [ imgdir '/' station '/' station '_info.pf' ] ;

    reg_ev_total = 0 ;
    tel_ev_total = 0 ;
    reg_ev_mag = -1 ;
    tel_ev_mag = -1 ;
    % my_local = struct() ;
    % my_tele = struct() ;
    reg_ev_mag = 0 ;
    reg_ev_lat = 0 ;
    reg_ev_lon =  0 ;
    reg_ev_time = 0 ;
    reg_ev_distance = 0 ;
    reg_ev_arrivaltime = 0 ;
    tel_ev_mag = 0 ;
    tel_ev_lat = 0 ;
    tel_ev_lon = 0 ;
    tel_ev_time = 0 ;
    tel_ev_distance = 0 ;
    tel_ev_arrivaltime = 0 ;

    for i=1:length(event_list)
        if strcmp( 'regional', event_region(latitude, longitude, event_list( i ), 10) )
            % my_local( i ) =  event_list( i ) ;
            reg_ev_total = reg_ev_total + 1 ;
            if reg_ev_total == 0 || event_list( i ).mag > reg_ev_mag
                reg_ev_mag = event_list( i ).mag ;
                reg_ev_lat = event_list( i ).Lat ;
                reg_ev_lon = event_list( i ).Lon ;
                reg_ev_time = event_list( i ).time ;
                reg_ev_arrivaltime = event_list( i ).arrival ;
                reg_ev_distance = event_list( i ).delta ;
            end
        else
            % my_tele( i ) = event_list( i ) ;
            tel_ev_total = tel_ev_total + 1 ;
            if tel_ev_total == 0 || event_list( i ).mag > tel_ev_mag
                tel_ev_mag = event_list( i ).mag ;
                tel_ev_lat = event_list( i ).Lat ;
                tel_ev_lon = event_list( i ).Lon ;
                tel_ev_time = event_list( i ).time ;
                tel_ev_arrivaltime = event_list( i ).arrival ;
                tel_ev_distance = event_list( i ).delta ;
            end
        end
    end

    fprintf( 'Open file %s\n', file ) ;
    fileID = fopen( file ,'w');

    format long ;

    fprintf( 'Save information to file %s\n', file ) ;

    fprintf( fileID, '# Information for station %s\n', station ) ;
    fprintf( fileID, epoch2str( now, '# Done on %l:%M:%S\n\n' ) ) ;

    fprintf( fileID, 'large_total_events      %d\n', tel_ev_total ) ;
    fprintf( fileID, 'large_wform_delay       %d\n', tel_ev_arrivaltime - tel_ev_time ) ;
    fprintf( fileID, 'large_wform_distance    %d\n', tel_ev_distance ) ;
    fprintf( fileID, 'large_wform_eventnumber %d\n', tel_ev_mag) ;
    fprintf( fileID, 'large_wform_hhmmss      &Tbl{\n' ) ;
    fprintf( fileID, epoch2str( tel_ev_time, '\t%l:%M:%S\n' ) ) ;
    fprintf( fileID, '}\n' ) ;

    fprintf( fileID, 'large_wform_mmddyyyy    &Tbl{\n' ) ;
    fprintf( fileID, epoch2str( tel_ev_time, '\t%D\n' ) ) ;
    fprintf( fileID, '}\n' ) ;

    fprintf( fileID, 'regional_total_events   %d\n', reg_ev_total ) ;
    fprintf( fileID, 'regional_wform_delay    %d\n', reg_ev_arrivaltime - reg_ev_time ) ;
    fprintf( fileID, 'regional_wform_distance %d\n', reg_ev_distance ) ;
    fprintf( fileID, 'regional_wform_eventnumber  %d\n', reg_ev_mag ) ;
    fprintf( fileID, 'regional_wform_hhmmss   &Tbl{\n' ) ;
    fprintf( fileID, epoch2str( reg_ev_time, '\t%l:%M:%S\n' ) ) ;
    fprintf( fileID, '}\n' ) ;

    fprintf( fileID, 'regional_wform_mmddyyyy &Tbl{\n' ) ;
    fprintf( fileID, epoch2str( reg_ev_time, '\t%D\n' ) ) ;
    fprintf( fileID, '}\n' ) ;

    fprintf( 'Done writing file %s\n', file ) ;

    fclose(fileID);



end
