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

function dbObj = dbcentral( dbpath, cluster )

    % Init database list
    dbObj.databases = [] ;

    %--- START: Database operations to get what we want

    % fprintf( 'dbcentral_open: Init database object\n' ) ;

    db = dbopen( dbpath, 'r' ) ;

    dbcentral = dblookup_table( db,'clusters' ) ;

    count = dbquery( dbcentral, 'dbRECORD_COUNT' ) ;
    fprintf( 'dbcentral_open: Found [%0d] clusters in dbcentral\n', count ) ;


    %--- Look for our clustername
    fprintf( 'dbcentral_open: Subset for clustername == %s\n', cluster ) ;
    subset = dbsubset( dbcentral, [ sprintf('clustername == "%s" ', cluster) ] ) ;

    count = dbquery( subset, 'dbRECORD_COUNT' ) ;
    fprintf( 'dbcentral_open: Found [%0d] clusters for [%s] \n', count, cluster ) ;


    % Verify cluster exists
    if ne(count,1)
        error('dbcentral_open: No cluster [%s] in [%s]\n', cluster, dbpath) ;
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
        error('dbcentral_open: An unexpected error has occured') ;

    end


    if strcmp(dbObj.volumes, 'month')
        % Get start and end months/years
        startmonth = str2num(epoch2str( dbObj.time, '%L' ) ) ;
        startyear = str2num(epoch2str( dbObj.time, '%Y' ) ) ;
        endmonth = str2num(epoch2str( dbObj.endtime, '%L' ) ) ;
        endyear = str2num(epoch2str( dbObj.endtime, '%Y' ) ) ;


        for y = startyear:endyear

            for m = 1:12

                % Too early
                if startyear == y && m < startmonth
                    continue
                end

                % Too late
                if endyear == y && m > endmonth
                    continue
                end

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

                dbObj.databases = [ dbObj.databases ; month_path ] ;

            end

        end


    elseif strcmp(dbObj.volumes, 'year')

        % Get start and end years
        startyear = str2num(epoch2str( dbObj.time, '%Y' ) ) ;
        endyear = str2num(epoch2str( dbObj.endtime, '%Y' ) ) ;

        % Format strings for sprintf
        dbObj.dir = strrep(dbObj.dir, '%Y', '%0d') ;
        dbObj.dfile = strrep(dbObj.dfile, '%Y', '%0d') ;

        for y = startyear:endyear
            dbObj.databases = [ dbObj.databases ; abspath( concatpaths( sprintf(dbObj.dir, y) , sprintf(dbObj.dfile, y) ) ) ] ;
        end
    else

        dbObj.databases = [ abspath( concatpaths( dbObj.dir, dbObj.dfile ) ) ] ;

    end

    %dbObj.databases


end
