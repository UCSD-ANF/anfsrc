function [compm dtsv npEGF npMS slat slon stasm phasem velEGF velMS velEGF_rot velMS_rot timems timeegf duration] ...
        = data_setup(db, orid, MS, select, reject, filter, tw);
% DATASETUP For each possible egf, set up the waveforms, origin, stations, arrivals.
% Inputs:
%   db:           pointer to main database
%   orid:         orid for main-shock event
%   select:       regex expression of stations to use
%   reject:       if not None, regex expression of stations to reject
%   filter:       butterworth bandpass filter for waveforms
%   tw:           time window in seconds for windowing waveforms around arrivals
% Outputs:
%   compm:        cell array of component names 
%   dtsv:         variable of individual component sample rates in seconds
%   npEGF:        number of points in each EGF waveform
%   npMS:         number of points in each Mainshock waveform
%   slat:         station latitudes
%   slon:         station longitudes
%   stasm:        cell array of station names
%   phasem:       cell array of phases
%   velEGF:       array of velocity seismograms for EGF
%   velMS:        array of velocity seismograms for Mainshock
%   timems:       array of mainshock arrival times
%   timeegf:      array of egf arrival times
%   duration:     array of predicted P-S times

% Initiate EGF Origin instance to retrieve egf origin info.
global mode_run

if mode_run.verbose
    logging.verbose(sprintf('Getting origin information for orid %s', orid))
end

EGF = Origin(db, orid, 'EGF', '');
EGF = get_stations(EGF, select, reject);
EGF = get_arrivals(EGF, select, reject);
% Find station/phase arrivals on both MS and EGF data.
% For each MS arrival, match to the corresponding EGF arrival.
match = cellfun(@(x, y) find(strcmp({MS.arrivals.sta}, x) == 1 & strcmp({MS.arrivals.iphase}, y) == 1) ...
        , {EGF.arrivals.sta}, {EGF.arrivals.iphase}, 'UniformOutput', false);
% Using match, get EGF indices.
egfinds = find(cellfun(@(x) isempty(x), match) == 0);
% Using match get MS indices.
msinds = cell2mat(match(cellfun(@(x) ~isempty(x), match)));

% Initiate variables to be returned.
stasm = {};  phasem = {}; compm = {};
timems = []; timeegf = []; duration = [];

% For each station with ms & egf arrivals, do:
s = 0;
ns = length(msinds);
for i=1:ns
    % Set up variable inputs for EGF Data instance.
    id = egfinds(i);
    sta = EGF.arrivals(id).sta;
    esaz = EGF.arrivals(id).esaz;
    chan = EGF.arrivals(id).chan;
    chan_code = strcat(chan(1:2), '.');
    egftime = EGF.arrivals(id).time;
    time = egftime - 8.0; 
    % Check that EGF station and times match truth. 
    %sta
    %epoch2str(time, '%Y-%m-%d %H:%M:%S')
   
    % Get trace table and apply_calib, integrate, filter, and rotate traces.
    EGF_wf = Data(db, sta, chan_code, time, tw, filter, esaz);
   
    % Set up variable inputs for MS Data instance.
    id = msinds(i);
    sta = MS.arrivals(id).sta;
    esaz = MS.arrivals(id).esaz;
    phase = MS.arrivals(id).iphase;
    chan = MS.arrivals(id).chan;
    chan_code = strcat(chan(1:2), '.');
    mstime = MS.arrivals(id).time;

    if MS.arrivals(id).pstime
        pstime = MS.arrivals(id).pstime;
    elseif phase=='P'
        m = find(strcmp({MS.stations.sta}, sta) == 1);
        pstime = MS.stations(m).pstime;
    else
        pstime = 0;
    end

    time = mstime - 8.0;
    % Check that MS station and times match truth. 
    %sta
    %epoch2str(mstime, '%Y-%m-%d %H:%M:%S')
    
    % Get trace table and apply_calib, integrate, filter, and rotate traces
    MS_wf = Data(db, sta, chan_code, time, tw, filter, esaz);
    % Extract waveform data from tr.
    if ~isempty(MS_wf.tr) & ~isempty(EGF_wf.tr)
        % Get data for channel and store.
        MS_wf = grab_data(MS_wf, chan, 'ms');
        EGF_wf = grab_data(EGF_wf, chan, 'egf');
    
        % If data exists, store arrivals, station, phase, comp, etc. 
        if ~isempty(MS_wf.data) & ~isempty(EGF_wf.data)
            s = s + 1;
            
            stasm{s} = sta;
            sid = find(strcmp({MS.stations.sta}, sta) == 1); 
            slat(s) = MS.stations(sid).lat;
            slon(s) = MS.stations(sid).lon;

            phasem{s} = phase;
            compm{s} = chan;
            timems(s) = mstime;
            timeegf(s) = egftime;
            duration(s) = pstime;

            dtsv(s) = 1./MS_wf.samprate;

            % Store waveform data.
            npMS(s) = length(MS_wf.data);
            velMS(s,1:npMS(s)) = MS_wf.data;
            velMS_rot(s,1:npMS(s)) = MS_wf.rot_data;
 
            npEGF(s)=length(EGF_wf.data);
            velEGF(s,1:npEGF(s)) = EGF_wf.data;
            velEGF_rot(s, 1:npEGF(s)) = EGF_wf.rot_data;
        end % if
    end % if
end % for loop

% if no waveform data, kill second_moment
if ~exist('dtsv')
    logging.die('No waveforms were found for all possible stations')
end

end % function

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
