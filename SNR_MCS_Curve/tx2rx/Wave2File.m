function [] = Wave2File(fileName, wave)
    waveReal = real(wave);
    waveImag = imag(wave);
    waveBoth = zeros(1, length(wave)*2);
    waveBoth(1: 2: end) = waveReal;
    waveBoth(2: 2: end) = waveImag;

    fileID = fopen(fileName, 'w');
    fwrite(fileID, waveBoth, 'float');
    fclose(fileID);
end