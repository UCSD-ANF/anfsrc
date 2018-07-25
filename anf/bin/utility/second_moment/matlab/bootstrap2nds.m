function [mv0u,mv0l,bound2u,bound2l,Lcu,Lcl,taucu,taucl,minvrsv,minvru,minvrl]=bootstrap2nds(A,b,conf,NB);
% A is the partial derivative matrix
% b is the data vector
% conf is the confidence level to determine lower and upper bound at
% NB is the number of boostrap samples to run
% function to find 95% confidence bounds for mv0 and mv01 given datavector d and
% associated Greens functions matrix G
c1=(1-conf)/2;
c2=1-c1;
N=length(b);
zz=ceil(N*rand(NB,N));
mv0sv=zeros(NB,1); Lcsv=zeros(NB,1); taucsv=zeros(NB,1); Wcsv=zeros(NB,1);
bound2sv=zeros(NB,1);  minvrsv=zeros(NB,1);

for i=1:NB
  inds=zz(i,:);
  Gi=A(inds,:);
  di=b(inds)';
  %whos Gi di;
  %keyboard

  m2=seconds_2d_v2(Gi,di);
  m2=m2(1:6); di=di';
  X=[m2(4), m2(5); m2(5), m2(6);];
  %ssqr=sum((Gi*m2-di').^2)
  [U,S,V]=svd(X);
  Lcsv(i)=2*sqrt(max(max(S)));
  Wcsv(i)=2*sqrt(S(2,2));
  v0=m2(2:3)/m2(1);
  mv0sv(i)=sqrt(sum(v0.^2));
  taucsv(i)=2*sqrt(m2(1));
  bound2sv(i)=(1/2)*(Lcsv(i)/taucsv(i));
  minvrsv(i)=max([bound2sv(i),mv0sv(i)]);
  %L0=taucsv(i)*mv0;
  %dir=L0/L_c;
  %ssqr3=sum((Gi*m2-di').^2)/sum((d2'-mean(d2)').^2);

end;
mv0sv=sort(mv0sv); Lcsv=sort(Lcsv); taucsv=sort(taucsv); Wcsv=sort(Wcsv);
bound2sv=sort(bound2sv); minvrsv=sort(minvrsv);

%indu=round(.975*B); indl=round(.025*B);   %95%
indu=round(c2*NB); indl=round(c1*NB);   
mv0u=mv0sv(indu); mv0l=mv0sv(indl);
Lcl=Lcsv(indl); Lcu=Lcsv(indu);
taucl=taucsv(indl); taucu=taucsv(indu);
bound2l=bound2sv(indl); bound2u=bound2sv(indu);
minvrl=minvrsv(indl); minvru=minvrsv(indu);

%figure
%subplot(1,2,1)
%hist(Lcsv,50);
%xlabel('L_c (km)','FontSize',12);
%set(gca,'FontSize',12)
%ylabel('#');
%subplot(1,2,2)
%hist(taucsv,50)
%xlabel('\tau_c (s)','FontSize',12)
%ylabel('#');
%set(gca,'FontSize',12);

end
