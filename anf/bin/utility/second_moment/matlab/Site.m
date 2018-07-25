classdef Site

    properties
        site_table
        stations
    end

    methods
        function S = Site(db, select, reject)
            
            steps = 'dbopen site'
            
            if select
                steps = append(steps, fprintf('dbsubset sta=~/%s/', select))
            if reject
                steps = append(steps, fprintf('dbsubset sta!~/%s/', reject))
               
            steps = strjoin(steps, ';') 
            
            S.site_table = dbprocess(db, steps)
           
            S.stations = struct() 
            %S.site_table = dblookup_table(db, 'site') 
            %S.site_table = dbsubset(S.site_table,   
            
        end

        function  info = getEQ(EQ)
            % GET ORIGIN INFORMATION %

            string = strcat('orid=="', num2str(EQ.orid),'"');
            table = dbsubset(EQ.joinevent, string);

            if dbnrecs(table) > 1
                subset = dbsubset(table, 'netmag.auth!~/mt.SOCAL_MODEL/')
                [etime,elat,elon,edepth,mag,eauth,eorid,eevid]=dbgetv(subset, 'time', 'lat', 'lon', 'depth', 'magnitude', 'auth', 'orid', 'evid');
                epoch2str(etime, '%Y-%m-%d %H:%M:%S')
            else
                [etime,elat,elon,edepth,mag,eauth,eorid,eevid]=dbgetv(subset, 'time', 'lat', 'lon', 'depth', 'magnitude', 'auth', 'orid', 'evid');
            end

            % GET MOMENT TENSOR INFORMATION %
            subset = dbsubset(EQ.info, string);
            mt_join = dbjoin(subset, EQ.mt);
            
            if dbnrecs(mt_join) > 0
                [estatus,emag,estrike1,estrike2,edip1,edip2]=dbgetv(mt_join, 'estatus', 'drmag', 'str1', 'str2', 'dip1', 'dip2');
                if (estatus == 'Quality: 0') | (estatus == 'Quality: 1')
                    mt_flag = 1;
                    elog_notify('MT Quality < 2: Do not use fault dimensions')
                else
                    mt_flag = 0;
                    elog_notify('MT Quality >= 2: Use fault dimensions')
                end
            else
              mt_flag = 1;
              elog_notify('MT solution does not exist')
            end

            if mt_flag == 1;
                strike1 = 307; dip1 = 83;
                strike2 = 216; dip2 = 82; % from moment tensor solution
                mag = mag
            else
                strike1 = estrike1; strike2 = estrike2;
                dip1 = edip1; dip2 = edip2;
                mag = emag
            end

            info = struct('etime',etime, 'elat', elat, 'elon', elon, 'edepth', edepth, 'mag', mag, 'eauth', eauth, 'eorid', eorid, 'eevid', eevid, 'estatus',estatus, 'strike1', strike1, 'strike2', strike2, 'dip1', dip1, 'dip2', dip2);
            %EQ.info = struct('etime',etime, 'elat', elat, 'elon', elon, 'edepth', edepth, 'mag', mag, 'eauth', eauth, 'eorid', eorid, 'eevid', eevid);
        end

    
        function info = getEGF(EQ, loc_margin, dep_margin, time_margin)
            string = strcat('evid !=', num2str(EQ.MSinfo.eevid), ' && magnitude < ', num2str(EQ.MSinfo.mag), ' && lon > ', num2str(EQ.MSinfo.elon-loc_margin), ...
                    ' && lon < ', num2str(EQ.MSinfo.elon+loc_margin), ' && lat > ', num2str(EQ.MSinfo.elat-loc_margin), ...
                    ' && lat < ', num2str(EQ.MSinfo.elat+loc_margin), ' && depth > ', num2str(EQ.MSinfo.edepth-dep_margin), ...
                    ' && depth < ', num2str(EQ.MSinfo.edepth+dep_margin), ' && time < ', num2str(EQ.MSinfo.etime+time_margin));
            egf_subset = dbsubset(EQ.joinevent, string);

            if dbnrecs(egf_subset) > 0
                [aorids,aevids,aprefors]=dbgetv(egf_subset, 'time', 'orid','evid', 'prefor');
                evids = unique(aevids);
                egf_orids = [];
                for i = length(evids);
                    evid = evids(i);
                    ind = find(aevids == evid);
                    orids = aorids(ind);
                    prefor = unique(aprefors(ind));
        
                    if find(orids == prefor) > 0
                        egforids = [ egf_orids ; prefor ];
                    else
                        egforids = [ egf_orids; orids(1) ];
                    end
                end

            info  = struct('orids', egforids)
            else
              elog_die(fprintf('No aftershock in database for orid %s', EQ.MSinfo.eorid))
            end
        end

        % write function that grab egf info, time, orid, location
    end % methods

end % class
