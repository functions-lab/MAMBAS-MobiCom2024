function [packetTx, paramTx] = GenerateTx(param)
    paramTx = {};
    nSlot = 0;

    CarrierCfg = nrCarrierConfig( ...
        'NCellID', 1, ...
        'SubcarrierSpacing', param.subBand, ...
        'NSizeGrid', param.rbNum, ...
        'NSlot', 0, ...
        'NFrame', 0);

    Dmrs = nrPDSCHDMRSConfig( ...
        "DMRSAdditionalPosition", 1, ...
        "DMRSConfigurationType", 1, ...
        "DMRSLength", 2);
    PdschCfg = nrPDSCHConfig( ...
        "Modulation", param.modu, ...
        "PRBSet", 0: param.rbNum-1, ...
        "NumLayers", param.ant, ...
        "RNTI", 1, ...
        "DMRS", Dmrs);

    NHARQProcesses = 16;     % Number of parallel HARQ processes
    rvSeq = [0 2 3 1];
    % Create DL-SCH encoder object
    encodeDLSCH = nrDLSCH;
    encodeDLSCH.MultipleHARQProcesses = true;
    encodeDLSCH.TargetCodeRate = param.code;
    
    % Create DLSCH decoder object
    decodeDLSCH = nrDLSCHDecoder;
    decodeDLSCH.MultipleHARQProcesses = true;
    decodeDLSCH.TargetCodeRate = param.code;
    decodeDLSCH.LDPCDecodingAlgorithm = "Normalized min-sum";
    decodeDLSCH.MaximumLDPCIterationCount = 6;
    % HARQ Management
    harqEntity = HARQEntity(0:NHARQProcesses-1,rvSeq,PdschCfg.NumCodewords);
    
    % Channel Configuration
    nTxAnts = param.ant;
    nRxAnts = param.ant;
    % Check that the number of layers is valid for the number of antennas
    if PdschCfg.NumLayers > min(nTxAnts,nRxAnts)
        error("The number of layers ("+string(PdschCfg.NumLayers)+") must be smaller than min(nTxAnts,nRxAnts) ("+string(min(nTxAnts,nRxAnts))+")")
    end
    
    channel = nrTDLChannel;
    channel.DelayProfile = "TDL-C";
    channel.NumTransmitAntennas = nTxAnts;
    channel.NumReceiveAntennas = nRxAnts;
    ofdmInfo = nrOFDMInfo(CarrierCfg);
    channel.SampleRate = ofdmInfo.SampleRate;
    
    estChannelGrid = getInitialChannelEstimate(channel,CarrierCfg);
    newPrecodingWeight = getPrecodingMatrix(PdschCfg.PRBSet,PdschCfg.NumLayers,estChannelGrid);

    % for nSlot = 0:totalNoSlots-1

    % New slot
    CarrierCfg.NSlot = nSlot;
    % Generate PDSCH indices info, which is needed to calculate the transport
    % block size
    [pdschIndices,pdschInfo] = nrPDSCHIndices(CarrierCfg,PdschCfg);

    % Calculate transport block sizes
    Xoh_PDSCH = 0;
    trBlkSizes = nrTBS(PdschCfg.Modulation,PdschCfg.NumLayers,numel(PdschCfg.PRBSet),pdschInfo.NREPerPRB,param.code,Xoh_PDSCH);

    % Get new transport blocks and flush decoder soft buffer, as required
    for cwIdx = 1:PdschCfg.NumCodewords
        if harqEntity.NewData(cwIdx)
            % Create and store a new transport block for transmission
            trBlk = randi([0 1],trBlkSizes(cwIdx),1);
            setTransportBlock(encodeDLSCH,trBlk,cwIdx-1,harqEntity.HARQProcessID);

            % If the previous RV sequence ends without successful
            % decoding, flush the soft buffer
            if harqEntity.SequenceTimeout(cwIdx)
                resetSoftBuffer(decodeDLSCH,cwIdx-1,harqEntity.HARQProcessID);
            end
        end
    end

    codedTrBlock = encodeDLSCH(PdschCfg.Modulation,PdschCfg.NumLayers,pdschInfo.G,harqEntity.RedundancyVersion,harqEntity.HARQProcessID);
    pdschSymbols = nrPDSCH(CarrierCfg,PdschCfg,codedTrBlock);
    precodingWeights = newPrecodingWeight;
    pdschSymbolsPrecoded = pdschSymbols*precodingWeights;
    dmrsSymbols = nrPDSCHDMRS(CarrierCfg,PdschCfg);
    dmrsIndices = nrPDSCHDMRSIndices(CarrierCfg,PdschCfg);
    pdschGrid = nrResourceGrid(CarrierCfg,nTxAnts);
    [~,pdschAntIndices] = nrExtractResources(pdschIndices,pdschGrid);
    pdschGrid(pdschAntIndices) = pdschSymbolsPrecoded;
    % PDSCH DM-RS precoding and mapping
    for p = 1:size(dmrsSymbols,2)
        [~,dmrsAntIndices] = nrExtractResources(dmrsIndices(:,p),pdschGrid);
        pdschGrid(dmrsAntIndices) = pdschGrid(dmrsAntIndices) + dmrsSymbols(:,p)*precodingWeights(p,:);
    end
    [packetTx, waveformInfo] = nrOFDMModulate(CarrierCfg, pdschGrid);

    packetTx = 0.3/sqrt(mean(abs(packetTx).^2)) * packetTx;

    % record everything and return 
    paramTx.trBlk = trBlk;
    paramTx.carrier = CarrierCfg;
    paramTx.dmrsIndices = dmrsIndices;
    paramTx.dmrsSymbols = dmrsSymbols;
    paramTx.pdsch = PdschCfg;
    paramTx.pdschIndices = pdschIndices;
    paramTx.precodingWeights = precodingWeights;
    paramTx.trBlkSizes = trBlkSizes;
    paramTx.harqEntity = harqEntity;
    paramTx.pdschInfo = pdschInfo;
    paramTx.pdschSymbols = pdschSymbols;
    paramTx.decodeDLSCH = decodeDLSCH;
