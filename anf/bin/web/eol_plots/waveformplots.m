%-----------------------------------------------------
%  Produce traces of waveforms
%-----------------------------------------------------
%
% Extract a segment of data for a particular station
% and plot each channel on the figure.
% reyes@ucsd.edu
%
%-----------------------------------------------------
%
function waveformplots( ev_type, imgdir, sta, chans, starttime, endtime, sta_time, sta_endtime, ev_database, ev_clustername, wf_database, wf_clustername )

    ImageDPI=200;
    set_fig( 1 )
    new_height = 0 ;

    dbObj = dbcentral( wf_database, wf_clustername, sta_time, sta_endtime ) ;
    database = dbcentral_time( dbObj, starttime ) ;

    db0 = dbopen( database, 'r' ) ;

    fprintf( 'Look in %s.wfdisc for %s \n', database, sta ) ;

    %--- Open the wfdisc
    db1 = dblookup_table( db0,'wfdisc' ) ;
    db2 = dbsubset( db1, ['sta=="' sta '"'] ) ;
    db3 = dbsubset( db2, ['chan=~/' chans '/'] ) ;
    wfrecords = dbquery( db3, 'dbRECORD_COUNT' ) ;


    if wfrecords < 3

        fprintf( 'No data in %s.wfdisc for %s \n', database, sta ) ;

    else

        try
            tr = trload_css( db3, starttime, endtime ) ;

            if( strcmp( ev_type, 'regional' ) )
                trfilter( tr, 'BW 0.1 4 3.0 4' ) ;
            else
                trfilter( tr, 'BW 0.05 4 1.0 4' ) ;
            end

            trapply_calib( tr ) ;
            nrecs = dbquery( tr,'dbRECORD_COUNT' ) ;
            %for i=1:nrecs,
            %    tr.record = i-1;
            %    %data_for_y = trextract_data(tr) ;
            %    data_for_y = data_for_y - ( sum( data_for_y ) / length( data_for_y ) ) ;
            %    max_y(i) = max( abs( data_for_y ) ) ;
            %end

            %my_max_y = max( abs( max_y ) ) ;
            %my_min_y = my_max_y * -1 ;

            pl_min = [ 0.05 0.05 ] ;
            pl_max = [ 0.98 0.98 ] ;
            pl_gap = [ 0.01 0.01 ] ;

            Xmin = pl_min(1) ;
            Ymin = pl_min(2) ;
            Xmax = pl_max(1) ;
            Ymax = pl_max(2) ;
            Xgap = pl_gap(1) ;
            Ygap = pl_gap(2) ;

            Xsize = ( Xmax - Xmin ) ;
            Ysize = ( Ymax - Ymin ) ;

            Xbox = Xsize - Xgap ;
            Ybox = Xsize - Ygap ;

            for i=1:nrecs,

                h = subplot( nrecs,1,i ) ;

                tr.record = i-1;
                data = trextract_data(tr) ;
                % Normalize between 0 and 1
                data = (data - min(data)) / ( max(data) - min(data) ) ;

                %data = trextract_data(tr) ;
                %data = data - ( sum( data ) / length( data ) ) ;

                xtime = 1/(dbgetv(tr,'samprate'))*[1:length(data)];

                %--- Get data in mins from orid time
                xtimeo = ( dbgetv(tr,'endtime') - dbgetv(tr,'time') ) / 60 ;

                %plot(xtimeo,data) ;
                plot(data) ;

                %set( h, 'YLim', [ my_min_y my_max_y ] ) ;
                set( h, 'YLim', [ 0 1 ] ) ;

                this_pos = get( h, 'Position' ) ;

                new_pos(1) = Xmin ;
                new_pos(2) = this_pos(2) + ( 0.07 * i ) ;
                new_pos(3) = Xsize ;

                if new_height == 0
                    new_pos(4) = this_pos(4) ;
                    new_height = new_pos(4) ;
                else
                    new_pos(4) = new_height ;
                end

                set( h, 'Position', [ new_pos(1) new_pos(2) new_pos(3) new_pos(4) ] ) ;

                hold on ;

                %%--- Only add time stamp on last (bottom) wform display
                %if i < nrecs
                %    set( gca, 'XTickLabel', [] ) ;
                %end
                set( gca, 'XTickLabel', [] ) ;

                set( gca, 'xtick', [] ) ;
                set( gca, 'xgrid', 'on' ) ;

                %yy = get(gca,'ylim') ;

                %%grid2 on x off y ;
                mylabel = dbgetv( tr, 'chan' ) ;
                ylabel( mylabel, 'FontSize', 12 ) ;
                set( gca,'yticklabel',[] ) ;
                set( gca, 'xtickMode', 'auto' ) ;

                %%--- Offset so text is readable
                %dy = 0.025*(yy(2)-yy(1)) ;

                %%for a=1:length( arr_time_mins ),
                %%    %--- Hack to solve Matlab casting of strings and cells
                %%    if length( arr_time_mins ) == 1
                %%        this_chan = arr_chan ;
                %%        this_iphase = arr_iphase ;
                %%    else
                %%        this_chan = arr_chan(a) ;
                %%        this_iphase = arr_iphase(a) ;
                %%    end

                %%    if( strcmp( mylabel, this_chan ) )
                %%        plot([arr_time_mins(a) arr_time_mins(a)],yy,'LineWidth', 1, 'Color', [ .6 0 0 ]) ;
                %%        text( [arr_time_mins(a)], yy(2)-dy,this_iphase,...
                %%            'HorizontalAlignment','left',...
                %%            'VerticalAlignment','top',...
                %%            'BackgroundColor', [ 1 0 0 ],...
                %%            'FontWeight', 'bold',...
                %%            'EdgeColor', [ .6 0 0 ] ) ;
                %%    end
                %%end


            end

            if( strcmp( ev_type, 'regional' ) )
                mytitle = { [ 'Three components recorded from a regional event detected by station TA ' sta ]  } ;
            else
                mytitle = { [ 'Three components recorded from a large event detected by station TA ' sta ]  } ;
            end

            axes('position',[ .05,.05,.9,.9 ] ) ; 
            htext = text( .5, 0.1, mytitle, 'FontSize',14 ) ; 
            set( htext, 'HorizontalAlignment','center' ) ; 
            set( gca, 'Visible','off' ) ;

            figname = [ sta '_' ev_type ] ;
            save_png( imgdir, sta, figname, ImageDPI ) ;

        catch exception

            disp(exception.identifier) ;
            disp(exception) ;
            fprintf( 'Cannot load trace object data, killing Matlab interpreter\n' ) ;

        end 

        %--- Open the wfdisc
        %db4 = dblookup_table( db0,'assoc' ) ;
        %db5 = dbsubset( db4, ['sta=="' sta '"'] ) ;
        %db6 = dbsubset( db5, ['time > "' time-120 '"'] ) ;
        %db7 = dbsubset( db6, ['time < "' time+120 '"'] ) ;
        %db8 = dbjoin( db7,'arrival' ) ;
        %flagrecords = dbquery( db3, 'dbRECORD_COUNT' ) ;



        %try
        %    [ arr_time, arr_chan, arr_iphase ] = dbgetv( arrivals, 'arrival.time', 'chan', 'iphase' ) ;
        %catch
        %    fprintf( 'Cannot get arrival time, arrival channel or arrival phase, killing Matlab interpreter\n' ) ;
        %    exit
        %end
        %%%%--- sprintf( '%0.5g', ( arr_time - oridtime ) ) 

        %%--- START: Get the first arrival
        %arrivals.record = 0 ;
        %try
        %    [ first_arr_time ] = dbgetv( arrivals, 'arrival.time' ) ;
        %catch
        %    fprintf( 'Cannot get arrival time, killing Matlab interpreter\n' ) ;
        %    exit
        %end

        %events(m).delay = ( first_arr_time - oridtime ) ;
        %%--- END: Get the first arrival

        %arr_time_mins = ( arr_time - oridtime ) / 60 ;

        %t0 = arr_time(1) - events(m).lead ;
        %t1 = t0 + events(m).mywindow ;

        %%--- Go back to using the original wfdisc
        %dbwf = dbsubset( dbwf, ['chan=~/' mychan '/'] ) ;
        %t0_ant = sprintf( '%17.5f', t0 ) ;
        %t1_ant = sprintf( '%17.5f', t1 ) ;
        %dbwf = dbsubset( dbwf, ['endtime > ' t0_ant ' && time < ' t1_ant ] ) ;

        %try
        %    tr = trload_css( dbwf, t0, t1 ) ;
        %catch
        %    fprintf( 'Cannot load trace object data, killing Matlab interpreter\n' ) ;
        %    exit
        %end 
        %trapply_calib( tr ) ;
        %trsplice( tr,0.5) ;
        %nrecs = dbquery( tr,'dbRECORD_COUNT' ) ;
        %for i=1:nrecs,

        %%--- END: Database operations to get what we want

        %%--- Set up bkgrd and frgrd colors
        %figure('Visible','off') ;
        %clf ;

        %% whitebg( [ 0 0 .63 ] ) ;
        %whitebg( [ 1 1 1 ] ) ;
        %% set( gcf, 'Color', [ 0, 0, 0 ] ) ;
        %set( gcf, 'Color', [ 1, 1, 1 ] ) ;
        %% set( gca, 'Color', 'y' ) ;
        %set( gca, 'Color', 'b' ) ;

        %set( gcf, 'PaperUnits', 'inches' ) ;
        %set( gcf, 'PaperOrientation', 'portrait' ) ;
        %set( gcf, 'PaperSize', [ 7 5 ] ) ;
        %set( gcf, 'PaperType', 'B2' ) ;

        %%--- Use to determine max and min for plots
        %for i=1:nrecs,
        %    tr.record = i-1;
        %    data_for_y = trextract_data(tr) ;
        %    data_for_y = data_for_y - ( sum( data_for_y ) / length( data_for_y ) ) ;
        %    max_y(i) = max( abs( data_for_y ) ) ;
        %end

        %my_max_y = max( abs( max_y ) ) ;
        %my_min_y = my_max_y * -1 ;

        %pl_min = [ 0.05 0.05 ] ;
        %pl_max = [ 0.98 0.98 ] ;
        %pl_gap = [ 0.01 0.01 ] ;

        %Xmin = pl_min(1) ;
        %Ymin = pl_min(2) ;
        %Xmax = pl_max(1) ;
        %Ymax = pl_max(2) ;
        %Xgap = pl_gap(1) ;
        %Ygap = pl_gap(2) ;

        %Xsize = ( Xmax - Xmin ) ;
        %Ysize = ( Ymax - Ymin ) ;

        %Xbox = Xsize - Xgap ;
        %Ybox = Xsize - Ygap ;

        %%--- Default to zero so we can do a test. Can't get exist() to work
        %new_height = 0 ;

    end



    %--- Open the wfdisc
    dbfree( db1 )
    dbfree( db2 )
    dbfree( db3 )
    dbclose( db0 )

end
