"""Constants used in the app."""

RES_STR = {
    'app_name': 'cctl',
    'app_desc': 'cctl is the utility for coachbot control.',
    'cmd_command_help': 'Control Robot State',
    'cmd_command': 'command',
    'cmd_on': 'on',
    'cmd_off': 'off',
    'cmd_id': 'id',
    'cmd_on_help': 'Boot a range of robots up.',
    'cmd_off_help': 'Boot a range of robots down.',
    'cmd_arg_id_help': 'The robot id or range of ids to modify. ' +
                       r'Format must match one of: [\d], [\d-\d] or "all".',
    'unsupported_argument': 'Unsupported Argument Passed.',
    'bot_booting_msg': 'Booting coachbot %d %s.',
    'bot_all_booting_msg': 'Booting all coachbots %s.',
    'server_dir_missing': 'Could not find server directory: %s',
    'cmd_start': 'start',
    'cmd_start_desc': 'Starts user code on all on robots.',
    'cmd_pause': 'pause',
    'cmd_pause_desc': 'Pauses user code on all on robots.',
    'bot_operating_msg': 'Setting operating state of all bots to %s.',
    'cmd_blink': 'blink',
    'cmd_blink_desc': 'Blinks the LED on specified robots.',
    'bot_blink_msg': 'Blinking robot %d.',
    'bot_all_blink_msg': 'Blinking all robots.',
    'cmd_update': 'upload',
    'cmd_update_desc': 'Updates the code on all on robots.',
    'cmd_update_os_desc': 'Uploads a fresh copy of the OS as well as the ' +
                          'user code.',
    'usr_code_path_desc': 'The path to the user code.',
    'upload_msg': 'Uploading user code to all on robots.',
    'upload_os_msg': 'Uploading new operating system code to all on bots.',
    'conf_error': 'Configuration file error. Please ensure a configuration ' +
                  'file exists in ~/.config/coachswarm/cctl.conf or ' +
                  '/etc/coachswarm/cctl.conf. Creating ' +
                  '~/.config/coachswarm.cctl.conf',
    'conf_malformed': 'Malformed configuration file.'
}

ERROR_CODES = {
    'conf_error': 101,
    'server_dir_missing': 102
}
