function [wave] = File2Wave(fileName)
    fileID = fopen(fileName, 'r');
    waveBoth = fread(fileID, 'float');
    fclose(fileID);

    waveReal = waveBoth(1: 2: end);
    waveImag = waveBoth(2: 2: end);
    wave = waveReal + 1i * waveImag;
    wave = wave.';
end