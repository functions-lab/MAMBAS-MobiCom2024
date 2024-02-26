function [energy] = GetEnergy(wave, symLen)
    waveLen = length(wave);
    symNum = floor(waveLen / symLen);

    energy = 0;
    for symIdx = 1: symNum
        startIdx = (symIdx-1) * symLen + 1;
        endIdx = symIdx * symLen;

        waveNow = wave(startIdx: endIdx);
        waveCal = waveNow - mean(waveNow);
        energy = energy + mean(abs(waveCal).^2)/symNum;
    end
end