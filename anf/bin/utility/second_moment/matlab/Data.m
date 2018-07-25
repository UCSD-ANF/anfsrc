classdef Data
    properties
        time
        sta
        chan_code
        samprate
        ncalib
        segtype
        tr
        chan
        data
        rot_data
    end %properties

    methods
        function WF = Data(db, sta, chan_code, time, tw, filter, esaz)
            % set starttime and endtime
            global mode_run
            WF.time = time;
            starttime = WF.time;
            endtime = starttime + tw;
            
            WF.sta = sta;
            WF.chan_code = chan_code;
            %
            % GET WFDISC TABLE
            %
            steps = {};
            
            % open wfdisc
            steps{1} = 'dbopen wfdisc';

            % subset for station, chan_codenel, and time
            steps{2} = sprintf('dbsubset sta=~/%s/ && endtime > %s && time < %s && chan =~/%s/', ...
                                sta, starttime, endtime, chan_code); 
             % join to sensor, instrument
            steps{3} = 'dbjoin sensor';
            steps{4} = 'dbjoin instrument';
            steps{5} = 'dbsort sta chan';

            % set table view
            dbview = dbprocess(db, steps);
            % if no records return from function
            if dbnrecs(dbview) == 0
                logging.warning(sprintf('No traces after subset for sta=~/%s/ && chan=~/%s/', sta, chan_code))
                return
            end

            % if 3 records 
            if dbnrecs(dbview) == 3
                % get wfdisc info for later
                [samprate, ncalib,segtype] = dbgetv(dbview, 'wfdisc.samprate', ...
                                'instrument.ncalib', 'instrument.rsptype');
                
                % only use one value for each, should be same for all 3 records
                WF.samprate = samprate(1); WF.ncalib = ncalib(1); WF.segtype = segtype(1); 

                %
                % LOAD DATA
                %
            
                % if data is not readable, return from function
                try
                    warning('off')
                    tr = trload_css(dbview, starttime, endtime);
                    %trsplice(tr)
                catch
                    logging.warning(sprintf('Could not read data for %s:%s', sta, chan_code))
                    return
                end
                % if no data, return from function
                if dbnrecs(tr) == 0
                    logging.warning(sprintf('No data after trload for %s:%s', sta, chan_code))
                    return
                end

                % if more than 3 records, return from function
                if dbnrecs(tr) > 3
                    logging.warning(sprintf('Too many traces after trload_cssgrp for %s:%s', sta, chan_code))
                    return
                end
                
                %          %
                % FIX DATA %
                %          %   

                % apply calibration
                % demean traces
                trapply_calib(tr);
                trfilter(tr, 'DEMEAN');

                % apply integration
                if strcmp(segtype, 'A')
                    trfilter(tr, 'INT');
                    segtype = 'V';

                elseif strcmp(segtype, 'D')
                    trfilter(tr, 'DIF');
                    segtype = 'V';

                elseif strcmp(segtype, 'V')
                    segtype = 'V';

                else
                    logging.warning(sprintf('Unknown data type for %s:%s', sta, chan_code))
                    return
                end
                
                %  rotation -- discuss with Juan first???
                try
                    warning('off')
                    lastwarn('')
                    trrotate(tr, esaz, 0, {'T','R','Z'});
                    [warnMsg, warnId] = lastwarn;
                    if ~isempty(warnMsg)
                        logging.warning(sprintf('Problems rotating %s:%s', sta, chan_code))
                        lastwarn('')
                        return
                    end
                catch
                    logging.warning(sprintf('Problems rotating %s:%s', sta, chan_code))
                    return
                end
 
                % filter
                try
                    trfilter(tr, filter);
                catch
                    logging.warning(sprintf('Problems with filter %s for %s:%s', filter, sta, chan_code))
                    return
                end

                % test rotation code
                %if mode_run.debug_plot
                %    plot_waveforms(tr, esaz)
                %end

                WF.tr = tr; 
            end
        end % function

        function WF = grab_data(WF, chan, type)
            % subset tr for specific channel
            %% add in rotated data to see if picker works on S arrivals


            tr = dbsubset(WF.tr, sprintf('chan =~/%s/', chan));
            if strcmp(chan(3), 'Z')
                tr_rot = dbsubset(WF.tr, sprintf('chan=~/%s/', 'Z'));
            else
                tr_rot = dbsubset(WF.tr, sprintf('chan=~/%s/', 'T'));
            end
 
            if dbnrecs(tr) == 1
                tr.record = 0;
                data = trextract_data(tr);

                data = detrend(data);
                
                if strcmp(type, 'ms')
                    tp=taper(length(data),.01);
                else
                    tp=taper(length(data),.05);
                end
                
                data=data.*tp;
%                data = data.*tp;
                WF.data = data;
            
            elseif dbnrecs(tr) > 1
                logging.warning(sprintf('More than 1 trace for %s:%s', WF.sta, chan))
                return
            elseif dbnrecs(tr) == 0
                logging.warning(sprintf('No traces for %s:%s', WF.sta, chan))
                return
            end
 
            if dbnrecs(tr_rot) == 1
                tr_rot.record = 0;
                data = trextract_data(tr_rot);

                data = detrend(data);
                
                if strcmp(type, 'ms')
                    tp=taper(length(data),.01);
                else
                    tp=taper(length(data),.05);
                end
                
                data=data.*tp;
%                data = data.*tp;
                WF.rot_data = data;

                % for longer mseed files, the tw will be changed
                % time: arrival - 8 seconds
                % original data before changes will be start: time - tw, end: time + 2*tw
                % there will be 2 extra time windows so filter and taper do not affect true window 
                % data = data[tw:2*tw]
                
            elseif dbnrecs(tr_rot) > 1
                logging.warning(sprintf('More than 1 trace for %s:%s', WF.sta, chan))
                return
            elseif dbnrecs(tr_rot) == 0
                logging.warning(sprintf('No traces for %s:%s', WF.sta, chan))
                return
            end
        end % function 
            
    end % methods
end %class
