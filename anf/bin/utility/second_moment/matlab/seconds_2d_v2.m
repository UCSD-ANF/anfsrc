function	[xopt]=seconds_2d_v2(A,b);
% To do the 2nd moments inverse problem using the robust control toolbox
% INPUTS
% Ax=b   linear system where x contains the second, moments in the order
% x=[tt,xt,yt,xx,xy,yy];
%
% OUTPUTS
% xopt is the decision variable, e.g. x with a dummy variable appended to
% it, see MZJ 2001.
%
% For details of how this works see the Robust Control Toolbox's webpages
% we use two key functions from it as well as its formalism for defining a
% linear matrix inequality problems.  The functions are:
% feasp  which finds and initial feasable point
% mincx  which minimizes the objective function subject to the constraints
%
% VERSION 2 Added a constraint that tau_c must be less than max of b  

%Define Problem
setlmis([]);
% decision variable x=[tt,xt,yt,xx,xy,yy];
% Could do this as a series of LMIs or as one big block diagonal
type=3; %lets you define the matrix in terms of the index of the decision variable
struct(1,1)=1;  % t-t
struct(1,2)=2;  % t-x
struct(1,3)=3;  % t-y
struct(2,1)=2;  % t-x
struct(2,2)=4;  % x-x
struct(2,3)=5;  % x-y
struct(3,1)=3;  % t-y
struct(3,2)=5;  % x-y
struct(3,3)=6;  % y-y
[Xposvolume,NDEC,XDEC]=lmivar(type,struct);
% next call lmiterm to define inequality
% this is the n=1 LMI, and I think X is RHS
% it's block 1, 1  (i.e. entries 2 and 3)
% outer factor and right coeficient are 1 so we get just
% Xposvolume>0
lmiterm([-1 1 1 Xposvolume], 1, 1);


% This part uses the SCHUR COMPLEMENT approach to specify
% the least-squares objective function
% a dummy variable for the objective function is appended to the decision vector
c=zeros(7,1); c(7)=1; dim=length(b);
type=3; clear struct;
struct(1,1)=7;
[Xdum,NDEC,XDEC]=lmivar(type,struct);
% define XLS as the 6 model parameters that are supposed to fit the data
type=3; clear struct;
struct(1:6)=[1:6];
struct=struct';
[XLS,NDEC,XDEC]=lmivar(type,struct);
%
%Now add the various factors, etc define 2 blocks
lmiterm([-2 1 1 Xdum], 1, 1);
lmiterm([-2 2 1 XLS],A,1);
lmiterm([-2 2 1 0],-1*b);
%skip the block below the diagonal
lmiterm([-2 2 2 0],1); %PUT IN IDENTITY like in example in lmiterm man page

%
% now make tauc lie in range of data
%
scale=A(1,1); maxtauc=1.0*max(b);
clear struct
type=3; %lets you define the matrix in terms of the index of the decision variable
struct(1,1)=1;  % t-t
[Xtauc,NDEC,XDEC]=lmivar(type,struct);
% next call lmiterm to define inequality
% this is the n=3 LMI, and I think X is RHS
% it's block 1, 1  (i.e. entries 2 and 3)
% outer factor and right coeficient are 1 so we get just
% maxtauc>Xtauc
lmiterm([3 1 1 Xtauc], 1, 1);
lmiterm([-3 1 1 0],maxtauc)

%get the description of the whole LMI system
lmisys=getlmis;

%find feasable point
disp('Finding Feasable Point')
[tmin,xfeas]=feasp(lmisys);

disp('Doing Objective Minimization')
%minimize objective
[copt,xopt]=mincx(lmisys,c,[.01,40,-100,10,0],xfeas);




   
   
   
   

