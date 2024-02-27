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

    param.subdevTx = "A:0";
    param.deviceTx = "192.168.70.3";
    param.gainTx = 15;
    
    param.deviceRx = "192.168.70.9";
    param.subdevRx = "A:0";
    param.gainRx = 15;
end