clear;
clc;
close all;
addpath(genpath("tx2rx"));
rng(0);

%%

param = GetParam();

[packetTx, paramTx] = GenerateTx(param);

[packetRx, SNR, CFO] = Tx2Rx(0.5*packetTx, 50e6, param);
disp("CFO: "+CFO+" Hz");
disp("SNR: "+SNR+" dB");

[EVM, BLER, BER, CSI] = AnalyzeRx(packetRx, paramTx, "Constel");
disp("EVM: "+EVM+" %");
% Please repeat this transmission to have an averaged BLER
disp("BLER: "+BLER*100+" %");
disp("BER: "+BER*100+" %");

figure;
subplot(2, 1, 1);
plot(abs(CSI));
subplot(2, 1, 2);
plot(angle(CSI));