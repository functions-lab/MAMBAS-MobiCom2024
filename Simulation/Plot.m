clear;
clc;
close all;

scenarioShow = 1;
ueNum = 8;
slotNum = 20;
filePath = "Result/";
methodList = ["DP_Individual", "TDMA_MU-Conjugate", "All_MU-ZF", "Spacing_MU-ZF", "Spacing_Nullify"];
legendList = ["Mambas", "Analog SUBF", "ZF", "ZF+S^2-MAS", "Nulli-Fi"];

colorList = { ...
    [0 0.4470 0.7410], [0.8500 0.3250 0.0980], [0.9290 0.6940 0.1250], ...
    [0.4940 0.1840 0.5560], [0.4660 0.6740 0.1880], [0.3010 0.7450 0.9330], ...
    [0.6350 0.0780 0.1840]};

%%
figure;
title("Rate");
for methodIdx = 1: length(methodList)
    method = methodList(methodIdx);
    color = colorList{methodIdx};
    speedMatList = load(filePath+"/Result_"+method+".mat").speedMatList(:, 1: slotNum, :);

    speedMat = reshape(speedMatList(scenarioShow, :, :), [slotNum, ueNum]);
    
    subplot(length(methodList), 1, methodIdx);
    heatmap(speedMat.', 'ColorLimits', [0 500]);
    xlabel("Slot");
    ylabel("UE");
    title(legendList(methodIdx));
end

%%

figure;
speedList = NaN(length(methodList), 1000);
for methodIdx = 1: length(methodList)
    method = methodList(methodIdx);
    speedMatList = load(filePath+"/Result_"+method+".mat").speedMatList(:, 1: slotNum, :);
    dataNum = size(speedMatList, 1);
    
    for dataIdx = 1: dataNum
        speedAvg = mean(reshape(speedMatList(dataIdx, :, :), [slotNum, ueNum]), 1);
        speedList(methodIdx, dataIdx) = sum(speedAvg);
    end
end

for methodIdx = 1: length(methodList)
    h = cdfplot(speedList(methodIdx, :));
    set(h, 'linewidth', 2);
    set(gca, 'linewidth', 1.5, 'fontsize', 20, 'fontname', 'Arial');
    hold on;
end
title('$M=8, N_s=32, U=8$', 'interpreter', 'latex');
xlabel("Sum Rate (Gbps)");
xlim([0 3000]);
ylabel('CDF');
xticks([0  500  1000  1500  2000  2500  3000 3500]);
xticklabels(["0.0", "0.5", "1.0", "1.5", "2.0", "2.5", "3.0", "3.5"]);
box on;
grid on;
leg = legend(legendList, Location="southeast", Fontsize=16);
leg.ItemTokenSize = [20, 20, 20, 20, 20];