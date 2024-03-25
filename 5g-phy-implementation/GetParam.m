function param = GetParam()
    % Wireless Setting
    param.modu = "16QAM";
    param.code = 490/1024;
    param.rbNum= 64;

    param.ant = 1; % Only supports 1
    param.subBand = 120; % [15, 30, 60, 120, 240] kHz
    param.subNum = 12; % Read Only

    param.sampleRate = 12 * param.subBand*1e3 * param.rbNum / 0.75;

    % USRP Setting
    param.carrier = 3.0e9;

    param.subdevTx = "B:1";
    param.deviceTx = "10.117.2.1";
    param.gainTx = 30;
    
    param.deviceRx = "10.117.3.1";
    param.subdevRx = "B:1";
    param.gainRx = 40;
end