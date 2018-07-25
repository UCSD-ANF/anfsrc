function [sigmatc,sigmaLc,sigmaWc,sigratio,sigv01,sigv02,sigmamV0]=geterrors(m2,varjack); 
% this version is setup for the 2-d fault plane
% This script does the variance calculations for thee characteristic rupture
% dimensions; It assumes m2 is the best estimate and it is ordered [tt, xt, yt, xx, xy, yy]
% varjack(1:6,1:6) is the covariance matrix from the jackknife calculation

       % for the variance of derived quantities;   the covariance matrix
       % of the derived function is just Jacobian*varjack*Jacobian'
       % MZJ 2001 equation 26 is a simplification of this for the
       % simple characteristic dimensions.
       % for the more complicated quantities, just do loop overi, loop over
       % j,  and sum up the partial_i * partial_j * Cij terms.
       
       % tau_c
       tauc=2*sqrt(m2(1));
       sigmatc=sqrt(varjack(1,1)/(m2(1)));
       %disp('Characteristic Duration')
       %disp([num2str(tauc,3),' plusminus ',num2str(sigmatc,3)])
       %keyboard     
       
       %L_c and W_c
        X=[m2(4), m2(5); m2(5), m2(6);];
        [U,S,V]=svd(X);
        L_c=2*sqrt(max(max(S)));
        W_c=2*sqrt(S(2,2));
        mhat=[m2(4), m2(5), m2(6)];
        rL=V(:,1); rW=V(:,2);
        zL=[rL(1)*rL(1),  2*rL(1)*rL(2), rL(2)*rL(2)];
        zW=[rW(1)*rW(1),  2*rW(1)*rW(2), rW(2)*rW(2)];
        sigsqL=0; sigsqW=0;
        for ii=1:3
         for jj=1:3
           sigsqL=sigsqL+zL(ii)*zL(jj)*varjack(3+ii,3+jj);
           sigsqW=sigsqW+zW(ii)*zW(jj)*varjack(3+ii,3+jj);
         end
        end
        % MZJ equation 26
        sigsqL=sigsqL/(zL*mhat'); sigsqW=sigsqW/(zW*mhat');
        sigmaLc=sqrt(sigsqL); sigmaWc=sqrt(sigsqW);
        %disp('Characteristic Length');
        %disp([num2str(L_c,3),' plusminus ',num2str(sqrt(sigsqL),3)]);
        %disp('Characteristic Width');
        %disp([num2str(W_c,3),' plusminus ',num2str(sqrt(sigsqW),3)]);
        
        %mV0 
        clear sigmasq sigma
        v0=m2(2:3)/m2(1);  %%%x_two(6:8)/x_two(5);
        mv0=sqrt(sum(v0.^2));
        L0=tauc*mv0;
        sigmasq=0;
        N=m2(2)^2+m2(3)^2;  D=m2(1)^2;
        for ii=1:3
         for jj=1:3
           if(ii==1)
             pari=(1/2)*(N/D)^(-1/2)*N*(-2)*m2(1)^(-3);
           elseif(ii==2|3)
             pari=(1/2)*(N/D)^(-1/2)*(2*m2(jj)/D);
           end
           if(jj==1)
             parj=(1/2)*(N/D)^(-1/2)*N*(-2)*m2(1)^(-3);
           elseif(jj==2|3)
             parj=(1/2)*(N/D)^(-1/2)*(2*m2(jj)/D);
           end          
          sigmasq=sigmasq+pari*parj*varjack(ii,jj);
          %[ii, jj, sigmasq]
         end
        end
        sigmamV0=sqrt(sigmasq);
        disp('mV0');
        %disp([num2str(mv0),' plusminus ', num2str(sigmamV0,3)]);
        
        % directivity ratio;   also MZJ 26 from old postall.m        
        ratio=L0/L_c;  %=mv0*tau_c *(1/2)*(zL*m2(4:6)^(-1/2);
        N=v0(1)^2+v0(2)^2;  %numerator?
        N2=(m2(2)^2/m2(1)) +(m2(2)^2/m2(1));
        D=zL*m2(4:6);
        sigmasq=0;
        
        for ii=1:6
         for jj=1:6
           pari=0; parj=0;
           %this is sigmai*sigmaj*partial/to_i*partial/to_j
           %sigi=sqrt(varjack(ii,ii));
           %sigj=sqrt(varjack(jj,jj));
           
           %xt contribution
           if(ii==2|3)
             pari=tauc*2*sqrt(D)*(1/2)*(m2(2)^2+m2(3)^2)^(-1/2)*2*m2(ii);
           end
           if(jj==2|3)
             parj=tauc*2*sqrt(D)*(1/2)*(m2(2)^2+m2(3)^2)^(-1/2)*2*m2(jj);
           end
           
           %tt contribution
           if(ii==1)
             pari=sqrt(m2(2)^2+m2(3)^2)*D^(-1/2)*(-1/2)*m2(1)^(-3/2);
           end
           if(jj==1)
             parj=sqrt(m2(2)^2+m2(3)^2)*D^(-1/2)*(-1/2)*m2(1)^(-3/2);
           end
           
           %three spatial contributions
           if(ii>=4) 
              pari=tauc*mv0*(-1/4)*D^(-3/2)*(zL(ii-3));
           end
           if(jj>=4)
             parj=tauc*mv0*(-1/4)*D^(-3/2)*(zL(jj-3));
           end
           %sigmasq=sigmasq+sigi*sigj*pari*parj;
           sigmasq=sigmasq+pari*parj*varjack(ii,jj);
           %disp([num2str(ii),' ',num2str(jj),' ',num2str(sigmasq,3),' ',num2str(pari),' ',num2str(parj)])
         end
        end
        sigratio=sqrt(sigmasq);
        %disp(['Directivity Ratio=',num2str(ratio,3),' plusminus',num2str(sigratio,3)]);
           
        
     
       % mv0 components
       sigsqV01=0; sigsqV02=0;
       for ii=1:3
        for jj=1:3
           %sigi=sqrt(varjack(ii,ii));
           %sigj=sqrt(varjack(jj,jj));
          if(ii==1)
            pari01=m2(2)*(-1)*m2(1)^2;
            pari02=m2(3)*(-1)*m2(1)^2;
          elseif(ii==2)
            pari01=(1/m2(1));
            pari02=0; 
          elseif(ii==3)
            pari01=0;
            pari02=(1/m2(1));
          end
          if(jj==1)
            parj01=m2(2)*(-1)*m2(1)^2;
            parj02=m2(3)*(-1)*m2(1)^2;
          elseif(jj==2)
            parj01=(1/m2(1));
            parj02=0;
          elseif(jj==3)
            parj01=0;
            parj02=(1/m2(1));
          end            
          sigsqV01=sigsqV01+pari01*parj01*varjack(ii,jj);
          sigsqV02=sigsqV02+pari02*parj02*varjack(ii,jj);
        end
       end
       sigv01=sqrt(sigsqV01); sigv02=sqrt(sigsqV02);
       %disp(['V0=',num2str([m2(2)/m2(1), m2(3)/m2(1)]),' plusminus',num2str([sigv01, sigv02])]);

      