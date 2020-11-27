# Handling relays automatically.
# Send several txs from eth to near, then from near to eth back.
# If `no_txs_in_same_block`, it's expected there are no txs that included into same block.

import sys, time

if len(sys.argv) < 3:
    print("python end2end.py <eth2near_tx_number> <near2eth_tx_number> [...]")
    exit(1)

no_txs_in_same_block = False
if 'no_txs_in_same_block' in sys.argv:
    no_txs_in_same_block = True

no_txs_in_parallel = False
if 'no_txs_in_parallel' in sys.argv:
    no_txs_in_parallel = True

assert not (no_txs_in_same_block and no_txs_in_parallel) # to avoid errors

eth2near_tx_number = int(sys.argv[1])
near2eth_tx_number = int(sys.argv[2])
assert eth2near_tx_number > 0 and eth2near_tx_number <= 1000 or eth2near_tx_number == 0 and near2eth_tx_number == 0
assert near2eth_tx_number >= 0 and near2eth_tx_number <= 1000

sys.path.append('lib')

from cluster import start_cluster, start_bridge
from bridge import alice

# TODO !! remove
from bridge import bridge_master_account
alice.eth_secret_key = bridge_master_account.eth_secret_key
print(alice)

nodes = start_cluster(2, 0, 1, None, [], {})

time.sleep(2)

(bridge, ganache) = start_bridge()
print('=== BRIDGE IS STARTED')

eth_address = bridge.get_eth_address_by_secret_key(alice.eth_secret_key)
print('=== ADDRESS of %s is %s' % (alice.name, eth_address))
eth_balance_before = bridge.get_eth_balance(eth_address)
print('=== ETH BALANCE BEFORE', eth_balance_before)
near_balance_before = bridge.get_near_balance(nodes[0], alice.near_account)
print('=== NEAR BALANCE BEFORE', near_balance_before)
print('=== SENDING 1000 ETH TO NEAR PER TX, %d TXS' % (eth2near_tx_number))
txs = []
for _ in range(eth2near_tx_number):
    txs.append(bridge.transfer_eth2near(alice.eth_secret_key,
                         alice.near_account,
                         1000))
    if no_txs_in_same_block:
        time.sleep(bridge.config['ganache_block_prod_time'] + 2)
    if no_txs_in_parallel:
        [p.wait() for p in txs]
exit_codes = [p.wait() for p in txs]

eth_balance_after = bridge.get_eth_balance(eth_address)
print('=== ETH BALANCE AFTER', eth_balance_after)
near_balance_after = bridge.get_near_balance(nodes[0], alice.near_account)
print('=== NEAR BALANCE AFTER', near_balance_after)
assert eth_balance_after + 1000 * eth2near_tx_number == eth_balance_before
assert near_balance_before + 1000 * eth2near_tx_number == near_balance_after

eth_balance_before = bridge.get_eth_balance(eth_address)
print('=== ETH BALANCE BEFORE', eth_balance_before)
near_balance_before = bridge.get_near_balance(nodes[0], alice.near_account)
print('=== NEAR BALANCE BEFORE', near_balance_before)
print('=== SENDING 1 NEAR TO ETH PER TX, %d TXS' % (near2eth_tx_number))
txs = []
for _ in range(near2eth_tx_number):
    txs.append(bridge.transfer_near2eth(alice.near_account, eth_address, 1))
    if no_txs_in_same_block:
        time.sleep(2.6) # default min_block_production_delay = 0.6
    if no_txs_in_parallel:
        [p.wait() for p in txs]
exit_codes = [p.wait() for p in txs]

eth_balance_after = bridge.get_eth_balance(eth_address)
print('=== ETH BALANCE AFTER', eth_balance_after)
near_balance_after = bridge.get_near_balance(nodes[0], alice.near_account)
print('=== NEAR BALANCE AFTER', near_balance_after)
assert eth_balance_before + 1 * near2eth_tx_number == eth_balance_after
assert near_balance_after + 1 * near2eth_tx_number == near_balance_before

print('EPIC')
