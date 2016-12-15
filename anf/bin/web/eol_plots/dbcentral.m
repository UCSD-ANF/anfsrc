%
%
% Functions to help Matlab scripts
% work easily with dbcentral
% databases.
%
%   Usage:
%       dbcentralObj = dbcentral( '/anf/shared/dbcentral/dbcentral', 'anza_rt' )
%
%       dbcentral_open: Init database object
%       dbcentral_open: Found [26] clusters in dbcentral
%       dbcentral_open: Subset for clustername == anza_rt
%       dbcentral_open: Found [1] clusters for [anza_rt]

%       dbcentralObj =
%
%             databases: '/anf/ANZA/rt/anza/anza'
%           clustername: 'anza_rt'
%               volumes: 'single'
%                  time: 1.2623e+09
%               endtime: 7.3662e+05
%                   dir: '/anf/ANZA/rt/anza'
%                 dfile: 'anza'
%
%
%
% Juan Reyes <reyes@ucsd.edu>
%

function dbObj = dbcentral( dbpath, cluster, statime, staendtime )

    % Init database list
    dbObj.databases = {} ;

    try
        [statime, status] = str2num(statime) ;
    catch
        fprintf( 'dbcentral: error converting statime' );
    end

    if ~exist('status') || ~status
        fprintf( 'dbcentral: statime non-numeric' );
        statime = 0
    end

    try
        [staendtime, status] = str2num(staendtime) ;
    catch
        fprintf( 'dbcentral: error converting staendtime' );
    end
    if ~exist('status') || ~status
        fprintf( 'dbcentral: staendtime non-numeric' );
        staendtime = round((now-datenum([1970 01 01 00 00 00]))*86400)
    end

    cluster = strsplit(cluster,',')


    %--- START: Database operations to get what we want

    for c=cluster

        c = char( c ) ;

        db = dbopen( dbpath, 'r' ) ;

        dbcentral = dblookup_table( db,'clusters' ) ;

        count = dbquery( dbcentral, 'dbRECORD_COUNT' ) ;
        fprintf( 'dbcentral_open: Found [%0d] clusters in dbcentral\n', count ) ;


        %--- Look for our clustername
        fprintf( 'dbcentral_open: Subset for clustername == %s\n', c ) ;
        subset = dbsubset( dbcentral, [ sprintf('clustername == "%s" ', c) ] ) ;

        count = dbquery( subset, 'dbRECORD_COUNT' ) ;
        fprintf( 'dbcentral_open: Found [%0d] clusters for [%s] \n', count, c ) ;


        % Verify cluster exists
        if ne(count,1)
            error('dbcentral_open: No cluster [%s] in [%s]\n', c, dbpath) ;
        end


        % Extract values from row
        try
            [dbObj.clustername, dbObj.volumes] = dbgetv(subset, 'clustername', 'volumes' ) ;
            [dbObj.time, dbObj.endtime] = dbgetv(subset, 'time', 'endtime' ) ;
            [dbObj.dir, dbObj.dfile] = dbgetv(subset, 'dir', 'dfile' ) ;


            if dbObj.endtime > round((now-datenum([1970 01 01 00 00 00]))*86400)
                dbObj.endtime = round((now-datenum([1970 01 01 00 00 00]))*86400) ;
                fprintf( 'dbcentral_open: NULL endtime. Set to now: [%d] \n', dbObj.endtime ) ;
            end

        catch exception

            disp(exception.identifier) ;
            fprintf('dbcentral_open: An unexpected error has occured') ;
            exit( 1 ) ;

        end


        if strcmp(dbObj.volumes, 'month')
            % Get start and end months/years
            startmonth = str2num(epoch2str( dbObj.time, '%L' ) ) ;
            startyear = str2num(epoch2str( dbObj.time, '%Y' ) ) ;
            endmonth = str2num(epoch2str( dbObj.endtime, '%L' ) ) ;
            endyear = str2num(epoch2str( dbObj.endtime, '%Y' ) ) ;
            fprintf('dbcentral: startmonth %d \n', startmonth ) ;
            fprintf('dbcentral: startyear %d \n', startyear ) ;
	    fprintf('dbcentral: endmonth %d \n', endmonth ) ;
	    fprintf('dbcentral: endyear %d \n', endyear ) ;

            % Convert station start and endtimes
            statimemonth = str2num(epoch2str( statime, '%L' ) ) ;
            statimeyear = str2num(epoch2str( statime, '%Y' ) ) ;
            staendtimemonth = str2num(epoch2str( staendtime, '%L' ) ) ;
            staendtimeyear = str2num(epoch2str( staendtime, '%Y' ) ) ;

            fprintf('dbcentral: statimemonth %d \n', statimemonth ) ;
            fprintf('dbcentral: statimeyear %d \n', statimeyear ) ;
            fprintf('dbcentral: staendtimemonth %d \n', staendtimemonth ) ;
            fprintf('dbcentral: staendtimeyear %d \n', staendtimeyear ) ;

            for y = startyear:endyear

                for m = 1:12

		    fprintf('dbcentral: Verify %d_%d \n', m, y ) ;

                    % Too early
                    if startyear == y && m < startmonth
                        fprintf('dbcentral: time too early %d_%d \n', m, y ) ;
                        continue
                    end

                    % Too late
                    if endyear == y && m > endmonth
                        fprintf('dbcentral: time too late %d_%d \n', m, y ) ;
                        continue
                    end

                    % Verify if station is active
                    if y < statimeyear || staendtimeyear < y
                        fprintf('dbcentral: sta year early/later %d_%d \n', m, y ) ;
                        continue
                    end
                    if statimeyear == y && m < statimemonth
                        fprintf('dbcentral: sta month early %d_%d \n', m, y ) ;
                        continue
                    end
                    if staendtimeyear == y && m > staendtimemonth
                        fprintf('dbcentral: sta month later %d_%d \n', m, y ) ;
                        continue
                    end

                    fprintf('dbcentral: valid %d_%d \n', m, y ) ;

                    dir = strrep(dbObj.dir, '%m', '%02d') ;
                    dfile = strrep(dbObj.dfile, '%m', '%02d') ;

                    dir = strrep(dir, '%Y', 'YEAR') ;
                    dfile= strrep(dfile, '%Y', 'YEAR') ;

                    dir = sprintf(dir, m) ;
                    dfile= sprintf(dfile, m) ;

                    dir = strrep(dir, 'YEAR', '%04d') ;
                    dfile= strrep(dfile, 'YEAR', '%04d') ;

                    dir = sprintf(dir, y) ;
                    dfile= sprintf(dfile, y) ;

                    month_path = abspath( concatpaths( dir, dfile) ) ;

                    dbObj.databases = [ dbObj.databases  month_path ] ;

                end

            end


        elseif strcmp(dbObj.volumes, 'year')

            % Get start and end years
            startyear = str2num(epoch2str( dbObj.time, '%Y' ) ) ;
            endyear = str2num(epoch2str( dbObj.endtime, '%Y' ) ) ;

            % Format strings for sprintf
            dbObj.dir = strrep(dbObj.dir, '%Y', '%0d') ;
            dbObj.dfile = strrep(dbObj.dfile, '%Y', '%0d') ;

            % Convert station start and endtimes
            statimeyear = str2num(epoch2str( statime, '%Y' ) ) ;
            staendtimeyear = str2num(epoch2str( staendtime, '%Y' ) ) ;
            fprintf('dbcentral: statimeyear %d \n', statimeyear ) ;
            fprintf('dbcentral: staendtimeyear %d \n', staendtimeyear ) ;

            for y = startyear:endyear

                % Verify if station is active
                if y < statimeyear || staendtimeyear < y
                    %fprintf('dbcentral: Too early/later %s \n', y ) ;
                    continue
                end

                fprintf('dbcentral: valid %d \n', y ) ;

                dbObj.databases = [ dbObj.databases abspath( concatpaths( sprintf(dbObj.dir, y) , sprintf(dbObj.dfile, y) ) ) ] ;
            end
        else

            dbObj.databases = [ dbObj.databases abspath( concatpaths( dbObj.dir, dbObj.dfile ) ) ] ;

        end
    end

    dbObj.databases


end
