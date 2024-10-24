instruction_info = {
    0xB9: {
        'method': 'power_down',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': None,
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,
    },

    0xAB: {
        'method': 'release_power_down',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': None,
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,
    },
    # VERIFIED
    0x06: {
        'method': 'write_enable',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'return_data': False,
        'dependencies': None,
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,
    },

    0x50: {
        'method': 'write_enable_volatile_status_register',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': None,
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,
    },

    
    0x04: {
        'method': 'write_disable',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': None,
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,
    },
    0x03: {
        'method': 'read',
        'instruction_bytes': 1,
        'address_bytes': 3,
        'dummy_bytes': 2,
        'data_min': 0,
        'data_max': 0,  # Variable data length
        'dependencies': None,
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,
    },
    0x02: {
        'method': 'page_program',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 1,
        'data_max': 256,
        'dependencies': ['write_enable'],
        'busy_block': True,
        'busy_lock': True,
        'execution_overhead': 5,  # Example value, adjust as needed
        'notes': 'wrap arround > 256'
    },
    0x20: {
        'method': 'erase_sector',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 3,
        'data_max': 3,
        'dependencies': ['write_enable'],
        'busy_block': True,
        'busy_lock': True,
        'execution_overhead': 10,  # Example value, adjust as needed
    },
    0xC7: {
        'method': 'chip_erase',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': ['write_enable'],
        'busy_block': True,
        'busy_lock': True,
        'execution_overhead': 100,  # Example value, adjust as needed
    },
    0x60: {
        'method': 'chip_erase',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': ['write_enable'],
        'busy_block': True,
        'busy_lock': True,
        'execution_overhead': 100,  # Example value, adjust as needed
    },
    0x9F: {
        'method': 'read_jedec_id',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_in': False,
        'data_out': True,
        'data_min': 0,
        'data_max': 3,
        'dependencies': None,
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,
    },
    0x75: {
        'method': 'erase_program_suspend',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': None,
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,
    },
    0x7A: {
        'method': 'erase_program_resume',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': None,
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,
    },
    0x7E: {
        'method': 'global_block_sector_lock',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 2,
        'data_max': 2,
        'dependencies': None,
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,
    },
    0x98: {
        'method': 'global_block_sector_unlock',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 2,
        'data_max': 2,
        'dependencies': None,
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,
    },
    0x01: {
        'method': 'write_status_register',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': ['write_enable'],
        'busy_block': True,
        'busy_lock': True,
        'execution_overhead': 5,  # Example value, adjust as needed
    },
    0x31: {
        'method': 'write_status_register',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': ['write_enable'],
        'busy_block': True,
        'busy_lock': True,
        'execution_overhead': 5,  # Example value, adjust as needed
    },
    0x11: {
        'method': 'write_status_register',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': ['write_enable'],
        'busy_block': True,
        'busy_lock': True,
        'execution_overhead': 5,  # Example value, adjust as needed
    },

    0x05: {
        'method': 'read_status_register',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': None,
        'busy_block': False,
        'busy_lock': False,
        'execution_overhead': 0,  # Example value, adjust as needed
    },     

    0x35: {
        'method': 'read_status_register',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': None,
        'busy_block': False,
        'busy_lock': False,
        'execution_overhead': 0,  # Example value, adjust as needed
    },

    0x15: {
        'method': 'read_status_register',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': None,
        'busy_block': False,
        'busy_lock': False,
        'execution_overhead': 0,  # Example value, adjust as needed
    },
    0x4B: {
        'method': 'read_unique_device_id',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': None,
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,  # Example value, adjust as needed
    },
    0x90: {
        'method': 'read_manufacturer_device_id',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': None,
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,  # Example value, adjust as needed
    },
    0x36: {
        'method': 'individual_lock',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': ['write_enable'],
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,  # Example value, adjust as needed
    },
    0x39: {
        'method': 'individual_unlock',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': ['write_enable'],
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,  # Example value, adjust as needed
    },

    0x3D: {
        'method': 'read_block_sector_lock',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': None,
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,  # Example value, adjust as needed
    },

    0x5A: {
        'method': 'read_sfdp_register',
        'instruction_bytes': 1,
        'dummy_bytes': 1,
        'data_min': 0,
        'data_max': 0,
        'dependencies': None,
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,  # Example value, adjust as needed
    },

    0x44: {
        'method': 'erase_security_register',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': ['write_enable'],
        'busy_block': True,
        'busy_lock': True,
        'execution_overhead': 0,  # Example value, adjust as needed
    },

    0x42: {
        'method': 'program_security_register',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': ['write_enable'],
        'busy_block': True,
        'busy_lock': True,
        'execution_overhead': 0,  # Example value, adjust as needed
    },


    0x48: {
        'method': 'read_security_register',
        'instruction_bytes': 1,
        'dummy_bytes': 0,
        'data_min': 0,
        'data_max': 0,
        'dependencies': None,
        'busy_block': True,
        'busy_lock': False,
        'execution_overhead': 0,  # Example value, adjust as needed
    },

       
}

