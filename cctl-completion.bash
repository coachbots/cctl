#!/usr/bin/env bash

SUPPORTED_COMMANDS=('on' 'off' 'blink' 'start' 'pause' 'upload' 'manage')
ID_ARG_COMMANDS=('on' 'off' 'blink')

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
    # If the user is asking for help, that should be the first thing we
    # suggest.
    if _is_flag; then
        COMPREPLY+=('--help')
    fi

    # If we're working on the upload, let's try to suggest the flags.
    if [ "${COMP_WORDS[1]}" == "upload" ]; then
        if _is_flag; then
            COMPREPLY+=('--operating-system');
        # Otherwise, we can suggest the files.
        else
            COMPREPLY+=($(compgen -A file ${COMP_WORDS[COMP_CWORD]}))
        fi
    # Else if we are writing an ID-arg command, let's suggest "all"
    elif _is_id_arg && [ $COMP_CWORD -eq 2 ]; then
        COMPREPLY+=('all')
    # If we're still on the subcommand, let's suggest the subommand
    elif [ $COMP_CWORD -eq 1 ] && ! _is_flag; then
        COMPREPLY+=($(compgen -W "${SUPPORTED_COMMANDS[*]} " ${COMP_WORDS[1]}))
    fi
}

complete -F _cctl_completions cctl
