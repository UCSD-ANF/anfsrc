%
% Helper function to DBCENTRAL module
% Based on a submitted time return the
% respective database
% reyes@ucsd.edu
%


function database = dbcentral_time( dbObj, query_time )

    % Test if time is too early
    if query_time < dbObj.time
        error( 'dbcentral_time: %d smaller than time. \n', qeury_time ) ;
    end

    % Test if time is too late
    if query_time > dbObj.endtime
        error( 'dbcentral_time: %d larger than endtime. \n', qeury_time ) ;
    end


    if strcmp(dbObj.volumes, 'month')

        y = str2num(epoch2str( query_time, '%Y' ) ) ;
        m = str2num(epoch2str( query_time, '%L' ) ) ;

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

        database = abspath( concatpaths( dir, dfile) ) ;

    elseif strcmp(dbObj.volumes, 'year')

        y = str2num(epoch2str( query_time, '%Y' ) ) ;

        % Format strings for sprintf
        dbObj.dir = strrep(dbObj.dir, '%Y', '%0d') ;
        dbObj.dfile = strrep(dbObj.dfile, '%Y', '%0d') ;

        database = abspath( concatpaths( sprintf(dbObj.dir, y) , sprintf(dbObj.dfile, y) ) ) ;

    else

        database = abspath( concatpaths( dbObj.dir, dbObj.dfile ) ) ;

end
