# MobiCom'24 Mambas

In this repository, you can find two components of codes in `Mambas`:

a) the 5G PHY implementation on the COSMOS testbed (labeled as [Testbed] in paper),

b) the ray-tracing based simulations (labeled as [Simulation] in the paper).

## Prerequisite
**Python**
1. `numpy`: e.g., `conda install anaconda::numpy`
2. `tqdm`: e.g., `conda install conda-forge::tqdm`
3. `scipy`: e.g., `conda install anaconda::scipy`
4. `matplotlib`: e.g., `conda install conda-forge::matplotlib`
5. `casadi`: e.g., `conda install conda-forge::casadi`

**MATLAB**
1. `5G Toolbox`

**UHD**

UHD 4.5.0 is recommended, and in this case, you can skip [Step 1](./5g-phy-implementation).

## 5G PHY Implementation

This 5G PHY implementation measures the over-the-air metrics, SNR, EVM, BLER, BER and etc, under an over-the-air USRP setting. 

You can find the codes in the folder [5g-phy-implementation](./5g-phy-implementation), and eventually, you can implement the SNR-MCS curves as shown in Fig. 8 in the paper (shown below).

![alt text](exp_sb2_rate_snr.png)

## Ray-Tracing based Simulations

There are three steps in the simulations:
1. Generate the Ray-Tracing dataset in MATLAB
2. Perform Mambas or other baselines on the generated Ray-Tracing dataset
3. Plot the simulation results

You can find the codes in the folder [ray-tracing-based-simulations](./ray-tracing-based-simulations), and eventually, you can implement the simulation experiments as shown in Fig. 13-14 in the paper (shown below).

![alt text](sim-cdf-sum-rate-new.png)

![alt text](sim-bar-varying-param-new.png)

## Reference

If you find our work useful in your research, please consider citing our paper:

```console
@inproceedings{gao2024mambas,
  title={Mambas: Maneuvering analog multi-user beamforming using an array of subarrays in mmWave networks},
  author={Gao, Zhihui and Qi, Zhenzhou and Chen, Tingjun},
  booktitle={Proc. ACM MobiCom'24},
  year={2024}
}
```

If you have any further questions, please feel free to contact us at :D

zhihui.gao@duke.edu
