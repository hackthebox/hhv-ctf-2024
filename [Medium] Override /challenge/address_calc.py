import copy

def get_log_addresses():
    # Starting address for the logs
    address = [0x00, 0x00, 0x00]
    # Define the increment step (12 bytes per log entry)
    increment_step = 16
    # Total number of logs
    total_logs = 160

    log_addresses = []
    

    # Calculate the increments
    for _ in range(total_logs):
        log_addresses.append(copy.deepcopy(address))
        # Increment the address by 12 bytes
        total_increment = (address[2] + increment_step)  # Calculate the total increment for the least significant byte
        address[2] = total_increment % 256  # Update the least significant byte
        
        # Carry over if needed
        carry_over = total_increment // 256
        if carry_over:
            address[1] += carry_over
            address[1], carry_over = address[1] % 256, address[1] // 256
        
        if carry_over:
            address[0] += carry_over
            # Assuming we don't exceed the addressable range for simplicity, no further carry-over handling
        #print(address)
        

    return log_addresses