end
    
function wtx = getPrecodingMatrix(PRBSet,NLayers,hestGrid)
% Calculate precoding matrix given an allocation and a channel estimate
    
    % Allocated subcarrier indices
    allocSc = (1:12)' + 12*PRBSet(:).';
    allocSc = allocSc(:);
    
    % Average channel estimate
    [~,~,R,P] = size(hestGrid);
    estAllocGrid = hestGrid(allocSc,:,:,:);
    Hest = permute(mean(reshape(estAllocGrid,[],R,P)),[2 3 1]);
    
    % SVD decomposition
    [~,~,V] = svd(Hest);
    
    wtx = V(:,1:NLayers).';
    wtx = wtx/sqrt(NLayers); % Normalize by NLayers
end

function estChannelGrid = getInitialChannelEstimate(channel,carrier)
% Obtain an initial channel estimate for calculating the precoding matrix.
% This function assumes a perfect channel estimate

    % Clone of the channel
    chClone = channel.clone();
    chClone.release();

    % No filtering needed to get channel path gains
    chClone.ChannelFiltering = false;    
    
    % Get channel path gains
    [pathGains,sampleTimes] = chClone();
    
    % Perfect timing synchronization
    pathFilters = getPathFilters(chClone);
    offset = nrPerfectTimingEstimate(pathGains,pathFilters);
    
    % Perfect channel estimate
    estChannelGrid = nrPerfectChannelEstimate(carrier,pathGains,pathFilters,offset,sampleTimes);
end

function refPoints = getConstellationRefPoints(mod)
% Calculate the reference constellation points for a given modulation
% scheme.
    switch mod
        case "QPSK"
            nPts = 4;
        case "16QAM"
            nPts = 16;
        case "64QAM"
            nPts = 64;
        case "256QAM"
            nPts = 256;            
    end
    binaryValues = int2bit(0:nPts-1,log2(nPts));
    refPoints = nrSymbolModulate(binaryValues(:),mod);
end