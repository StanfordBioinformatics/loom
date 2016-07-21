#!/usr/bin/env bats

@test "docker binary is in path" {
    command -v docker
}

@test "verify sysconfig settings" {
    grep '\--userland-proxy=false --bip=192.168.200.1/22' /etc/sysconfig/docker
}

@test "docker0 bridge exists" {
    ip a s docker0
}
