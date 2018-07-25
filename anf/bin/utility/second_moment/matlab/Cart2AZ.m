function cart0 = Cart2AZ(cart)
    % Convert from cartesian to azimuth
    cart0 = reorient(cart);
    
    ndx1 = cart >= 0. & cart < pi/2;
    cart0(ndx1) = pi/2 - cart(ndx1);   
    ndx2 = cart >= pi/2 & cart < pi;
    cart0(ndx2) = 3*pi/2 - cart(ndx2);
    ndx3 = cart >= pi & cart < 2*pi;
    cart0(ndx3) = 2*pi - cart(ndx3) + pi/2;
end

function arg = reorient(arg)
    ndx = arg < 0.0;
    arg(ndx) = arg(ndx) + 2*pi;
end

