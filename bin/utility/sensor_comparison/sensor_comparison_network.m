function sensor_comparison_network( dbpath, prefor, station, time_bounds, channel_raw, channel_scaled, flip_polarity, filter_band, fignum )
global index fignumG;
index = 1;
fignumG = fignum;
% --------------------------------------------------------------------------------------------------
% script to plot comparison of data from colocated sensors at a site.  Configured to allow operator
% to choose order of sensors. Data from the second sensor is recast into coordinate system of first
% sensor.
%
%  arguments:
%
%	event - structure passed from irisFetch.Events containing earthquake information
%       station - station
%	time_bounds - 2 element array containg number of seconds before and after origin time to start segment
%	channel_raw - channel group for data to be compared to, for example LH-00
%	channel_scaled - channel group for data to be re-scaled and rotated to channel_raw, for example LH-10
%	flip_polarity - valued at either +1.0 (no change) or -1.0 (change polarity)
%	filter_band - 2 element array containg low- and high- pass filter values in Hz
%
% --------------------------------------------------------------------------------------------------
dbmaster_path = '/anf/TA/dbs/dbmaster';

db = dbopen(dbpath,'r');
db_event = dblookup_table(db,'event');
db_event = dbjoin(db_event,dblookup_table(db,'origin'));
db_event = dbsubset(db_event,sprintf('orid == %d',prefor));
db_event = dbjoin(db_event,dblookup_table(db,'netmag'));
db_event.record = 0;

if nargin < 8
disp(nargin)
    error('myApp:argChk', 'Number of inputs invalid for function sensor_comparison. Exiting');
end


% massage input for uniformity:

sta = upper(station);
chan_target = sprintf('%s?', channel_raw(1:2));
chan_simul  = sprintf('%s?', channel_scaled(1:2));

otime = dbgetv(db_event,'time');

t1 = otime - time_bounds(1);
t2 = otime + time_bounds(2);

dbwf_target = dbsort(dbsubset(dblookup_table(db,'wfdisc'),sprintf('sta =~ /%s/ && chan =~ /%s./ && endtime > _%f_ && time < _%f_',station,channel_raw(1:2),t1,t2)),'chan');
dbwf_simul = dbsort(dbsubset(dblookup_table(db,'wfdisc'),sprintf('sta =~ /%s/ && chan =~ /%s./ && endtime > _%f_ && time < _%f_',station,channel_scaled(1:2),t1,t2)),'chan');

% ---------------------------------------------------------------------------------------------
% data components rotated into coordinate system of target sensor
% ---------------------------------------------------------------------------------------------

figure(fignum)
subplot(1,1,1);

for n=1:3

	subplot(3,1,n);

    if n == 1
        dbwf_target_chan = dbsubset(dbwf_target,'chan =~ /..Z/'); 
    elseif n == 2
        dbwf_target_chan = dbsubset(dbwf_target,'chan =~ /..N/');
    elseif n == 3
        dbwf_target_chan = dbsubset(dbwf_target,'chan =~ /..E/');
    end
    
    dbwf_target_chan.record = 0;
    
    target_trace = dbinvalid();
    target_trace = trload_css(dbwf_target_chan,t1,t2);
    target_trace.record = 0;
    target_data = trextract_data(target_trace);
    [target_nsamp,target_samprate,target_time,target_endtime,target_chan] = dbgetv(target_trace,'nsamp','samprate','time','endtime','chan');
    db_tmp = dbsubset(dbjoin(dblookup_table(db,'sensor'),dblookup_table(db,'sitechan')),sprintf('sta =~ /%s/ && chan =~ /%s/ && time <= _%f_ && endtime >= _%f_',station,target_chan,t1,t2));
    db_tmp.record = 0;
    [target_vang,target_hang] = dbgetv(db_tmp,'vang','hang');
    
