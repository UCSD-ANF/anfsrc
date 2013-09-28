function sensor_comparison_v2(dbpath, prefor, station, tb, strong_chan, weak_chan, flipit, filter_band, fignum);

db = dbopen(dbpath,'r');

dborigin = dblookup_table(db,'origin');
dborigin = dbsubset(dborigin,sprintf('orid == %d',prefor));
otime = double(dbgetv(dborigin,'time'));

ts = otime - tb(1);
te = otime + tb(2);

dbwf = dblookup_table(db,'wfdisc');
    
for i=1:3
    figure(i);
    if i==1
        comp = 'Z';
        dbwf_s = dbsubset(dbwf,sprintf('sta =~ /%s/ && chan =~ /%s%s/ && time < _%f_ && endtime > _%f_',station,strong_chan(1:2),'Z',te,ts));
        dbwf_w = dbsubset(dbwf,sprintf('sta =~ /%s/ && chan =~ /%s%s/ && time < _%f_ && endtime > _%f_',station,weak_chan(1:2),'Z',te,ts));
        dbwf_s.record = 0;
        dbwf_w.record = 0;
    elseif i==2
        comp = 'N';
        dbwf_s = dbsubset(dbwf,sprintf('sta =~ /%s/ && chan =~ /%s%s/ && time < _%f_ && endtime > _%f_',station,strong_chan(1:2),'N',te,ts));
        dbwf_w = dbsubset(dbwf,sprintf('sta =~ /%s/ && chan =~ /%s%s/ && time < _%f_ && endtime > _%f_',station,weak_chan(1:2),'N',te,ts));
        dbwf_s.record = 0;
        dbwf_w.record = 0;
    elseif i==3
        comp = 'E';
        dbwf_s = dbsubset(dbwf,sprintf('sta =~ /%s/ && chan =~ /%s%s/ && time < _%f_ && endtime > _%f_',station,strong_chan(1:2),'N',te,ts));
        dbwf_w = dbsubset(dbwf,sprintf('sta =~ /%s/ && chan =~ /%s%s/ && time < _%f_ && endtime > _%f_',station,weak_chan(1:2),'N',te,ts));
        dbwf_s.record = 0;
        dbwf_w.record = 0;
    end
    
    tr_s = dbinvalid();
    tr_s = trload_css(dbwf_s,ts,te);
    tr_s.record = 0;
    trapply_calib(tr_s);
    data_s = trextract_data(tr_s);
    [nsamp_s,samprate_s,calib_s] = dbgetv(tr_s,'nsamp','samprate','calib');
    data_s = data_s - mean(data_s);
    
    tr_w = dbinvalid();
    tr_w = trload_css(dbwf_w,ts,te);
    tr_w.record = 0;
    trapply_calib(tr_w);
    trfilter(tr_w,'DIF');
    data_w = trextract_data(tr_w);
    [nsamp_w,samprate_w,calib_w] = dbgetv(tr_w,'nsamp','samprate','calib');
    data_w = data_w - mean(data_w);
    
    
    if samprate_s > samprate_w
        data_s = resample(data_s,samprate_w,samprate_s);
        samprate_s = samprate_w;
        nsamp_s = length(data_s);
    elseif samprate_w > samprate_s
        data_w = resample(data_w,samprate_s,samprate_w);
        samprate_w = samprate_s;
        nsamp_w = length(data_w);
    end
    
    subplot(3,1,1);
    plot(data_s,'b-');
    ylabel(sprintf('%s%s',strong_chan(1:2),comp));
    
    subplot(3,1,2);
    plot(data_w,'b-');
    ylabel(sprintf('%s%s',weak_chan(1:2),comp));
    
    subplot(3,1,3);
    plot(data_s,'b-'); hold on;
    plot(data_w,'r-.'); hold off;
    ylabel(sprintf('Combined - %s component',comp));
end
legend(sprintf('%s%s',strong_chan(1:2),comp),sprintf('%s%s',weak_chan(1:2),comp));
    
    
    
    

