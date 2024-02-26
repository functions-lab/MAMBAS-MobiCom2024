function [csiNew] = myChannelEstimate(csiOld, dmrsPos)
    [subNum, symNum] = size(csiOld);

    phaseDelta = zeros(subNum, length(dmrsPos)-1);
    for dmrsIdx = 2: length(dmrsPos)
        phaseDelta(:, dmrsIdx-1) = angle(csiOld(:, dmrsPos(dmrsIdx)) ./ csiOld(:, dmrsPos(1)));
    end
    phaseSlope = zeros(subNum, 1);
    for subIdx = 1: subNum
        p = polyfit(dmrsPos(2: end), phaseDelta(subIdx, :), 1);
        phaseSlope(subIdx) = p(1);
    end
    phaseBias = angle(csiOld(:, dmrsPos(1))) - phaseSlope * dmrsPos(1);
    csiPhase = zeros(length(phaseBias), symNum);
    for i = 1: symNum
        csiPhase(:, i) = phaseBias + i*phaseSlope;
    end
    csiAmp = mean(abs(csiOld(:, dmrsPos)), 2);
    
    csiNew = abs(csiAmp) .* exp(1i*csiPhase);
end