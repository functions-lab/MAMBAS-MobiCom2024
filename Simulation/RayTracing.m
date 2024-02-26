clear;
clc;
close all;
rng(0);

%%

ueNum = 32;
distBound = [20, 100];
angleBound = [-30 +30];

%%

freq = 28.019e9;
latDist = 111.19e3;
latMin = 41.876 * latDist;
latMax = 41.887 * latDist;
longDist = 82.63e3;
longMin = -87.637 * longDist;
longMax = -87.625 * longDist;
gridSize = 100;

pathLossMax = 120;
trialMax = 2*ueNum;
resol = 0.5;

folder = "./Dataset/";
if ~exist(folder, 'dir')
    mkdir(folder);
end
pm = propagationModel("raytracing", ...
    "Method", "sbr", ...
    "MaxNumReflections", 2, ...
    "MaxNumDiffractions", 1);
dataNum = 0;
pathLossList = [];
for longBS = longMin: gridSize: longMax
    for latBS = latMin: gridSize: latMax
        dataNum = dataNum + 1;
        if ~exist(folder+"Scenario_"+dataNum, 'dir')
            mkdir(folder+"Scenario_"+dataNum);
        end

        direcSet = zeros(1, ueNum);
        trialNum = 0;
        for ueIdx = 1: ueNum
            while 1
                trialNum = trialNum + 1;
                ueDist = unifrnd(distBound(1), distBound(2));
                direc = unifrnd(angleBound(1), angleBound(2));
                if(ueIdx>1)&&(min(abs(direcSet(1: ueIdx-1)-direc))<=resol)
                    continue
                end
                longUE = longBS + ueDist * sin(direc/360*2*pi);
                latUE = latBS + ueDist * cos(direc/360*2*pi);
    
                viewer = siteviewer("Buildings", "chicago.osm");
                BS = txsite("Latitude", latBS/latDist, ...
                    "Longitude", longBS/longDist, ...
                    "TransmitterFrequency", freq);
                show(BS);
                UE = rxsite("Latitude", latUE/latDist, ...
                    "Longitude", longUE/longDist, ...
                    "AntennaHeight", 30);
                show(UE);
                raytrace(BS, UE, pm);
                rays = raytrace(BS, UE, pm);
                close(viewer);
                
                pathLoss = [];
                phaseShift = [];
                AoD = [];
                LOS = 0;
                for raysIdx = 1: length(rays{1, 1})
                    AoDNow = rays{1, 1}(1, raysIdx).AngleOfDeparture(1)-90;
                    pathLossNow = rays{1, 1}(1, raysIdx).PathLoss;
                    if (AoDNow < angleBound(1))||(AoDNow > angleBound(2))||(pathLossNow>pathLossMax)
                        continue;
                    end
                    pathLoss = [pathLoss pathLossNow]; %#ok<AGROW> 
                    phaseShift = [phaseShift rays{1, 1}(1, raysIdx).PhaseShift/2/pi*360]; %#ok<AGROW> 
                    AoD = [AoD AoDNow]; %#ok<AGROW> 
                    if rays{1, 1}(1, raysIdx).LineOfSight
                        LOS = 1;
                    end
                end

                if (length(AoD) >= 1)||(trialNum > trialMax)
                    break;
                end
            end

            [~, index] = sort(pathLoss);
            pathLoss = pathLoss(index);
            phaseShift = phaseShift(index);
            AoD = AoD(index);
            save(folder+"Scenario_"+dataNum+"/UE_"+ueIdx+".mat", "pathLoss", "phaseShift", "AoD", "LOS");

            pathLossList = [pathLossList min(pathLoss)]; %#ok<AGROW>
            figure(1);
            cdfplot(pathLossList);
        end
        if trialNum > trialMax
            dataNum  = dataNum - 1;
        end
    end
end
