function z = normalize(vector, id)
    z = (vector(id) - min(vector))/(max(vector)-min(vector));
end
