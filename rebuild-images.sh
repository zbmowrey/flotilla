#!/bin/bash

IDS=( "7044b4d1d8e3" "d4b0610b9df2" "0660330c6c96" "1fd0e31dbdae" "28e4dd1ee8b3" "48c3c8a9a17f" "afd333b5ff0d" "641c4864cf8c" "c1d188beb52f" "018c2cccd8b1" )

for id in ${IDS[@]}
do
    docker image rm $id
done
