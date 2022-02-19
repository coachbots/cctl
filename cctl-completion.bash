#!/usr/bin/env bash

SUPPORTED_COMMANDS=('on' 'off' 'blink' 'start' 'pause' 'upload' 'manage' \
                    'cam' 'fetch-logs')
ID_ARG_COMMANDS=('on' 'off' 'blink' 'fetch-logs')

function _is_flag()
{
    if [[ "${COMP_WORDS[COMP_CWORD]}" =~ ^- ]]; then
        return 0
    else
        return 1
    fi
}

function _is_id_arg()
{
    if [[ " ${ID_ARG_COMMANDS[*]} " =~ " ${COMP_WORDS[1]} " ]]; then
        return 0
    else
        return 1
    fi
}

function _cctl_completions()
{
    if [ "${COMP_WORDS[1]}" == "fetch-logs" ]; then
        if [ "${COMP_WORDS[COMP_CWORD - 1]}" == "--directory" ] || \
           [ "${COMP_WORDS[COMP_CWORD - 1]}" == "-d" ]; then
            COMPREPLY+=($(compgen -d))
        fi
        COMPREPLY+=($(compgen -W "--legacy --directory" -- \
            "${COMP_WORDS[COMP_CWORD]}" ))
        COMPREPLY+=($(compgen -W "all" -- "${COMP_WORDS[COMP_CWORD]}" ))

    elif [ "${COMP_WORDS[1]}" == "cam" ]; then
        if [ "$COMP_CWORD" == "2" ]; then
            COMPREPLY+=($(compgen -W "setup preview" -- \
                "${COMP_WORDS[COMP_CWORD]}"))
        fi

    elif [ "${COMP_WORDS[1]}" == "on" ]; then
        COMPREPLY+=($(compgen -W "all" -- "${COMP_WORDS[COMP_CWORD]}"))
    
    elif [ "${COMP_WORDS[1]}" == "off" ]; then
        COMPREPLY+=($(compgen -W "all" -- "${COMP_WORDS[COMP_CWORD]}"))

    elif [ "${COMP_WORDS[1]}" == "blink" ]; then
        COMPREPLY+=($(compgen -W "all" -- "${COMP_WORDS[COMP_CWORD]}"))

    elif [ "${COMP_WORDS[1]}" == "upload" ]; then
        COMPREPLY+=($(compgen -f -- \
            "${COMP_WORDS[COMP_CWORD]}"))
        COMPREPLY+=($(compgen -W "--operating-system" -- \
            "${COMP_WORDS[COMP_CWORD]}"))


    elif [ $COMP_CWORD -eq 1 ] && ! _is_flag; then
        COMPREPLY+=($(compgen -W "${SUPPORTED_COMMANDS[*]}" -- ${COMP_WORDS[1]}))
    fi
}

complete -F _cctl_completions cctl
