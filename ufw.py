import time
import torch
import argparse
import bittensor as bt
import subprocess
from typing import List, Dict, Set


NETUID_LIST = [10]

# Function to resynchronize with the Bittensor metagraph
def resync_metagraph(netuids: List[int]) -> Dict[int, List['bt.NeuronInfoLite']]:
    bt.logging.info("resync_metagraph()")

    new_neurons = {}
    for netuid in netuids:
        new_neurons[netuid] = subtensor.neurons_lite(netuid=netuid)
    
    bt.logging.info("Metagraph synced!")

    return new_neurons

# Function to get the IPs of any neurons that have vpermit = True
def neurons_to_ips(all_neurons: Dict[int, List['bt.NeuronInfoLite']]) -> Set[str]:
    bt.logging.info("neurons_to_ips()")

    validator_ips = set()
    for _, subnet_neurons in all_neurons.items():
        ips = [neuron.axon_info.ip for neuron in subnet_neurons if neuron.validator_permit and neuron.axon_info.ip!='0.0.0.0']
        validator_ips.update(set(ips))
        print("======= validator with zero ips =======")
        print([(neuron.uid, neuron.hotkey) for neuron in subnet_neurons if neuron.validator_permit and neuron.axon_info.ip=='0.0.0.0'])
    
    return validator_ips

# Function to whitelist IPs in UFW (Uncomplicated Firewall)
def whitelist_ips_in_ufw(ips: List[str]):
    # Disable UFW
    stop_cmd = "sudo ufw disable"
    # Reset UFW
    reset_cmd = "echo y | sudo ufw reset"
    # Default policy to deny
    deny_cmd = "sudo ufw default deny incoming"
    
    subprocess.run(stop_cmd, shell=True)
    subprocess.run(reset_cmd, shell=True)
    subprocess.run(deny_cmd, shell=True)
    
    # Allow SSH connections
    ssh_cmd = "sudo ufw allow ssh"
    subprocess.run(ssh_cmd, shell=True)
    
    # Whitelist the provided IPs for TCP connections
    for ip in ips:
        cmd = f"sudo ufw allow proto tcp from {ip}"
        subprocess.run(cmd, shell=True)
        bt.logging.info(f"Whitelisted IP {ip} for bittensor")
    
    # Enable UFW
    start_cmd = "echo y | sudo ufw enable"
    subprocess.run(start_cmd, shell=True)

# Function to parse command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="Run firewall")
    parser.add_argument('--subtensor.chain_endpoint', dest='chain_endpoint', help='Subtensor node', type=str, required=False, default=None)
    
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    # Connect to Bittensor network
    subtensor: 'bt.subtensor'
    if args.chain_endpoint:
        subtensor = bt.subtensor(network="finney", chain_endpoint=args.chain_endpoint)
    else:
        subtensor = bt.subtensor(network="finney")

    # Resync the metagraph
    neurons_dict = resync_metagraph(netuids = NETUID_LIST)

    # Get the IPs of any neurons that have vpermit = True
    ips = neurons_to_ips(neurons_dict)
    
    print("======= validator non-zero ips ========")
    print(ips)
    
    # Transform the IPs to a specific format
    # ips = [ip.split(".")[0] + "." + ip.split(".")[1] + ".0.0" for ip in ips]
    
    # Whitelist the IPs in UFW
    whitelist_ips_in_ufw(ips)
