function [packetRx, snr, cfo] = Tx2Rx(packetTx, sampleRate, param)
    thisPath = mfilename("fullpath");
    thisPath = thisPath(1: end-strlength("Tx2Rx"));

    padTime = 10e-3;
    capNum = 3;
    noiseNum = 1000;
    zadoffSet = [139 839]; % ascent
    if ~exist(thisPath+"Buffer", "dir")
        mkdir(thisPath+"Buffer")
    else
        delete(thisPath+"Buffer/*");
    end

    packetLen = size(packetTx);
    zadoffNum = length(zadoffSet);

    zadoffTx = [];
    for zadoffIdx = 1: zadoffNum
        zadoffLen = zadoffSet(zadoffIdx);
        zadoff = repmat(zadoffChuSeq(25, zadoffLen), 2, 1);
        zadoffTx = [zadoffTx; 0.3*zadoff; zeros(zadoffLen*2, 1)]; %#ok<AGROW>
    end
    headLen = size(zadoffTx, 1);

    padLen = round(padTime * sampleRate);
    padTx = zeros(padLen, 1);

    waveTx = [padTx; zadoffTx; packetTx; padTx];
    waveLen = size(waveTx, 1);
    Wave2File(thisPath+"Buffer/Tx.bin", waveTx);

    while 1
        try
            system("bash "+thisPath+"Tx2Rx.sh " + ...
                param.carrier+" "+sampleRate+" "+ ...
                param.deviceTx+" "+param.subdevTx+" "+param.gainTx+" "+thisPath+"Buffer/Tx.bin "+ ...
                param.deviceRx+" "+param.subdevRx+" "+param.gainRx+" "+thisPath+"Buffer/Rx.bin "+ ...
                capNum*waveLen);
            waveRx = File2Wave(thisPath+"Buffer/Rx.bin").';

            [offsetList, corrList] = ZadoffDetection( ...
                waveRx(waveLen+1: 2*waveLen).', zadoffSet(end), zadoffSet(end), 0.8);
            [~, index] = max(corrList);
            offset = offsetList(index(1)) + waveLen + 4*zadoffSet(end) - headLen;
            if(offset<0)
                continue;
            end
            offsetHead = offset;
            offsetPacket = offset + headLen;
        catch
            continue;
        end
        break;
    end

    figure(11);
    plot(1: size(waveRx), 20*log10(abs(waveRx+1e-10)));
    xline(offsetHead);
    xline(offsetPacket);
    xline(offsetPacket+packetLen);
    ylim([-100 0]);
    saveas(gcf, thisPath+"Buffer/detection.png");

    pfOffset = comm.PhaseFrequencyOffset( ...
        'SampleRate', sampleRate, ...
        'FrequencyOffsetSource', 'Input port');
    headOffset = 0;
    cfoSet = zeros(1, zadoffNum);
    for zadoffIdx = 1: zadoffNum
        zadoffLen = zadoffSet(zadoffIdx);

        zadoff_1 = waveRx(offsetHead+headOffset+(1: zadoffLen));
        zadoff_2 = waveRx(offsetHead+headOffset+zadoffLen+(1: zadoffLen));
        cfoSet(zadoffIdx) = -sampleRate/zadoffLen*angle(sum(zadoff_1.*conj(zadoff_2)))/2/pi;
        waveRx(offsetHead+1: offsetHead+headLen) = pfOffset(waveRx(offsetHead+1: offsetHead+headLen), -cfoSet(zadoffIdx));

        headOffset = headOffset + 4*zadoffLen;
    end
    cfo = sum(cfoSet);
    pfOffset = comm.PhaseFrequencyOffset( ...
        'SampleRate', sampleRate, ...
        'FrequencyOffsetSource', 'Input port');
    waveRx(offsetPacket: offsetPacket+packetLen) = pfOffset(waveRx(offsetPacket: offsetPacket+packetLen), -cfo);
    packetRx = waveRx(offsetPacket+1: offsetPacket+packetLen);

    noiseList = zeros(1, noiseNum);
    for noiseIdx = 1: noiseNum
        startIdx = round(length(waveRx)/noiseNum*(noiseIdx-1)) + 1;
        endIdx = round(length(waveRx)/noiseNum*(noiseIdx-1)) + round(4e-6*sampleRate);
        noiseSym = waveRx(startIdx: endIdx);
        noise = GetEnergy(noiseSym, round(4e-6*sampleRate));
        noiseList(noiseIdx) = noise;
    end
    noise = prctile(noiseList, 10);
    signal = GetEnergy(packetRx, round(4e-6*sampleRate)) - noise;
    snr = 10 * log10(signal/noise);
end