#!/bin/sh

target_version="$1"
t_ver_spl=$(echo -n "$target_version" | tr "." " ")
t_ver_maj=$(echo -n "$t_ver_spl" | awk '{ print $1 }')
t_ver_min=$(echo -n "$t_ver_spl" | awk '{ print $2 }')

for binary in $(ls -1 /usr/bin/python* | grep '.*[2-3]\(.[0-9]\+\)\?$'); do
    version=$($binary --version 2>&1 | tr -d '\n' | awk '{ print $2; }' \
                | tr "." " ")

    ver_maj=$(echo -n "$version" | awk '{ print $1 }')
    ver_min=$(echo -n "$version" | awk '{ print $2 }')

    if test "$ver_maj" -lt "$t_ver_maj"; then
        continue
    fi

    if test "$(echo -n "$version" | awk '{ print $2 }')" -ge "$t_ver_min"; then
        echo "$binary"
        exit 0
    fi
done
