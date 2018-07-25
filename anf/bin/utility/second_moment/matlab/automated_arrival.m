function [tt1b tt2b] = automated_arrival(xi, nbins, samples, phase, dtype, data, tt1b, tt2b, sb, sa, dt, np)
% AUTOMATED_ARRIVALS Detect arrival within given waveform and update arrival and window times accordingly
% Inputs:
%   xi:      damping parameter of waveform, PhasePicker parameter (see PhasePicker.m)
%   nbins:   number of bins, PhasePicker parameter
%   samples: number of samples to add on to beginning of waveform for detecting arrivals
%   phase:   arrival phase, accepts P or S as input
%   data:    waveform data
%   tt1b:    window start time
%   tt2b:    window end time
%   sb:      number samples before arrival
%   sa:      number of samples after arrival
%   dt:      waveform frequency (sample rate inverse)
% Outputs:
%   tt1b:    updated window start time
%   tt2b:    updated window end time

    type = 'na';
    pflag = 'N';
    Tn = 0.01;
    o = 'to_peak';

    if strcmp(dtype, 'MS')
        try 
            [locs, snr_dbs] = arrayfun(@(x) PhasePicker(data((tt1b-samples):tt2b), dt, type, pflag, Tn, xi, x, o), nbins);
        catch
            logging.warning('Cannot run picker, try different PhasePicker parameters')
        end 
        [max_snr, ind] = max(snr_dbs);
        loc = locs(ind);
        if loc >= 0
            logging.info('Detected arrival: Will update arrival time')
            ts = tt1b + loc/dt - samples;
            tt2b = ts + sa;
            tt1b = ts - sb;
        else
            logging.info('Failed to detect arrival: Will not update arrival time')
            return
        end
    else
        try 
            [locs, snr_dbs] = arrayfun(@(x) PhasePicker(data((tt1b-sb-samples):tt2b), dt, type, pflag, Tn, xi, x, o), nbins);
        catch
            logging.warning('Cannot run picker: Try different PhasePicker parameters')
        end 
        [max_snr, ind] = max(snr_dbs);
        loc = locs(ind);
         
        if loc >= 0
            logging.info('Detected arrival: Will update arrival time')
            tt1b = tt1b + loc/dt - sb - samples;
            tt2b = tt1b + np - 1;
        else
            logging.info('Failed to detect arrival: Will not update arrival time')
            return
        end
    end 
end            

% type = 'na';
% pflag = 'Y';
% Tn = 0.01;
% o = 'to_peak';
% if strcmp(phasem(i), 'P')
%     xi = 0.5;
%     bins = [25 50 100 2/dtsv(i)];

%     try
%         [locs, snr_dbs] = arrayfun(@(x) PhasePicker(velMS_rot(tt1b:tt2b), dtsv(i), type, pflag, Tn, xi, x, o), bins);
%     catch
%         'Cannot run picker, try different parameters'
%     end

%     [max_snr, ind] = max(snr_dbs)
%     loc = locs(ind);
%     % if new arrival was selected update arrival and waveform window 
%     if loc >= 0
%         t = tt1b + loc/dtsv(i);
%         tt2b = tt1b + loc/dtsv(i) + samps_after;
%         tt1b = tt1b + loc/dtsv(i) - samps_before;
%     end
% end

