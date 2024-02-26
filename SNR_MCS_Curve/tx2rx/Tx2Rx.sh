#!/bin/bash

carrier=$1
rate=$2

deviceTx=$3
subdevTx=$4
gainTx=$5
fileTx=$6

deviceRx=$7
subdevRx=$8
gainRx=$9
fileRx=${10}

waveLen=${11}

${0%/*}/tx_samples_from_file --args addr=$deviceTx --subdev $subdevTx --ant "TX/RX" --gain $gainTx --file $fileTx --type float --freq $carrier --rate $rate --repeat &
pid=$!
sleep 3s
${0%/*}/rx_samples_to_file --args addr=$deviceRx --subdev $subdevRx --ant "RX2" --gain $gainRx --file $fileRx --type float --freq $carrier --rate $rate --nsamps $waveLen
kill -9 $pid