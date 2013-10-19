function [ERROR_LOG] = sensor_comparison(dbpath, network, prefor, station, tb, strong_chan, weak_chan);

global ERROR_LOG;

db = dbopen(dbpath,'r');

OUTPUT_DB = dbopen(sprintf('/anf/%s/work/white/xcal/%s/%s_entire',network,datestr(now,'yyyymmdd'),network),'r+');
OUTPUT_DB = dblookup_table(OUTPUT_DB,'xcal');

OUTPUT_FIGURE_DIR = sprintf('/anf/%s/work/white/xcal/%s/figures',network,datestr(now,'yyyymmdd'));
OUTPUT_FIGURE_TYPE = 'epsc';

PLOT = true;
FILTER_PARAMS = [1 3 10 3]; %[lco_freq lco_order uco_freq uco_order] Butterworth

dborigin = dblookup_table(db,'origin');
dborigin = dbsubset(dborigin,sprintf('orid == %s',prefor));
otime = double(dbgetv(dborigin,'time'));
time_stamp = epoch2str(otime,'%Y%m%d%H%M%S');

ts = otime - tb(1);
te = otime + tb(2);

for i=1:3
    
    if i==1
       comp = 'Z';
    elseif i==2
        comp = 'N';
    elseif i==3
        comp = 'E';
    end
    wchan = sprintf('%s%s',weak_chan(1:2),comp);
    schan = sprintf('%s%s',strong_chan(1:2),comp);

    try
        trace_s = read_data(station,schan,ts,te,db);
        trace_w = read_data(station,wchan,ts,te,db);
    catch err
        disp(sprintf('\t\t\tSkipping %s-%s comparison for %s...', schan,wchan,station));
        disp(' ');
        fprintf(ERROR_LOG,'%s-%s comparison skipped for %s\n',schan,wchan,station);
        fprintf(ERROR_LOG,'orid - %d\n',prefor);
        fprintf(ERROR_LOG,'origin time - %s\n',epoch2str(otime,'%D %H:%M:%S.%s'));
        fprintf(ERROR_LOG,'database - %s\n',dbquery(db,'dbDATABASE_NAME'));
        fprintf(ERROR_LOG,'ERROR - %s\n\n',err.message);
        continue;
    end

    [data_s,data_w,data_s_unfil,data_w_unfil] = process_data(trace_s,trace_w,FILTER_PARAMS);
    [r,lags] = xcorr(data_s,data_w,'coeff');
    r = r*rms(data_w)/rms(data_s);
    lags = lags/dbgetv(trace_w,'samprate');
    lag = lags(find(r == max(r)));
    
    if PLOT
        ts_serial = datenum(epoch2str(ts,'%Y-%m-%d %H:%M%:%S.%s'),'yyyy-mm-dd HH:MM:SS.FFF');
        te_serial = datenum(epoch2str(te,'%Y-%m-%d %H:%M%:%S.%s'),'yyyy-mm-dd HH:MM:SS.FFF');
        
        fig = figure(i);
        subplot(4,1,1);
        times = linspace(ts_serial,te_serial,length(data_s_unfil));
        plot(times,data_s_unfil,'b-'); datetick;
        hy = ylabel(sprintf('%s - raw',schan)); set(hy,'FontSize',13);
        hx = xlabel('Time (HH:MM:SS)'); set(hx,'FontSize',16);

        subplot(4,1,2);
        times = linspace(ts_serial,te_serial,length(data_w_unfil));
        plot(times,data_w_unfil,'b-'); datetick;
        hy = ylabel(sprintf('%s - raw',wchan)); set(hy, 'FontSize',13);
        hx = xlabel('Time (HH:MM:SS)'); set(hx, 'FontSize',16);
        
        subplot(4,1,3);
        times = linspace(ts_serial,te_serial,length(data_s));
        plot(times,data_s,'b-'); hold on;
        plot(times,data_w,'r-.'); hold off; datetick;
        hy = ylabel(sprintf('Processed',schan,wchan)); set(hy, 'FontSize',13);
        hx = xlabel('Time (HH:MM:SS)'); set(hx, 'FontSize',16);
        hl = legend(schan,wchan); set(hl, 'FontSize',13);
        
        subplot(4,1,4);
        plot(lags,r);
        hy = ylabel('Cross-Correlation'); set(hy, 'FontSize',13);
        hx = xlabel('Lag (seconds)'); set(hx, 'FontSize',16);
        ht = text(0.9*max(lags),0.75*max(r),sprintf('%.4f',max(r)));  set(ht, 'FontSize',16);
        
        subplot(4,1,1);
        ht = title(sprintf('%s - %s %s/%s %s',network,station,schan,wchan,epoch2str(otime,'%D %H:%M:%S'))); set(ht, 'FontSize', 20 );
        
        filename = sprintf('%s_%s_%s',station,comp,time_stamp);
        saveas(fig,sprintf('%s/%s',OUTPUT_FIGURE_DIR,filename),OUTPUT_FIGURE_TYPE);
        
        dbaddv(OUTPUT_DB,'time',otime,'sta',station,'wchan',wchan,'schan',schan,'xcor',max(r),'lag',lag,'filter',sprintf('BW %.2f %d %.2f %d',FILTER_PARAMS(1),FILTER_PARAMS(2),FILTER_PARAMS(3),FILTER_PARAMS(4)),'dir',OUTPUT_FIGURE_DIR,'dfile',sprintf('%s.%s',filename,OUTPUT_FIGURE_TYPE));
    else
        dbaddv(OUTPUT_DB,'time',otime,'sta',station,'wchan',wchan,'schan',schan,'xcor',max(r),'lag',lag,'filter',sprintf('BW %.2f %d %.2f %d',FILTER_PARAMS(1),FILTER_PARAMS(2),FILTER_PARAMS(3),FILTER_PARAMS(4)));
    end
    if exist('trace_s')
        trdestroy(trace_s);
    end
    if exist('trace_w')
        trdestroy(trace_w);
    end
