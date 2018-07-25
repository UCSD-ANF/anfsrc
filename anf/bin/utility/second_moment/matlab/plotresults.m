if mode_run.debug_plot
    figure('pos', [10 10 900 500]);
end

angle = atan2(max_evc(2), max_evc(1));
if angle < 0
    angle = angle + 2*pi;
end

theta_grid = linspace(0, 2*pi);
ellipse_x_r = L_c*cos(theta_grid)*1000;
ellipse_y_r = W_c*sin(theta_grid)*1000;

ellipse_x_az = Cart2AZ(ellipse_x_r);
ellipse_y_az = Cart2AZ(ellipse_y_r);

R = [cos(angle) sin(-angle); sin(angle) cos(angle)];
r_ellipse = [ellipse_x_r;ellipse_y_r]' * R;

timestring = sprintf('Time: %s', epoch2str(MS.eqinfo.etime, '%Y-%m-%d %H:%M:%S'));
datestring = sprintf('Location: (%.2f, %.2f, %.2f)', lone, late, depe);
magstring = sprintf('Magnitude: %.1f', mage);
faultstring = sprintf('Strike/Dip: %.0f/%.0f', strike, dip);
text1 = [timestring newline datestring newline magstring newline faultstring]; 

if DOJACKKNIFE
    variancestring = sprintf('Variance Reduction: %4.4f', ssqr);
    taucstring = sprintf('   Duration: %4.2f+-%3.3f (s)', tauc, sigmatc);
    lengthstring = sprintf('   Length: %4.2f+-%3.2f (km)', L_c, sigmaLc);
    widthstring = sprintf('   Width: %4.2f+-%3.2f (km)', W_c, sigmaWc);
    velocitystring = sprintf('   Velocity: %4.2f+-%3.2f (km/s)', mv0, sigmamV0);
    directivitystring = sprintf('Directivity Ratio: %4.2f+-%3.2f', ratio, sigratio);
else
    variancestring = sprintf('Variance Reduction: %4.4f', ssqr);
    taucstring = sprintf('   Duration: %4.2f (s)', tauc);
    lengthstring = sprintf('   Length: %4.2f (km)', L_c);
    widthstring = sprintf('   Width: Width: %4.2f (km)', W_c);
    velocitystring = sprintf('   Velocity: %4.2f (km/s)', mv0);
    directivitystring = sprintf('Directivity Ratio: %4.2f', ratio);
end    

text2 = [variancestring newline newline 'Rupture' newline lengthstring newline widthstring newline taucstring newline velocitystring newline newline directivitystring];

text_result = [text1 newline newline text2];

subplot(2, 2, 1)
text(0, 0.4, text_result, 'FontSize', 18); axis off
title('Event Information', 'FontSize', 18)

subplot(2,2,2)
plot(r_ellipse(:,1), r_ellipse(:,2), '-')
xlabel('Distance along Strike (m)', 'FontSize', 14)
ylabel('Z (m)', 'FontSize', 14)
title('Rupture Ellipse', 'FontSize', 18)

%daspect([1 1 1])
hold on
%quiver is not plotting properly, look up
quiver(0, 0, m2(2), m2(3), L0*1000, 'LineWidth', 1.5, 'MaxHeadSize', 10)
hold off 

subplot(2,2,3)
minc = min(2*sqrt(t2(IJ))); maxc = max(2*sqrt(t2(IJ)));
hh=scatter(slon(IJ),slat(IJ),100,2*sqrt(t2(IJ)),'filled'); hold on;
plot(slon(IJ),slat(IJ),'ko','MarkerSize',10);
colormap(jet); colorbar; caxis([minc maxc])
plot(lone,late,'w^','MarkerSize',15,'MarkerFaceColor','r');
axis([-117.0 -115.9 33.0 34.1])
xlabel('Longitude','FontSize',14);
ylabel('Latitude','FontSize',14);
set(gca,'FontSize',14);
title('Measurements \tau_c(s) in seconds ','FontSize',18);

subplot(2,2,4)
hh=scatter(slon(IJ),slat(IJ),100,2*sqrt(G*m2),'filled'); hold on;
plot(slon(IJ),slat(IJ),'ko','MarkerSize',10);
colormap(jet); colorbar; caxis([minc maxc])
plot(lone,late,'w^','MarkerSize',15,'MarkerFaceColor','r');
axis([-117.0 -115.9 33.0 34.1])
xlabel('Longitude','FontSize',14);
ylabel('Latitude','FontSize',14);
title('2nd Moments Fit, \tau_c(s) in seconds','FontSize',18);
set(gca,'FontSize',14);

if mode_run.debug_plot
    k = waitforbuttonpress;
else
    set(gcf, 'visible', 'off')
    set(gcf, 'pos', [10 10 800 800])
end

if ~mode_run.no_figure
    saveas(gcf, sprintf('%s/MS%d_EGF%d_result.png', image_dir, msorid, orid))
end

close
