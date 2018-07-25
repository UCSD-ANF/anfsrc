classdef logging
    methods (Static)
        function verbose(message)
            global mode_run
            if mode_run.verbose
                timestamp = string(datetime('now', 'Format', 'yyyy-MM-dd HH:mm:ss.SSS'));
                message = char(strcat(timestamp, ' second_moment[NOTIFY]: ', message));
                elog_notify(message)
            end
        end
        
        function debug(message)
            global mode_run
            if mode_run.debug
                timestamp = string(datetime('now', 'Format', 'yyyy-MM-dd HH:mm:ss.SSS'));
                message = char(strcat(timestamp, ' second_moment[NOTIFY]: ', message));
                elog_notify(message)
            end
        end
       
        function info(message)
            timestamp = string(datetime('now', 'Format', 'yyyy-MM-dd HH:mm:ss.SSS'));
            message = char(strcat(timestamp, ' second_moment[INFO]: ', message));
            elog_notify(message)
        end
 
        function die(message)
            timestamp = string(datetime('now', 'Format', 'yyyy-MM-dd HH:mm:ss.SSS'));
            message = char(strcat(timestamp, ' second_moment[KILL]: ', message));
            elog_notify(message)
            exit()    
        end
        
        function warning(message)
            timestamp = string(datetime('now', 'Format', 'yyyy-MM-dd HH:mm:ss.SSS'));
            message = char(strcat(timestamp, ' second_moment[WARNING]: ', message));
            elog_complain(message)    
        end
    end
end

