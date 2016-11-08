%-----------------------------------------------------
%  Evaluate distance of event to station
%-----------------------------------------------------
%
% Determine if the event is regional or global
% reyes@ucsd.edu
%
%-----------------------------------------------------
%
function location = event_region( sta_lat, sta_lon, event_obj, range )

    [arclen,az] = distance(sta_lat,sta_lon,event_obj.Lat,event_obj.Lon) ;


    if arclen < range
        location = 'regional' ;
    else
        location = 'large' ;

    end

end
