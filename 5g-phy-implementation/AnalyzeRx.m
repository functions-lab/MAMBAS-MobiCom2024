function [EVM, BLER, BER, CSI] = AnalyzeRx(packetRx, paramTx, filePath)
    packetRx = packetRx - mean(packetRx);

    gridRx = nrOFDMDemodulate(paramTx.carrier, packetRx);
    [estChGridLayers, noiseEst] = nrChannelEstimate( ...
        paramTx.carrier, gridRx, paramTx.dmrsIndices, paramTx.dmrsSymbols, ...
        'CDMLengths', paramTx.pdsch.DMRS.CDMLengths);
    csiLinear = reshape(estChGridLayers, [], 1);
    CSI = csiLinear(paramTx.dmrsIndices);
    CSI = reshape(CSI, [], 4);
    estChGridLayers = myChannelEstimate(estChGridLayers, [3 4 11 12]);

    [pdschRaw, pdschHest] = nrExtractResources(paramTx.pdschIndices, gridRx, estChGridLayers);
    [pdschRx, csi] = nrEqualizeMMSE(pdschRaw, pdschHest, noiseEst);
    
    pdschTx = paramTx.pdschSymbols;
    evm = comm.EVM( ...
        ReferenceSignalSource="Estimated from reference constellation", ...
        ReferenceConstellation=pdschTx);
    EVM = evm(pdschRx);

    if filePath ~= ""
        figure;
        hold off;
        pdschIdxSide = [1: round(0.2*length(pdschRx)) round(0.8*length(pdschRx)): length(pdschRx)];
        scatter(real(pdschRx(pdschIdxSide)), imag(pdschRx(pdschIdxSide)));
        hold on;
        pdschIdxMid = round(0.2*length(pdschRx))+1: round(0.8*length(pdschRx));
        scatter(real(pdschRx(pdschIdxMid)), imag(pdschRx(pdschIdxMid)));
        hold on;
        scatter(real(pdschTx), imag(pdschTx), 50, 'Marker', '+', 'LineWidth', 2);
        axis([-1 1 -1 1]*1.2);
        grid on;
        if ~isempty(filePath)
            saveas(gcf, filePath+".png");
        end
    end

    [dlschLLRs,rxSymbols] = nrPDSCHDecode(paramTx.carrier,paramTx.pdsch,pdschRx,noiseEst);
    % Scale LLRs by CSI
    csi = nrLayerDemap(csi);                                    % CSI layer demapping
    for cwIdx = 1:paramTx.pdsch.NumCodewords
        Qm = length(dlschLLRs{cwIdx})/length(rxSymbols{cwIdx}); % Bits per symbol
        csi{cwIdx} = repmat(csi{cwIdx}.',Qm,1);                 % Expand by each bit per symbol
        dlschLLRs{cwIdx} = dlschLLRs{cwIdx} .* csi{cwIdx}(:);   % Scale
    end
    % DL-SCH Decoding
    paramTx.decodeDLSCH.TransportBlockLength = paramTx.trBlkSizes;
    [decbits, BLER] = paramTx.decodeDLSCH(dlschLLRs,paramTx.pdsch.Modulation,paramTx.pdsch.NumLayers, ...
        paramTx.harqEntity.RedundancyVersion,paramTx.harqEntity.HARQProcessID);
    % % HARQ Process Update
    % statusReport = updateAndAdvance(txsetting.harqEntity,blkerr,txsetting.trBlkSizes,txsetting.pdschInfo.G);    
    % disp("Slot "+(nSlot)+". "+statusReport);

    BER = biterr(decbits, paramTx.trBlk)/length(decbits);
end