end

dbfree(dborigin);
dbclose(OUTPUT_DB);
dbclose(db);

%--------------------------------------------------------------------------

function [trace] = read_data(sta,chan,ts,te,db);

dbwf = dblookup_table(db,'wfdisc');

try
    i = dbfind(dbwf,sprintf('sta =~ /%s/ && chan =~ /%s/ && time <= _%f_ && endtime >= _%f_',sta,chan,ts,te));
    if i ~= -102
        dbwf = dblist2subset(dbwf,i);
    else
        i=0;
        recs = [];
        while i ~= -102
            i = dbfind(dbwf,sprintf('sta =~ /%s/ && chan =~ /%s/ && time <= _%f_ && endtime >= _%f_',sta,chan,te,ts),i);

            if i ~= -102
                recs(length(recs)+1) = i;
             elseif length(recs) == 0
                 error('No records found in wfdisc');
            end
        end
        dbwf = dblist2subset(dbwf,recs);
    end

    dbwf.record = 0;
    trace = trload_css(dbwf,ts,te);
    dbfree(dbwf);
    
catch err
    disp(sprintf('\t\t\tWARNING - Failed to read %s data for station %s locally. Attempting to retrieve data from IRIS DMC...',chan,sta));
    trace = read_data_DMC(sta,chan,ts,te,db);
end

trace.record = 0;

%get proper calib value and apply
dbcalib = dblookup_table(db,'calibration');
dbcalib = dbsort(dbsubset(dbcalib,sprintf('sta =~ /%s/ && chan =~ /%s/ && time <= _%f_',sta,chan,ts)),'time');
dbcalib.record = dbnrecs(dbcalib) - 1;

[calib,samprate] = dbgetv(dbcalib,'calib','samprate');
dbputv(trace,'calib',calib);

trapply_calib(trace);

dbfree(dbcalib);

%--------------------------------------------------------------------------


function [trace] = read_data_DMC(sta,chan,ts,te,db);

try
    db_tmp = dbsubset(dblookup_table(db,'snetsta'),sprintf('sta =~ /%s/',sta));
    db_tmp.record = 0;
    if dbquery(db_tmp,'dbRECORD_COUNT') < 1
        error('dbsubset failed in read_data_DMC()');
    end
    network = dbgetv(db_tmp,'snet');
    dbfree(db_tmp);
    
    tr = irisFetch.Traces(network,sta,'--',chan,epoch2str(ts,'%D %H:%M:%S.%s'),epoch2str(te,'%D %H:%M:%S.%s'));
    
    if length(tr.data) == 0
        error('NULL data retrieved from IRIS DMC');
    end
    
    trace = trnew();
    trace = dblookup_table(trace,'trace');
    trace.record = dbaddnull(trace);
    trinsert_data(trace,tr.data);
    dbputv(trace,'nsamp',tr.sampleCount,'samprate',tr.sampleRate,'time',ts,'endtime',te,'sta',sta,'chan',chan);

catch err
    disp(sprintf('\t\t\tERROR - Failed to read data from IRIS DMC.'));
    error(sprintf('%s - thrown by read_data_DMC()',err.message));
end

disp(sprintf('\t\t\tSuccessfully retrieved data from IRIS DMC.'));

%--------------------------------------------------------------------------

function [data_s,data_w,data_s_unfil,data_w_unfil] = process_data(trace_s,trace_w,FILTER_PARAMS);

data_s_unfil = trextract_data(trace_s);

trfilter(trace_s,sprintf('DEMEAN; BW %f %d %f %d',FILTER_PARAMS(1),FILTER_PARAMS(2),FILTER_PARAMS(3),FILTER_PARAMS(4)));
data_s = trextract_data(trace_s);
samprate_s = dbgetv(trace_s,'samprate');

trfilter(trace_w,'DEMEAN');
data_w_unfil = trextract_data(trace_w);

trfilter(trace_w,sprintf('DIF; BW %f %d %f %d',FILTER_PARAMS(1),FILTER_PARAMS(2),FILTER_PARAMS(3),FILTER_PARAMS(4)));
data_w = trextract_data(trace_w);
samprate_w = dbgetv(trace_w,'samprate');

if samprate_s > samprate_w
    data_s = resample(data_s,samprate_w,samprate_s);
    samprate_s = samprate_w;
elseif samprate_w > samprate_s
    data_w = resample(data_w,samprate_s,samprate_w);
    data_w_unfil = resample(data_w_unfil,samprate_s,samprate_w);
    samprate_w = samprate_s;
end

%HACK
if length(data_s) > length(data_w)
    data_s = data_s(mod(length(data_s),length(data_w))+1:end);
elseif length(data_w) > length(data_s)
    data_w = data_w(mod(length(data_w),length(data_s))+1:end);
end