% first produce rotated data plot:
    dbwf_simul.record=0;
    simul_trace = dbinvalid();
    simul_trace = trload_css(dbwf_simul,t1,t2);
    simul_trace.record = 0;
    simul_data = trextract_data(simul_trace);
    
	scaled_data = zeros( size(simul_data) );
    scaled_data = scaled_data(1:end-mod(length(scaled_data),2));
    
	for k=1:3
        
        if k == 1
            dbwf_simul_chan = dbsubset(dbwf_simul,'chan =~ /..Z/');
            flag = true;
        elseif k == 2
            dbwf_simul_chan = dbsubset(dbwf_simul,'chan =~ /..N/');
            flag = false;
        elseif k == 3
            dbwf_simul_chan = dbsubset(dbwf_simul,'chan =~ /..E/');
            flag = false;
        end
        
        dbwf_simul_chan.record = 0;
        
        simul_trace = trload_css(dbwf_simul_chan,t1,t2);
        simul_trace.record = 0;
        simul_data = double(trextract_data(simul_trace));

        [simul_nsamp,simul_samprate,simul_time,simul_endtime,simul_chan] = dbgetv(simul_trace,'nsamp','samprate','time','endtime','chan');
        db_tmp = dbsubset(dbjoin(dblookup_table(db,'sensor'),dblookup_table(db,'sitechan')),sprintf('sta =~ /%s/ && chan =~ /%s/ && time <= _%f_ && endtime >= _%f_',station,simul_chan,t1,t2));
        db_tmp.record = 0;
        [simul_vang,simul_hang] = dbgetv(db_tmp,'vang','hang');
        simul_data = simulate_target_response( target_trace, simul_trace, dbpath, dbmaster_path );
        fnyquist = simul_samprate / 2;
		simul_data = ii_filter( simul_data, filter_band(1), filter_band(2), fnyquist );
        ang1 = simul_vang - target_vang;
        ang2 = simul_hang - target_hang;
		geometric_factor = flip_polarity * cos( ang1 * pi / 180 ) * cos( ang2 * pi / 180 );
        
		scaled_data = scaled_data + geometric_factor * simul_data;
    end
    
	ild = length(scaled_data);
	scaled_data = scaled_data - mean(scaled_data);
	ik1 = (  floor(ild * 0.1):floor(ild * 0.9) );
	times = linspace(simul_time,simul_endtime,simul_nsamp);
	h1=plot( times(ik1), scaled_data(ik1), 'b-'); hold on;
	datetick;

% now target plot:

	d = target_data;
	fnyquist = target_samprate / 2;
	d = ii_filter( d, filter_band(1), filter_band(2), fnyquist );
	d = d - mean(d);
    
	ild = length(d);
	ik2 = (  floor(ild * 0.1):floor(ild * 0.9) );
    
	times = linspace(target_time,target_endtime,target_nsamp);
	h2=plot( times(ik2), d(ik2)*max(scaled_data)/max(d), 'r-.'); hold off;
    %h2=plot( times(ik2), d(ik2), 'r-.'); hold off;
	datetick;
	hy = ylabel( [ target_chan, ' (Counts)' ] ); set(hy, 'FontSize', 14 );


    %if sampling frequency is the same, compute the scale:
    if target_samprate == simul_samprate
        [p, s] = polyfit( scaled_data(ik1), d(ik2), 1);
        v = axis; xpos = v(1) + ( v(2)-v(1) ) * 0.7; ypos = v(3) + ( v(4)-v(3) ) * 0.7;
        str = sprintf('sc=%.3f', p(1)); htt=text(xpos, ypos, str); set(htt, 'FontSize', 12);
    end

end % n

% --------------------------------------------------------------------------------------------------
% add a title:
% --------------------------------------------------------------------------------------------------

otime = epoch2str(dbgetv(db_event,'time'),'%D %H:%M:%S');
subplot(3,1,1);
str = sprintf('ROTATED DATA: NETWORK-%s     %s M=%.1f', sta, otime, dbgetv(db_event,'magnitude') );
ht = title(str); set(ht, 'FontSize', 16 );

% --------------------------------------------------------------------------------------------------
% print out
% --------------------------------------------------------------------------------------------------
subplot(3,1,1); hold off;
subplot(3,1,2); hold off;
subplot(3,1,3); hold off;
legend( [h1 h2], channel_scaled, channel_raw, 'Location', 'Southeast');

%sot = strrep( otime, ':', '' ); sot = strrep(sot, '-', ''); sot = strrep(sot, ' ','_');
%orient tall;
%cmd = sprintf( 'print -dpng  PLOTS/%s_%s.png', sta, sot(1:13) ); eval(cmd);

%-------------------------------------------------------------------------------------------
%
% bandpass data from flowpass to fhighpass and remove quadratic terms:
%
%-------------------------------------------------------------------------------------------

function [data_out] = ii_filter( data, flowpass, fhighpass, fnyquist );

band = [flowpass fhighpass] / fnyquist;
[b, a] = butter( 3, band );

