function plot_waveforms(tr, esaz);
figure('position', [0, 0, 1200, 1200])

nrecs = dbnrecs(tr);
for n=1:nrecs
    tr.record = n-1;
    data = trextract_data(tr);
    [chan, sta] = dbgetv(tr, 'chan', 'sta');

    subplot(2,3,n);
    plot(1:length(data), data);
    title(chan, 'FontSize', 16);
end
suptitle(sprintf('%s, esaz: %s', sta, num2str(esaz)))
k = waitforbuttonpress;
close all
end
