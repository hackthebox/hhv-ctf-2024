from mem_config import *
from instruction_set import *

from chall_scenario import *

DEBUG = False
INFO = True
INFO2 = False

def get_address(address_list, bit_count=24):
    byte_count = int(bit_count/8)
    address = 0
    # Ensure we only process the first 3 bytes, even if the list is longer
    for i, byte in enumerate(address_list[:byte_count]):
        address |= byte << (8 * (2 - i))  # 2 - i, because we're focusing on the first 3 bytes

    #address &= 0xffff00

    return address



def set_last_bit(bit_bool, value=0x00):
    # Clear the last bit
    value &= ~1
    # Set the last bit based on bit_bool
    if bit_bool:
        value |= 1
    return value


class FlashMemorySimulation:

    def __init__(self, capacity_bytes=16*1024*1024, sector_size=4096, page_size=256, sectors_per_block=16):
 
        # Memory configuration
        self.capacity_bytes = capacity_bytes  # Total capacity of the flash memory
        self.sector_size = sector_size  # Size of each sector
        self.page_size = page_size  # Size of each page
        self.sectors_per_block = sectors_per_block  # Sectors per block
        self.blocks = capacity_bytes // (sector_size * sectors_per_block)  # Total number of blocks
        

        # CHALLENGE UPDATES
        challenge_data = create_data_with_hash(SECRET, SECRET_POS)
        self.memory = [0xFF] * (capacity_bytes - len(challenge_data))  # Main memory space, initialized to all 1s (erased state)
        self.memory  = challenge_data + self.memory


        self.block_size = 0x10000  # 64KB block size
     
        #self.write_enabled = False
        # Simulated JEDEC ID and Unique Device ID (example values)
        self.jedec_id = JEDEC_ID # Example JEDEC ID: Manufacturer, Memory Type, Capacity
        self.device_id = DEVICE_ID 
        self.sfdp_data = SFDP_DATA
        self.unique_device_id = CHIP_UID  # Example Unique ID
        
        self.sfdp_register = SFDP_REGISTER
        # Define operation delay generators with a bias towards typical timing
        # TODO: UPDATE WITH ACTUAL VALUES
        
        self.realistic_speed = False
        self.write_status_register_delay = self.generate_delay_function(0.001, 0.00099, 0.015, typical_probability=0.9)

        self.page_program_delay = self.generate_delay_function(0.0007, 0.002, 0.003, typical_probability=0.9)
        self.sector_erase_delay = self.generate_delay_function(0.045, 0.042, 0.4, typical_probability=0.9)
        self.block_erase_delay = self.generate_delay_function(2.0, 1.8, 2.2, typical_probability=0.9)
        self.chip_erase_delay = self.generate_delay_function(40, 35, 200, typical_probability=0.9)


        self.operation_suspended = False

        # Status Register 1 bits description
        '''
        Status Register 1 bits:
        - 7 (SRP): Status register protect 0.
        - 6 (SEC): Sector protect bit.
        - 5 (TB): Top/Bottom protect bit.
        - 4 (BP2): Block protect bit 2.
        - 3 (BP1): Block protect bit 1.
        - 2 (BP0): Block protect bit 0.
        - 1 (WEL): Write enable latch. - VOLATILE
        - 0 (BUSY): Write in progress (WIP) bit. - VOLATILE
        '''

        # Status Register 2 bits description
        '''
        Status Register 2 bits:
        - 7 (SUS): Suspend status bit.
        - 6 (CMP): Complement protect bit. - VOLATILE/Non
        - 5 (LB3): Security register lock bit 3. - VOLATILE/Non
        - 4 (LB2): Security register lock bit 2. - VOLATILE/Non
        - 3 (LB1): Security register lock bit 1. - VOLATILE/Non
        - 2: Reserved.  // CHANGED
        - 1 (QE): Quad enable bit. - VOLATILE/Non
        - 0 (SRL): Status register protect 1. - VOLATILE/Non

        '''

        # Status Register 3 bits description
        '''
        Status Register 3 bits:
        - 7: Reserved. 
        - 6 (DRV1): Output driver strength. - VOLATILE/Non
        - 5 (DRV0): Output driver strength. - VOLATILE/Non
        - 4: Reserved.
        - 3: Reserved.
        - 2 (WPS): Write protect selection. - VOLATILE/Non
        - 1: Reserved.
        - 0: Reserved.
        '''

        # Configuration Register bits description
        '''
        Configuration Register bits:
        Note: Specific bit assignments can vary significantly between devices.
        This register often includes bits for controlling features like dummy cycles for fast reads,
        hardware reset function, and others depending on the device.
        '''

        # Registers
        # Initialize the Status Registers and Configuration Register
        self.registers = {
            'Status Register 1': 0b00000000,  # Controls basic operations like write protection. Bit 1 (WEL) is the write enable latch.
            'Status Register 2': 0b00000000,  # Provides additional status and control bits, such as QE (Quad Enable).
            'Status Register 3': 0b00000000,  # Contains more device-specific settings, such as drive strength.
            #'Configuration Register': 0b00000100,  # Used for configuring device features and operational parameters.
        }
        

        # Initialize a dictionary to track volatile writes
        self.volatile_writes = {
            'Status Register 1': None,
            'Status Register 2': None,
            'Status Register 3': None,
            #'Configuration Register': None,
        }

        # Security Registers with OTP locks
        # Simulate 3x256-byte security registers that can be locked once written
        self.security_registers = [[0xFF] * 256 for _ in range(3)]  # 3 security registers
  

        # Mapping of instruction bytes to their corresponding methods
        self.instruction_map = {
            0xB9: self.power_down, # TESTED
            0xAB: self.release_power_down, # TESTED
            0x06: self.write_enable, # TESTED
            0x04: self.write_disable, # TESTED
            0x03: self.read, # TESTED
            0x02: self.page_program, # TESTED
            0x20: self.erase_sector, # TESTED
            #0x52: self.block_erase_32kb,
            #0xD8: self.block_erase_64kb,
            0xC7: self.chip_erase, # TESTED
            0x60: self.chip_erase,  # TESTED # Chip Erase has two valid codes
            0x90: self.read_manufacturer_device_id,
            0x4B: self.read_unique_device_id, # TESTED
            0x9F: self.read_jedec_id,
            0x75: self.erase_program_suspend,
            0x7A: self.erase_program_resume,
            0x7E: self.global_block_sector_lock,
            0x98: self.global_block_sector_unlock,

            # instruction code checks happen inside function 
            0x01: self.write_status_register,
            0x31: self.write_status_register,
            0x11: self.write_status_register,
            
            0x05: self.read_status_register,
            0x35: self.read_status_register,
            0x15: self.read_status_register,


            0x36: self.individual_lock,
            0x39: self.individual_unlock,
            0x3D: self.read_block_sector_lock,
            0x5A: self.read_sfdp_register,

            0x44: self.erase_security_register,
            0x42: self.program_security_register,
            0x48: self.read_security_register
        }
        

        # TODO: UPDATE BASED ON DATASHEET TRUTH TABLE PAGE: 18
        self.BLOCK_PROTECT_RANGES = {
            0b000: None,  # No protection
            0b001: (0, 0x1FFFF),  # Protect the first 1/8 of memory
            0b010: (0, 0x3FFFF),  # Protect the first 1/4 of memory
            0b011: (0, 0x7FFFF),  # Protect the first 1/2 of memory
            # Add more mappings based on your device's specification
        }

        self.driver_strength_settings = {
            '00': 'Maximum',
            '01': 'High',
            '10': 'Medium',
            '11': 'Lowest'
        }

        self.WP_pin = 0

        # Default driver strength is the lowest, assuming all bits are cleared
        self.current_driver_strength = 'Lowest'

        # Initialize DRV1 and DRV0 bits to 1, setting driver strength to Maximum by default
        self.set_driver_strength(1, 1)  # Set DRV1=1 and DRV0=1

        # Initialize all block locks to True (locked) by default
        # Special cases for blocks 0 and 255, which will use a list of sector locks
        #self.block_locks = {block: True for block in range(1, 255)}
        #self.special_sector_locks = {'0': [True]*16, '255': [True]*16}  # Assuming 32 sectors per special block


    
        # Assuming memory size is 256 blocks * 64KB per block
        #self.blocks = 256
        self.block_locks = [True] * self.blocks  # False: unlocked, True: locked
        # Special handling for blocks 0 and 255 for sector-level locking
        self.special_sector_locks = {0: [True]*16, 255: [True]*16}

    

        self.protection_map_cmp_0 = {
            (0, 0, 0, 0, 0): [],  # No protection
            (0, 1, 0, 0, 0): [],  # No protection
            (1, 0, 0, 0, 0): [],  # No protection
            (1, 1, 0, 0, 0): [],  # No protection
            
            (0, 0, 0, 0, 1): [(0xFC0000, 0xFFFFFF)],  # Protect upper 1/64 of memory
            (0, 0, 0, 1, 0): [(0xF80000, 0xFFFFFF)],  # Protect upper 1/32 of memory
            (0, 0, 0, 1, 1): [(0xF00000, 0xFFFFFF)],  # Protect upper 1/16 of memory
            (0, 0, 1, 0, 0): [(0xE00000, 0xFFFFFF)],  # Protect upper 1/8 of memory
            (0, 0, 1, 0, 1): [(0xC00000, 0xFFFFFF)],  # Protect upper 1/4 of memory
            (0, 0, 1, 1, 0): [(0x800000, 0xFFFFFF)],  # Protect upper 1/2 of memory
            
            (0, 1, 0, 0, 1): [(0x000000, 0x03FFFF)],  # Protect lower 1/64 of memory
            (0, 1, 0, 1, 0): [(0x000000, 0x07FFFF)],  # Protect lower 1/32 of memory
            (0, 1, 0, 1, 1): [(0x000000, 0x0FFFFF)],  # Protect lower 1/16 of memory
            (0, 1, 1, 0, 0): [(0x000000, 0x1FFFFF)],  # Protect lower 1/8 of memory
            (0, 1, 1, 0, 1): [(0x000000, 0x3FFFFF)],  # Protect lower 1/4 of memory
            (0, 1, 1, 1, 0): [(0x000000, 0x7FFFFF)],  # Protect lower 1/2 of memory
            (0, 0, 1, 1, 1): [(0x000000, 0xFFFFFF)],  # All memory protected when SEC=1
            (0, 1, 1, 1, 1): [(0x000000, 0xFFFFFF)],  # All memory protected when SEC=1
            (1, 0, 1, 1, 1): [(0x000000, 0xFFFFFF)],  # All memory protected when SEC=1
            (1, 1, 1, 1, 1): [(0x000000, 0xFFFFFF)],  # All memory protected when SEC=1
        

            # Specific sector protections when SEC=1 and TB=0 (upper sectors)
            (1, 0, 0, 0, 1): [(0xFFF000, 0xFFFFF)],  # Protect the last 4KB of memory
            (1, 0, 0, 1, 0): [(0xFFE000, 0xFFFFF)],  # Protect the last 8KB of memory
            (1, 0, 0, 1, 1): [(0xFFC000, 0xFFFFF)],  # Protect the last 16KB of memory
            (1, 0, 1, 0, 0): [(0xFF8000, 0xFFFFF)],  # Protect the last 32KB of memory
            (1, 0, 1, 0, 1): [(0xFF8000, 0xFFFFF)],  # Protect the last 32KB of memory
            
            # Specific sector protections when SEC=1 and TB=1 (lower sectors)
            (1, 1, 0, 0, 1): [(0x000000, 0x000FFF)],  # Protect the first 4KB of memory
            (1, 1, 0, 1, 0): [(0x000000, 0x001FFF)],  # Protect the first 8KB of memory
            (1, 1, 0, 1, 1): [(0x000000, 0x003FFF)],  # Protect the first 16KB of memory
            (1, 1, 1, 0, 0): [(0x000000, 0x007FFF)],  # Protect the first 32KB of memory
            (1, 1, 1, 0, 1): [(0x000000, 0x007FFF)],  # Protect the first 32KB of memory
        }


        self.protection_map_cmp_1 = {
            (0, 0, 0, 0, 0): [(0x000000, 0xFFFFFF)],  # All memory
            (0, 1, 0, 0, 0): [(0x000000, 0xFFFFFF)],  # All memory
            (1, 0, 0, 0, 0): [(0x000000, 0xFFFFFF)],  # All memory
            (1, 1, 0, 0, 0): [(0x000000, 0xFFFFFF)],  # All memory

            (0, 0, 0, 0, 1): [(0x000000, 0xFBFFFF)],  # Lower 63/64
            (0, 0, 0, 1, 0): [(0x000000, 0xF7FFFF)],  # Lower 31/32
            (0, 0, 0, 1, 1): [(0x000000, 0xEFFFFF)],  # Lower 15/16
            (0, 0, 1, 0, 0): [(0x000000, 0xDFFFFF)],  # Lower 7/8
            (0, 0, 1, 0, 1): [(0x000000, 0xBFFFFF)],  # Lower 3/4
            (0, 0, 1, 1, 0): [(0x000000, 0x7FFFFF)],  # Lower 1/2

            (0, 1, 0, 0, 1): [(0x040000, 0xFFFFFF)],  # Upper 63/64
            (0, 1, 0, 1, 0): [(0x080000, 0xFFFFFF)],  # Upper 31/32
            (0, 1, 0, 1, 1): [(0x100000, 0xFFFFFF)],  # Upper 15/16
            (0, 1, 1, 0, 0): [(0x200000, 0xFFFFFF)],  # Upper 7/8
            (0, 1, 1, 0, 1): [(0x400000, 0xFFFFFF)],  # Upper 3/4
            (0, 1, 1, 1, 0): [(0x800000, 0xFFFFFF)],  # Upper 1/2

            (1, 0, 0, 0, 1): [(0x000000, 0xFFEFFF)],  # Lower, excluding the last 4KB
            (1, 0, 0, 1, 0): [(0x000000, 0xFFDFFF)],  # Lower, excluding the last 8KB
            (1, 0, 0, 1, 1): [(0x000000, 0xFFBFFF)],  # Lower, excluding the last 16KB
            (1, 0, 1, 0, 0): [(0x000000, 0xFF7FFF)],  # Lower, excluding the last 32KB
            (1, 0, 1, 0, 1): [(0x000000, 0xFF7FFF)],  # Lower, excluding the last 32KB

            (1, 1, 0, 0, 1): [(0x001000, 0xFFFFFF)],  # Upper, excluding the first 4KB
            (1, 1, 0, 1, 0): [(0x002000, 0xFFFFFF)],  # Upper, excluding the first 8KB
            (1, 1, 0, 1, 1): [(0x004000, 0xFFFFFF)],  # Upper, excluding the first 16KB
            (1, 1, 1, 0, 0): [(0x008000, 0xFFFFFF)],  # Upper, excluding the first 32KB
            (1, 1, 1, 0, 1): [(0x008000, 0xFFFFFF)],  # Upper, excluding the first 32KB
            # No protection when all BP bits are set and CMP = 1
            (0, 0, 1, 1, 1): [],  # No protection regardless of SEC and TB when BP=1, 1, 1
            (0, 1, 1, 1, 1): [],  # No protection for any combination of SEC and TB
            (1, 0, 1, 1, 1): [],  # No protection, showing explicitly that SEC and TB states don't matter
            (1, 1, 1, 1, 1): [],  # No memory is protected when all BP bits are set, regardless of SEC and TB
        }

        # Dynamically select which protection map to use based on the CMP bit
        self.current_protection_map = self.protection_map_cmp_0  # Default selection

        self.reset_enalbed = False
        self.write_enable_volatile = False
        self.power_status = True

        if DEBUG:
            print(self.registers)



    def clear_status_registers(self, register, mask=0b11111111):
        # Apply the mask using bitwise AND to clear the last two bits
        self.registers['Status Register 1'] &= mask

        return True


    def update_protection_map(self):
        # Extract the CMP bit from Status Register-2
        cmp_bit = (self.registers['Status Register 2'] >> 6) & 0x01

        # Select the appropriate protection map based on the CMP bit
        if cmp_bit == 0:
            self.current_protection_map = self.protection_map_cmp_0
        else:
            self.current_protection_map = self.protection_map_cmp_1

    def calculate_protected_ranges(self):
        # Ensure the current protection map is up to date
        self.update_protection_map()

        # Extract SEC, TB, BP2, BP1, and BP0 bits from Status Register-1
        sec = (self.registers['Status Register 1'] >> 6) & 0x01
        tb = (self.registers['Status Register 1'] >> 5) & 0x01
        bp = (self.registers['Status Register 1'] >> 2) & 0x07  # Combining BP2, BP1, BP0 into a single integer

        # Lookup the protected range based on the current bit settings
        key = (sec, tb, bp >> 2, (bp >> 1) & 0x01, bp & 0x01)
        protected_ranges = self.current_protection_map.get(key, [])
        if DEBUG:
            print('protection key:', key)
            print(protected_ranges)
            hex_ranges = [(hex(a), hex(b)) for a, b in protected_ranges]
            print(hex_ranges)


        return protected_ranges


    def update_protection_settings(self, sr1, sr2, sr3):
        """Update status register values to control memory protection."""
        self.registers['Status Register 1'] = sr1
        self.registers['Status Register 2'] = sr2
        self.registers['Status Register 3'] = sr3


    def individual_lock(self, instruction_code, data, *args, **kwargs):
        address = get_address(data)
        """Lock a block or a sector based on the address."""
        block_number, is_special_block, sector_index = self.decode_address(address)

        if is_special_block:
            self.special_sector_locks[block_number][sector_index] = True
            if DEBUG or INFO:
                print(f"Sector {sector_index} in special block {block_number} locked.")
        else:
            self.block_locks[block_number] = True
            if DEBUG or INFO:
                print(f"Block {block_number} locked.")

    def individual_unlock(self, instruction_code, data, *args, **kwargs):
        address = get_address(data)
        """Unlock a block or a sector based on the address."""
        block_number, is_special_block, sector_index = self.decode_address(address)

        if is_special_block:
            self.special_sector_locks[block_number][sector_index] = False
            if DEBUG or INFO:
                print(f"Sector {sector_index} in special block {block_number} unlocked.")
        else:
            self.block_locks[block_number] = False
            if DEBUG or INFO:
                print(f"Block {block_number} unlocked.")

    def decode_address(self, address):
        """Decode the address into block number, whether it's a special block, and sector index (if applicable)."""
        # Convert hexadecimal address to integer

        if isinstance(address, str):
            address = int(address, 16)
    

        block_number = address // self.block_size
        sector_index = (address % self.block_size) // self.sector_size

        is_special_block = block_number in [0, self.blocks - 1]
        if DEBUG or INFO2:
            print('block_number:', block_number)
            print('is_special_block:', is_special_block)
            print('sector_index:', sector_index)

        return block_number, is_special_block, sector_index




    def read_block_sector_lock(self, instruction_code, data, bytes_to_return, *args, **kwargs):
        address = get_address(data)

        """Read the lock status of a specific block or sector."""
        block_number, is_special_block, sector_index = self.decode_address(address)
        if is_special_block:
            lock_status = self.special_sector_locks[block_number][sector_index]
        else:
            lock_status = self.block_locks[block_number]
        print(lock_status)

        return [set_last_bit(lock_status)]*bytes_to_return

    def global_block_sector_lock(self, *args, **kwargs):

        """Lock all blocks and sectors."""
        if not self.is_write_enabled():
            if DEBUG or INFO:
                print("Error: global_block_sector_lock attempted without write enable.")
            return False

        # Lock all regular blocks
        for i in range(self.blocks):
            self.block_locks[i] = True

        # Lock all sectors in special blocks
        for block in self.special_sector_locks:
            self.special_sector_locks[block] = [True] * 16
        
        if DEBUG or INFO:
            print("All blocks and sectors locked.")

        self.write_disable()
        return True

    def global_block_sector_unlock(self, *args, **kwargs):
        """Unlock all blocks and sectors."""
        if not self.is_write_enabled():
            if DEBUG or INFO:
                print("Error: Erase operation attempted without write enable.")
            return False

        # Unlock all regular blocks
        for i in range(self.blocks):
            self.block_locks[i] = False

        # Unlock all sectors in special blocks
        for block in self.special_sector_locks:
            self.special_sector_locks[block] = [False] * 16
        if DEBUG or INFO:
            print("All blocks and sectors unlocked.")

        if DEBUG:
            print(self.block_locks)
            print(self.special_sector_locks)

        self.write_disable()
        return True


    def update_driver_strength_bits(self):
        """Update the current driver strength based on DRV1 and DRV0 bits in Status Register-3."""
        drv_bits = (self.registers['Status Register 3'] >> 5) & 0x03  # Extract bits 5 and 6
        drv_setting = f'{(drv_bits >> 1) & 1}{drv_bits & 1}'  # Convert to string '00', '01', '10', '11'
        self.current_driver_strength = self.driver_strength_settings.get(drv_setting, "Unknown")
        
        if DEBUG or INFO:
            print(f"Driver strength set to {self.current_driver_strength}.")

        return  self.current_driver_strength

    def set_driver_strength(self, drv1, drv0):
        """Set DRV1 and DRV0 bits in Status Register-3 and update driver strength."""
        # Clear previous DRV1 and DRV0 bits then set new values
        self.registers['Status Register 3'] &= ~(0x03 << 5)  # Clear DRV bits
        self.registers['Status Register 3'] |= ((drv1 << 1) | drv0) << 5  # Set new DRV bits
        driver_strength = self.update_driver_strength_bits()  # Update the current driver strength based on new DRV bits

        return driver_strength

    ## STATUS REGISTERS CONTROL 
    ## -----------------------------

    def write_enable_volatile_status_register():
        # Send the Write Enable for Volatile Status Register (50h) instruction
        self.write_enable_volatile = True
        return True

    def set_busy_bit(self):
        """Set the BUSY bit in Status Register 1 to indicate an operation is in progress."""
        self.registers['Status Register 1'] |= 0x01  # Assuming BUSY bit is bit 0
  
    def clear_busy_and_wel_bits(self):
        """Clear the BUSY and WEL bits in Status Register 1 after operation completion."""
        self.registers['Status Register 1'] &= ~0x03  # Clear both BUSY and WEL bits
    

    # INSTRUCTION: Read Status Register-1 (05h), Status Register-2 (35h) & Status Register-3 (15h)
    def read_status_register(self, instruction_code, *args, **kwargs):
        # Send the Read Status Register instruction based on the provided instruction code
        # Receive and return the 8-bit Status Register value
  
        instruction_register_mapping = {
            0x05: 'Status Register 1',
            0x35: 'Status Register 2',
            0x15: 'Status Register 3'
        }

        register_name = instruction_register_mapping[instruction_code]

        if register_name not in self.registers.keys():
            return False 

        register_value = self.registers[register_name]

        return [register_value]

    def set_status_register_bit(self, register_name, bit_position, value):
        """Set or clear a specific bit in a given status register."""
        if value:
            self.registers[register_name] |= (1 << bit_position)
        else:
            self.registers[register_name] &= ~(1 << bit_position)
    
    def get_status_register_bit(self, register_name, bit_position):
        """Get the value of a specific bit in a given status register."""
        return bool(self.registers[register_name] & (1 << bit_position))


    def is_write_enabled(self):
        """Check if write is enabled by examining the WEL bit in Status Register 1."""
        return (self.registers['Status Register 1'] & 0x02) == 0x02
    
    def write_enable(self, *args, **kwargs):
        """Sets the WEL bit in Status Register 1 if write operations are currently allowed."""
        if self.can_write_status_register():
            # Only set the WEL bit if the status register can currently be written to
            self.registers['Status Register 1'] |= 0x02  # Set WEL bit
            if DEBUG or INFO:
                print("Write enabled.")
        else:
            # Do not set the WEL bit if the status register cannot be written to due to protection settings
            if DEBUG or INFO:
                print("Write enable command ignored due to protection settings.")
        
    def write_disable(self, *args, **kwargs):
        """Clears the WEL bit in Status Register 1 to disable write operations."""
        self.registers['Status Register 1'] &= ~0x02  # Clear WEL bit
        if DEBUG or INFO:
            print("Write disabled.")



    def can_write_status_register(self):
        """Determine if the Status Register can be written to based on SRL, SRP, /WP, and WEL."""
        sr1 = self.registers['Status Register 1']
        sr2 = self.registers['Status Register 2']

        # Extract relevant bits
        wel = (sr1 >> 1) & 0x01  # Write Enable Latch
        srp = (sr1 >> 7) & 0x01  # Status Register Protect 0 (SRP0)
        srl = (sr2 >> 1) & 0x01  # Status Register Lock (SRL)
        
        if DEBUG:
            print(wel,srp,srl)
        if srl == 1:  # Power Supply Lock-Down or One Time Program
            # Status Register is locked regardless of other bits
            return False
        elif srp == 0:
            # Software Protection: /WP pin has no control, check WEL only
            return True
        else:
            # Hardware Protected/Unprotected based on /WP pin state
            if self.WP_pin:
                # /WP pin high, SRP=1, check WEL
                return True
            else:
                # /WP pin low, SRP=1, Status Register locked
                return False



    # INSTRUCTION: Write Status Register-1 (01h), Status Register-2 (31h) & Status Register-3 (11h)
   
    def write_status_register(self, instruction_code, data, volatile=False):
        
        value = data

        instruction_register_mapping = {
            0x01: 'Status Register 1',
            0x31: 'Status Register 2',
            0x11: 'Status Register 3'
        }
        register_name = instruction_register_mapping[instruction_code]
        """Attempt to update Status Register-1, checking protection mechanisms."""
        if not self.can_write_status_register():
            if DEBUG or INFO:
                print(f'Status Register-{register_name} update failed due to protection settings or write enable latch not set.')
            
            self.write_disable()
            return False

        """Write a value to a register, optionally as a volatile write."""
        if isinstance(value, list) and instruction_code == 0x01:
            if volatile:
                # Store the current value before changing it, for volatile writes only
                self.volatile_writes['Status Register 1'] = self.registers['Status Register 1']
                self.volatile_writes['Status Register 2'] = self.registers['Status Register 2']
        
            self.registers['Status Register 1'] = value[0]
            self.registers['Status Register 2'] = value[1]

            self.write_disable()
            return True

        if volatile:
            # Store the current value before changing it, for volatile writes only
            self.volatile_writes[register_name] = self.registers[register_name]
        
        #self.registers[register_name] = int(value, 16)
        self.registers[register_name] = value
        
        if DEBUG or INFO:
            print(f'Status Register-{register_name} updated successfully.')
    
        self.write_disable()
        return True


    def set_busy_flag(self):
        self.registers['Status Register 1'] |= 0x01  # Set BUSY flag

    def clear_busy_flag(self):
        self.registers['Status Register 1'] &= ~0x01  # Clear BUSY flag

    def is_suspended(self):
        """Check if an Erase/Program operation is currently suspended."""
        return (self.registers['Status Register 2'] & 0x80) != 0

    def is_busy(self):
        """Check if the device is busy (BUSY=1)."""
        return bool(self.registers['Status Register 1'] & 0x01)  # Assuming BUSY bit is bit 0 in SR1

    # COMMAND
    def erase_program_suspend(self):
        """Simulate the Erase/Program Suspend (75h) instruction."""
        # Check if BUSY is set and SUS is not set
        if (self.registers['Status Register 1'] & 0x01) and not (self.registers['Status Register 2'] & 0x80):
            self.registers['Status Register 2'] |= 0x80  # Set SUS bit in Status Register-2
            self.registers['Status Register 1'] &= ~0x01  # Clear BUSY bit to simulate operation suspend
            if DEBUG or INFO:
                print("Erase/Program operation suspended.")
        else:
            if DEBUG or INFO:
                print("Suspend instruction ignored due to inappropriate conditions.")

    # COMMAND
    def erase_program_resume(self):
        """Simulate the Erase/Program Resume (7Ah) instruction."""
        if self.registers['Status Register 2'] & 0x80:  # Check if SUS bit is set
            self.registers['Status Register 2'] &= ~0x80  # Clear SUS bit
            self.registers['Status Register 1'] |= 0x01  # Optionally, set BUSY bit if resuming operation
            if DEBUG or INFO:
                print("Erase/Program operation resumed.")
        else:
            if DEBUG or INFO:
                print("Resume instruction ignored because no suspend state is active.")

    def power_cycle(self):
        """Simulate a power cycle affecting the device."""
        # Clear both SUS and BUSY bits
        self.registers['Status Register 2'] &= ~0x80  # Clear SUS bit
        self.registers['Status Register 1'] &= ~0x01  # Clear BUSY bit
        if DEBUG or INFO:
            print("Device power cycled. SUS and BUSY bits cleared.")

    # INSTRUCTION: Power-down (B9h)
    def power_down(self, *args, **kwargs):
        self.power_status = not self.power_status
        return []

    def read_manufacturer_device_id(self, instruction_code, data, *args, **kwargs):
        
        if len(data) >= 3:        
            return self.device_id

        return []


    # INSTRUCTION: Release Power-down / Device ID (ABh)
    def release_power_down(self, instruction_code, data, *args, **kwargs):
        self.power_status = not self.power_status
        
        if len(data) >= 3:
            
            return self.device_id

        return []

    ## =============================
    ## =============================

    '''
    def calculate_protected_blocks(self, bp, tb, cmp):
        """Calculate which blocks are protected based on BP, TB, and CMP bits."""
        # Placeholder for logic to calculate protected block ranges based on BP, TB, CMP
        # This method should return a list or set of block numbers that are considered protected.
        # The actual calculation will depend on the specific definitions of BP ranges and TB behavior.
        protected_blocks = set()
        # Example logic (simplified and needs to be adjusted to actual chip specifications):
        range_start, range_end = 0, 256  # Default full range, adjust based on BP, TB, CMP
        if tb:
            range_end = 128  # Example adjustment for TB bit
        else:
            range_start = 128
        if cmp:
            range_start, range_end = range_end, range_start  # Invert range for CMP bit
        
        for block in range(range_start, range_end):
            protected_blocks.add(block)
        
        return protected_blocks

    '''
    # ISSUES 

    def is_memory_protected(self, address):
        """Determine if the memory at a given address is write-protected."""
        block_number, is_special_block, sector_index = self.decode_address(address)
        
        if isinstance(address, str):
            address = int(address, 16)
        # Extract relevant bits from status registers
        wps = (self.registers['Status Register 3'] >> 2) & 0x01  # WPS bit
        sec = (self.registers['Status Register 1'] >> 6) & 0x01  # SEC bit
        tb = (self.registers['Status Register 1'] >> 5) & 0x01   # TB bit
        bp = (self.registers['Status Register 1'] >> 2) & 0x07   # BP bits
        cmp = (self.registers['Status Register 2'] >> 6) & 0x01  # CMP bit

        if DEBUG:
            print("REGISTER BITS")
            print('wps:', wps)
            print('sec:', sec)
            print('tb:', tb)
            print('bp:', bp)
            print('cmp:', cmp)

        if wps:
            # Individual Block Locks mechanism
            if is_special_block:
                # Check if the sector within the special block is locked
                return self.special_sector_locks[block_number][sector_index]
            else:
                # Check if the entire block is locked
                return self.block_locks[block_number]
        else:
            # Global protection settings apply
            #if not sec:
            #    # If sector protection is not enabled, the memory is not write-protected by BP, TB, CMP.
            #    return False
            
            protected_blocks = self.calculate_protected_ranges()
         
            if len(protected_blocks) > 1:
                lower_limit = protected_blocks[0][0]
                upper_limit = protected_blocks[0][1]
                
                if lower_limit <= address <= upper_limit:

                    return True

            return False

    ## CUSTOM WRAPPERS
    ## -----------------------------
    '''
    def execute_command(self, hex_code, *args):
        """Execute a command based on its hex code, considering SUS and BUSY bits."""
        busy = self.registers['Status Register 1'] & 0x01  # BUSY bit in Status Register 1
        sus = (self.registers['Status Register 2'] & 0x80) >> 7  # Simulate SUS bit as the first bit of Status Register 2

        #if hex_code == '75' and not sus and busy:  # Suspend command
        #    self.suspend_operation()
        #elif hex_code == '7A' and sus and not busy:  # Resume command
        #    self.resume_operation()
        #elif sus:  # Check if operation is suspended and restrict certain commands
        #    print("Operation suspended. Certain commands are restricted.")
        #    return False
        #else:
        


        # If not handling a suspend/resume command, delegate to specific command implementations
        return self.execute_command(hex_code, *args)

    '''

    def generate_delay_function(self, typical, minimum, maximum, typical_probability=0.9):
        """Generates a function to produce a delay, typically the typical value, otherwise random between min and max."""
        def delay_function():
            if random.random() < typical_probability:  # With typical_probability, choose the typical value
                return typical
            else:  # Otherwise, choose a random value between min and max, excluding the typical value
                # Ensure the random value is not equal to the typical value
                while True:
                    value = random.uniform(minimum, maximum)
                    if value != typical:
                        return value
        return delay_function


    def simulate_dummy_clocks(self):
        """Simulate the effect of eight dummy clock cycles."""
        # In a real implementation, this might adjust timing or setup. Here, it's a placeholder.
        pass

    ## =============================
    ## =============================



    def update_protection_settings(self, bp_bits_value, tb_value, sec_value, cmp_value):
        """Update block protection settings in Status Register 1."""
        # Set BP bits (assuming BP2, BP1, BP0 are bits 4, 3, 2 respectively in Status Register 1)
        for i, bit_value in enumerate([bp_bits_value >> 2 & 1, bp_bits_value >> 1 & 1, bp_bits_value & 1]):
            self.set_status_register_bit('Status Register 1', 2 + i, bit_value)
        
        # Set TB, SEC, and CMP bits (assuming specific bit positions)
        self.set_status_register_bit('Status Register 1', 5, tb_value)  # TB bit
        self.set_status_register_bit('Status Register 1', 6, sec_value)  # SEC bit
        self.set_status_register_bit('Status Register 1', 7, cmp_value)  # CMP bit
        
        if DEBUG or INFO:
            print("Protection settings updated.")


    def is_operation_allowed(self, address):
        """Check if write/erase operation is allowed at the given address based on protection settings."""
        # Simplified; actual implementation should calculate based on BP, TB, SEC, CMP
        # Here's a placeholder for the logic
        if self.get_status_register_bit('Status Register 1', 7):  # Assuming CMP bit as an example
            if DEBUG or INFO:
                print("Operation not allowed due to protection settings.")
            return False
        return True  # Placeholder, should return False based on actual protection logic


    ## READ COMMANDS 
    ## -----------------------------

    '''
    JEDEC ID (0x9F):
    dummy 0: ef 40 18
    dummy 1: 40 18 00
    dummy 2: 18 00 00
    dummy 3: 00 00 00
    dummy 4: 00 00 00
    dummy 5: 00 00 00
    dummy 6: 00 00 00
    dummy 7: 00 00 00
    dummy 8: 00 00 00
    dummy 9: 00 00 00
    '''
    def read_jedec_id(self, instruction_code, data, bytes_to_return, *args, **kwargs):
        print(instruction_code)
        """Returns the JEDEC ID of the flash memory."""
        return self.jedec_id

    def read_sfdp_register(self, instruction_code, data, bytes_to_return, *args, **kwargs):
        """Simulates reading the SFDP register, returning basic flash parameters."""
        # For simplicity, return the SFDP header and basic flash parameters
        #sfdp = self.sfdp_data['header'] + self.sfdp_data['parameters']['basic_flash_parameters']
        address = get_address(data[:3])

        sfdp = self.sfdp_register
        return sfdp[address:address+bytes_to_return]

    def read(self, instruction_code, data, bytes_to_return):
        address = get_address(data)
        print('address', address)
        """Simulate a read operation showing the effect of driver strength."""
        # Simulated impact of driver strength on read operations
        if DEBUG or INFO:
            print(f"Reading data with {self.current_driver_strength} driver strength.")
        

        return self.memory[address:address+bytes_to_return]
    
    '''
    DEVICE UNIQUE ID (0x4B):
    dummy 0: ff ff ff ff d2 66 b4 21
    dummy 1: ff ff ff d2 66 b4 21 83
    dummy 2: ff ff d2 66 b4 21 83 51
    dummy 3: ff d2 66 b4 21 83 51 30
    dummy 4: d2 66 b4 21 83 51 30 2c
    dummy 5: 66 b4 21 83 51 30 2c d2
    dummy 6: b4 21 83 51 30 2c d2 66
    dummy 7: 21 83 51 30 2c d2 66 b4
    dummy 8: 83 51 30 2c d2 66 b4 21
    dummy 9: 51 30 2c d2 66 b4 21 83
    '''

    def read_unique_device_id(self, instruction_code, data, *args, **kwargs):
        """Returns the Unique Device ID of the flash memory."""
        return self.unique_device_id


    '''def read_status_register(self):
        """Returns the current value of the status register."""
        return self.status_register
    '''


    ## =============================
    ## =============================
  

    ## PAGE PROGRAM COMMANDS 
    ## -----------------------------


    def page_program(self, instruction_code, data, *args, **kwargs):
        
        address_size = 3
        
        address = get_address(data)
        data = data[address_size:]

        """Simulates the Page Program operation, allowing programming only on erased (0xFF) locations."""
        if not self.is_write_enabled():
            if DEBUG or INFO:
                print("Error: Write operation attempted without write enable.")
            return False

        # Ensure the address is within the flash memory bounds
        if address >= self.capacity_bytes:
            if DEBUG or INFO:
                print("Error: Address is out of bounds.")
            return False

        if self.is_memory_protected(address):
            if DEBUG or INFO:
                print("Error: Attempt to write to a protected memory region.")
            return False

        self.set_busy_flag()

        # Calculate page start and end to ensure we don't cross page boundaries
        page_start_address = address & ~(self.page_size - 1)  # Align to start of the page
        page_end_address = page_start_address + self.page_size

        if address + len(data) > page_end_address:
            if DEBUG or INFO:
                print("Warning: Data exceeds current page boundary" ) #. Operation adjusted to fit the page.")
            
            ## Adjust data to fit into the page without wrapping
            #data = data[:page_end_address - address]

        # Perform the Page Program operation 
        for i in range(len(data)):
            #current_address = address + i

            current_address = page_start_address + ((address - page_start_address + i) % self.page_size)

            #print('CURRENT ADDRESS:', hex(current_address), len(data))

            # Check if the current location is erased (0xFF)
            #if self.memory[current_address] != 0xFF:
            #    if DEBUG or INFO:
            #        print(f"Error: Memory location {current_address} contains data. Cannot overwrite without erase.")
            #    self.clear_busy_flag()
            #    self.write_disable()
            #    return False

            if not self.operation_suspended:
                # Program the data since the location is erased
                self.memory[current_address] &= data[i]





        # Automatically disable write enable (WEL) after the operation
        self.clear_busy_flag()
        self.write_disable()
        if DEBUG or INFO:
            print(f"Page programmed successfully at address {address}.")
        return True


    ## =============================
    ## =============================
  
  
  
    ## ERASE COMMANDS 
    ## -----------------------------

   
    def erase_sector(self, instruction_code, data, *args, **kwargs):
        """Erase a sector with write protection check."""

        sector_address = get_address(data[:3]) 
        print(data[:3])
        print(sector_address)
        sector_address &= 0xfff000
        print(sector_address)

        if not self.is_write_enabled():
            if DEBUG or INFO:
                print("Error: Erase operation attempted without write enable.")
            return []

        if self.is_memory_protected(sector_address):
            if DEBUG or INFO:
                print("Error: Attempt to erase a protected sector.")
            return []


        start_address = sector_address
        end_address = start_address + self.sector_size
        
        print(start_address)
        print(end_address)

        for i in range(start_address, end_address):

            if self.realistic_speed:
                delay_time = self.sector_erase_delay()/self.sector_size
                time.sleep(delay_time)

            self.memory[i] = 0xFF

        self.write_disable()
     
        return []
    
    def erase_block(self, block_number):
        """Erase a block with write protection check."""

        if not self.is_write_enabled():
            if DEBUG or INFO:
                print("Error: Erase operation attempted without write enable.")
            return []

       
        block_start_address = block_number * self.block_size

        if self.is_memory_protected(block_start_address):
            if DEBUG or INFO:
                print(f"Error: Attempt to erase a protected block {block_number}.")
            return []


        start_address = block_number * self.sector_size * self.sectors_per_block
        end_address = start_address + (self.sector_size * self.sectors_per_block)
        for i in range(start_address, end_address):
            self.memory[i] = 0xFF
        self.write_disable()
        return []


    def is_any_protected_invididual(self):
        # Check block locks

        if any(self.block_locks):
            return True
        
        # Check sector locks
        #print( self.special_sector_locks.values())
        for sectors in self.special_sector_locks.values():
            if any(sectors):
                return True
        
        # If no blocks or sectors are protected
        return False
    
    def chip_erase(self, *args):
        if not self.is_write_enabled():
            if DEBUG or INFO:
                print("Error: Erase operation attempted without write enable.")
            return False

        wps = (self.registers['Status Register 3'] >> 2) & 0x01  # WPS bit

        if wps:

            if self.is_any_protected_invididual():
                if DEBUG or INFO:
                    print("Error: Attempt to chip erase with protected area present.")
                return False
           
        else:

            # Check if any block of the memory is protected
            for block_number in range(self.capacity_bytes // self.block_size):  # Assuming 64KB blocks
                block_start_address = block_number * 0x10000
                #print(block_start_address)
                if self.is_memory_protected(block_start_address):
                    if DEBUG or INFO:
                        print("Error: Attempt to chip erase with protected block present.")
                    return False

            # Check if any sector of the memory is protected
            for sector_number in range(self.capacity_bytes // self.sector_size):  # Assuming 64KB blocks
                sector_start_address = sector_number * 0x10000
                if self.is_memory_protected(sector_start_address):
                    if DEBUG or INFO:
                        print("Error: Attempt to chip erase with protected sector  present.")
                    return False


        for i in (range(len(self.memory))):
            if self.realistic_speed:
                delay_time = self.chip_erase_delay()/self.capacity_bytes
                time.sleep(delay_time)
            self.memory[i] = 0xFF
        self.write_disable()
        
        return True

    ## =============================
    ## =============================
  

    ## SECURITY REGISTERS 
    ## -----------------------------


    def is_security_register_locked(self, register_number):
        """Check if a specific security register is locked."""
        if register_number < 0 or register_number > 2:
            if DEBUG or INFO:
                print("Invalid security register number.")
            return True  # Treat invalid register numbers as locked for safety.
        
        lock_bit = 1 << (5 - register_number)  # Calculate the lock bit based on the register number
        return bool(self.registers['Status Register 2'] & lock_bit)


    def program_security_register(self, instruction_code, data, bytes_to_return, *args, **kwargs):
        """Program data to a security register based on a 24-bit address."""
        address = get_address(data[:3])
        data = data[3:]

        if not self.is_write_enabled():
            if DEBUG or INFO:
                print("Error: Write Enable Latch (WEL) is not set.")
            return False

        # Decode the register number and byte address from the 24-bit address
        register_number = (address & 0x000F000) >> 12  # Extract A15-12 for the register number
        # Adjust register_number to match 0-indexed security_registers list
        register_number -= 1

        byte_address = address & 0x00000FF  # Extract A7-0 for the byte address
        
        

        # Validate register number and address
        if not (0 <= register_number < len(self.security_registers)):
            if DEBUG or INFO:
                print(f"Error: Invalid register address {hex(address)}.")
            return False

        if not (0 <= byte_address < 256):
            if DEBUG or INFO:
                print(f"Error: Invalid byte address {hex(byte_address)} in security register.")
            return False

        # Check if the data is being programmed to previously erased (FFh) locations
        reg_data = self.security_registers[register_number]

        if any(byte != 0xFF for byte in reg_data[byte_address:byte_address+len(data)]):
            if DEBUG or INFO:
                print("Error: Security register location must be previously erased.")
            return False
        
        # Program the data
        for i in range(len(data)):
            # +1 to simulate unwritabel first byte as seen in real mem
         
            reg_address = (byte_address+i) %256
            if reg_address == 0:
                reg_address += 1
            reg_data[reg_address] &= data[i]

        if bytes_to_return:
            for i in range(bytes_to_return):
                reg_data[byte_address+1+(len(data)+i)] &= 0x00


        if DEBUG or INFO:
            print(f"Security Register {register_number+1} programmed successfully at address {hex(byte_address)}.")
        
        # Clear WEL after the operation
        self.write_disable()

        return True

    def erase_security_register(self, instruction_code, data, *args, **kwargs):
        address = get_address(data[:3])
        """Erase a security register based on a 24-bit address."""
        if not self.is_write_enabled():
            if DEBUG or INFO:
                print("Error: Write Enable Latch (WEL) is not set. Erase operation not executed.")
            return False

        # Decode the register number from the 24-bit address
        register_number = (address & 0x000F000) >> 12  # Extract A15-12
        register_number -= 1  # Adjust for 0-based indexing

        if not (0 <= register_number < len(self.security_registers)):
            if DEBUG or INFO:
                print(f"Error: Invalid address {hex(address)} for erasing security register.")
            return False

        if self.is_security_register_locked(register_number):
            if DEBUG or INFO:
                print(f"Error: Security Register {register_number} is locked. Erase operation not executed.")
            return False

        # Simulate /CS pin being driven high and the start of the erase operation
        #print("Starting Erase Security Register operation...")
        #self.set_busy_bit()
        
        # Simulate the self-timed erase operation (tSE) with a sleep. In real hardware, this would be the time the operation takes.
        #time.sleep(self.tSE)  # Assume tSE is defined elsewhere in your class
        

        # Erase the security register by setting all its bytes to 0xFF
        self.security_registers[register_number] = [0xFF] * 256
        if DEBUG or INFO:
            print(f"Security Register {register_number + 1} erased.")

        # Clear WEL after the operation
        self.write_disable()


    def read_security_register(self, instruction_code, data, bytes_to_return, *args, **kwargs):
        """Read a specified number of bytes from a security register based on a 24-bit address."""
        address = get_address(data[:3])
        
    

        number_of_bytes = bytes_to_return
    
        if self.is_busy():
            if DEBUG or INFO:
                print("Device is busy. Read Security Register instruction ignored.")
            return None

        register_number = self.decode_register_number_from_address(address)
        

        if register_number is None:
            if DEBUG or INFO:
                print(f"Error: Invalid address {hex(address)} for reading security register.")
            return None

        # Simulate dummy clocks
        #self.simulate_dummy_clocks()

        # Starting byte address within the security register
        byte_address = address & 0xFF  # Last 8 bits of the address

        # Ensure the number of bytes to read does not exceed the size of the security register
        max_bytes = min(number_of_bytes, 256 - byte_address)
        
        data_out = self.security_registers[register_number][byte_address:byte_address + max_bytes]
    
        return data_out


    def decode_register_number_from_address(self, address):
        """Decode the security register number from a 24-bit address."""
        register_bits = (address >> 12) & 0x07  # Extract bits 12 to 14 as register identifier
        if register_bits in (1, 2, 3):  # Valid register identifiers
            return register_bits - 1  # Adjust to 0-indexed register number
        return None

    def lock_security_register(self, register_number):
        """Lock a specific security register."""
        
        register_number -= 1

        if register_number < 0 or register_number > 2:
            if DEBUG or INFO:
                print("Invalid security register number.")
            return
        
        # Corrected to directly map register_number to bit positions
        bit_position = 5 - register_number  # Directly gives 3 for LB1, 4 for LB2, and 5 for LB3
        self.registers['Status Register 2'] |= 1 << bit_position
        if DEBUG or INFO:
            print(f"Security Register {register_number} locked.")


    ## =============================
    ## =============================
  
    def get_memory_address(block_number=None, sector_number=None):
        block_size = 64 * 1024  # Assuming each block size is 64 KB
        sector_size = 4 * 1024   # Assuming each sector size is 4 KB
        base_address = 0x000000   # Assuming the base address of the memory
        
        if block_number is not None and sector_number is not None:
            # Calculate address based on both block and sector numbers
            address = base_address + (block_number * block_size) + (sector_number * sector_size)
        elif block_number is not None:
            # Calculate address based on block number only
            address = base_address + (block_number * block_size)
        elif sector_number is not None:
            # Calculate address based on sector number only
            address = base_address + (sector_number * sector_size)
        else:
            raise ValueError("At least one of block_number or sector_number must be provided.")
        
        return hex(address)


    # NEEDS UPDATE:
    # =============
    # =============

    def enable_reset(self):
        self.reset_enalbed = True

    def disable_reset(self):
        self.reset_enalbed = False


    def software_reset(self):
        """Simulates a software reset of the flash memory device."""
        """Simulate a software reset, reverting volatile writes."""
        # Reset internal state, except the memory content and unique IDs
        if not self.reset_enalbed:
            return False


        for register, volatile_value in self.volatile_writes.items():
            if volatile_value is not None:  # If there was a volatile write
                self.registers[register] = volatile_value  # Revert to the saved value
                self.volatile_writes[register] = None  # Clear the volatile write record

        self.write_disable()  # Reset write enable state
        #self.clear_status_registers('Status Register 1', 0b11111100)
        #self.clear_status_registers('Status Register 2', 0b00000000)
        #self.clear_status_registers('Status Register 3', 0b00000000)

        if DEBUG or INFO:
            print("Flash memory has been reset.")

        return True

    # Based on command handle data? or use args?
    


    # TBD: disect packet on each command to make execute instruction more generic?

    def execute_instruction(self, packet, bytes_to_return=0, *args, **kwargs):
        """Execute the function corresponding to the given instruction byte, passing any additional arguments."""
        instruction_code = packet[0]
        data = packet[1:]
        
        #print('PACKET:', packet)
        #print('bytes_to_return', bytes_to_return)
        
        if instruction_code in self.instruction_map:

            if not self.power_status and instruction_code != 0xAB: #.release_power_down,
                print('[!] Device in power down!')
                return []

            instruction = self.instruction_map[instruction_code]
            
           
            instruction_details = instruction_info[instruction_code]
            instruction_name = instruction_details['method']
            instruction_depedencies = instruction_details['dependencies']

            busy_block = instruction_details['busy_block']
            set_busy = instruction_details['busy_lock']

            if self.is_busy() and busy_block:
                print('[!] BUSY == 1. Instruction will be ignored')
                return []

            instruction = getattr(self, instruction_name)
            if INFO2:
                print(f'[+] Intstruction found: {instruction_code} {instruction.__name__}')

            if isinstance(instruction_depedencies, list):
                if 'write_enable' in instruction_depedencies:
                   
                    if not self.is_write_enabled():
                        print("[!] Error: Write Enable Latch (WEL) is not set.")
                        if set_busy:
                            self.clear_busy_and_wel_bits()

                        return []

            if INFO2:
                print(f'[+] Executing intstruction: {instruction_code} {instruction.__name__}')

            if set_busy:
              self.set_busy_bit()

            if len(packet) == 2:
                data = packet[1]
            else:
                data = packet[1:]

            returned_data = instruction(instruction_code, data, bytes_to_return)

            if isinstance(instruction_depedencies, list):
                if 'write_enable' in instruction_depedencies:
                    self.write_disable()  

            #dummy_bytes = instruction_details['dummy_bytes']

            #data_min = instruction_details['data_min']
            #data_max = instruction_details['data_max']
            #data_in = instruction_details['data_in']
            #data_out = instruction_details['data_out']


            
            #if data_out:
            #    returned_data = instruction(instruction_code, data, bytes_to_return)
            #else:
            #    returned_data = instruction(instruction_code, data)

            #returned_data = instruction(instruction_code, data)

            '''if len(packet) > 1:
                if len(packet) == 2:
                    data = packet[1]
                else:
                    data = packet[1:]
                returned_data = instruction(instruction_code, data)
            else:
                returned_data = instruction(instruction_code, data)'''


        else:
            print("Unknown instruction:", instruction_code)
 
        if returned_data is None or isinstance(returned_data, bool):
            if set_busy:
                self.clear_busy_and_wel_bits()

            return []
        returned_data_size = len(returned_data) 
        print(returned_data_size, bytes_to_return)
        if returned_data_size <= bytes_to_return:

            response_data = returned_data + [0xFF]*(bytes_to_return- returned_data_size)
        else: 
            response_data = returned_data[:bytes_to_return]

        if set_busy:
            self.clear_busy_and_wel_bits()

        return response_data