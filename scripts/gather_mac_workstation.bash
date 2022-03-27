#!/usr/bin/env bash

rsd gather packages.homebrew > brew.rsd.json
rsd combine brew.rsd.json > host.rsd.json