d = detrend(data);
d = filter( b, a, d);
x = 1:length(d);
[p,s,mu] = polyfit(x',d, 2);
data_out = d - polyval(p, x', s, mu);

%--------------------------------------------------------------------------
%Build model of instrument response using eval_resp method
%--------------------------------------------------------------------------
function [response] = build_instrument_response_model(response_file_path,fnyq,nsamp);

resp_ptr = dbresponse(response_file_path);
df = 2*fnyq/nsamp;
freq = linspace(0,fnyq,nsamp/2+1);
w = 2*pi*freq;

for i=1:length(w)
    response(i) = eval_response(resp_ptr,w(i));
end

response = response';

%-------------------------------------------------------------------------------------------
% function to convert time series input to have raw response of target
%-------------------------------------------------------------------------------------------

function outdata = simulate_target_response( target_trace, simul_trace, dbpath, dbmaster_path );
global index fignumG;

[nsamp, samprate] = dbgetv(simul_trace,'nsamp','samprate');
indata = trextract_data(simul_trace);
nsamp = nsamp - mod(nsamp,2);
indata = indata(1:end-mod(nsamp,2));
fnyq = samprate/2;

db=dbopen(dbpath,'r');

[simul_sta,simul_chan,simul_time,simul_endtime] = dbgetv(simul_trace,'sta','chan','time','endtime');

%--------------------------------------------------------------------------
%Look up path to appropriate response file, and build instrument response
%model for input instrument
%--------------------------------------------------------------------------
db_ins = dblookup_table(db,'sitechan');
db_ins = dbsubset(db_ins,sprintf('sta =~ /%s/ && chan =~ /%s/',simul_sta,simul_chan));
db_ins = dbjoin(db_ins,dblookup_table(db,'sensor'));
db_ins = dbsubset(db_ins,sprintf('time <= _%f_ && endtime >= _%f_',simul_time,simul_endtime));
db_ins = dbjoin(db_ins,dblookup_table(db,'instrument'));
db_ins.record = 0;

input_resp = build_instrument_response_model(sprintf('%s/%s/%s',dbmaster_path,dbgetv(db_ins,'dir'),dbgetv(db_ins,'dfile')),fnyq,nsamp);

%--------------------------------------------------------------------------
%Get appropriate calib and calratio values for input instrument
%--------------------------------------------------------------------------
dbwf = dblookup_table(db,'wfdisc');
dbwf = dbsubset(dbwf,sprintf('sta =~ /%s/ && chan =~ /%s/ && time <= _%f_ && endtime >= _%f_',simul_sta,simul_chan,simul_time,simul_endtime));
dbwf = dbjoin(dbwf,dblookup_table(db,'sensor'));
dbwf.record = 0;
[calib,calratio] = dbgetv(dbwf,'calib','calratio');

indata = indata*calib*calratio;
INDATA = fft(indata);

outdata = ones(size(INDATA));
outdata(2:nsamp/2) = INDATA(2:nsamp/2) ./ input_resp(2:nsamp/2);
outdata(nsamp:-1:nsamp/2+2) = conj(outdata(2:nsamp/2));
outdata(nsamp/2+1) = 0;
outdata(1) = 0;
ind = find( isnan(outdata) );
outdata(ind) = 0;

%--------------------------------------------------------------------------
%Transform back to time-domain, differentiate to get units of acceleration
%then transform back to frequency-domain and continue.
%This makes the assumption that the target trace is an accelerometer
%channel and that the input trace is a seismometer channel.
%--------------------------------------------------------------------------
outdata = ifft(outdata);
% if index <= 3
%     figure(index + 10);
%     plot(outdata); hold on ;
% end
outdata = diff(outdata);
% if index <= 3
%     plot(outdata,'r-.'); hold off;
%     figure(fignumG);
%     index = index +1;
% end
plot(outdata);
outdata = fft(outdata);

%--------------------------------------------------------------------------
%Look up path to appropriate response file, and build instrument response
%model for target instrument
%--------------------------------------------------------------------------
[target_sta,target_chan,target_time,target_endtime] = dbgetv(target_trace,'sta','chan','time','endtime');
db_ins = dblookup_table(db,'sitechan');
db_ins = dbsubset(db_ins,sprintf('sta =~ /%s/ && chan =~ /%s/',target_sta,target_chan));
db_ins = dbjoin(db_ins,dblookup_table(db,'sensor'));
db_ins = dbsubset(db_ins,sprintf('time <= _%f_ && endtime >= _%f_',target_time,target_endtime));
db_ins = dbjoin(db_ins,dblookup_table(db,'instrument'));
db_ins.record = 0;

target_resp = build_instrument_response_model(sprintf('/anf/TA/dbs/dbmaster/%s/%s',dbgetv(db_ins,'dir'),dbgetv(db_ins,'dfile')),fnyq,nsamp);

%--------------------------------------------------------------------------
%Get appropriate calib and calratio values for target instrument
%--------------------------------------------------------------------------
dbwf = dblookup_table(db,'wfdisc');
dbwf = dbsubset(dbwf,sprintf('sta =~ /%s/ && chan =~ /%s/ && time <= _%f_ && endtime >= _%f_',target_sta,target_chan,target_time,target_endtime));
dbwf = dbjoin(dbwf,dblookup_table(db,'sensor'));
dbwf.record = 0;
[calib,calratio] = dbgetv(dbwf,'calib','calratio');

outdata = outdata*calib*calratio;

outdata(2:nsamp/2) = outdata(2:nsamp/2) .* target_resp(2:nsamp/2);
outdata(nsamp:-1:nsamp/2+2) = conj(outdata(2:nsamp/2));
outdata(nsamp/2+1) = 0;
outdata(1) = 0;
ind = find(isnan(outdata));
outdata(ind) = 0;

outdata = ifft(outdata);
outdata = outdata/(calib*calratio);
