import qlmdb3
import binascii
import json
from pyblake2 import blake2b
import ed25519_blake2b
import os
import sys

keydata = bytes.fromhex('34F0A37AAD20F4A260F0A5B3CB3D7FB50673212263E58A380BC10474BB039CE4')
genesis_pub = 'lgs_3e3j5tkog48pnny9dmfzj1r16pg8t1e76dz5tmac6iq689wyjfpiij4txtdo'

fwlogos = open('genlogos.json', 'w')
acc = []
startrep = []
announce = []
micros = []
epochs = []

def hash_startrep(b2b, dictionary):
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(19, 1)))                         # type
    b2b.update(binascii.unhexlify(dictionary['origin']))                         # origin
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 32)))                         # previous
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 16)))                         # fee
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 4, True)))                    # sequence
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 4)))                          # epoch
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 32)))                         # gov previous
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(int(dictionary['stake']), 16)))  # stake
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(100, 1)))                        # levy percentage
    return b2b

def hash_announce(b2b, dictionary):
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(17, 1)))                         # type
    b2b.update(binascii.unhexlify(dictionary['origin']))                         # origin
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 32)))                         # previous
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 16)))                         # fee
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 4, True)))                    # sequence
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 4)))                          # epoch
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 32)))                         # gov previous
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(int(dictionary['stake']), 16)))  # stake
    b2b.update(binascii.unhexlify(dictionary['bls_pub']))                        # bls
    b2b.update(binascii.unhexlify(dictionary['ecies_pub']))                      # ecies
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(100, 1)))                        # levy percentage
    return b2b

def hash_send(b2b, dictionary, sequence, previous):
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 1, True)))                    # type
    b2b.update(qlmdb3.fromaccount(genesis_pub))                                  # origin
    b2b.update(binascii.unhexlify(previous))                                     # previous
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 16)))                         # fee
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(sequence, 4, True)))             # sequence
    b2b.update(binascii.unhexlify(dictionary['account']))                        # destination 
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(int(dictionary['amount']), 16))) # amount
    return b2b

def hash_micro(b2b, epoch, previous):
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 1, True)))                    # version    
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(epoch, 4, True)))                # epoch number
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 4, True)))                    # delegate epoch_num
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(epoch, 4, True)))                # sequence
    b2b.update(binascii.unhexlify(previous))                                     # previous
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(1, 1)))                          # last
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 4, True)))                    # numblocks
    for numdel in range(32):
        b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 4)))                      # epoch number
        b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 4)))                      # sequence
        b2b.update(binascii.unhexlify((qlmdb3.hexstr(0, 32))))                   # tips
    return b2b

def hash_delegate(b2b, dictionary):
    b2b.update(binascii.unhexlify(dictionary['account']))                        # account
    b2b.update(binascii.unhexlify(dictionary['bls_pub']))                        # bls
    b2b.update(binascii.unhexlify(dictionary['ecies_pub']))                      # ecies
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(int(dictionary['vote']), 16)))   # rawvote
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(int(dictionary['stake']), 16)))  # rawstake
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(int(dictionary['vote']), 16)))   # vote
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(int(dictionary['stake']), 16)))  # stake
    return b2b
    
def hash_epoch(b2b, epoch, previous, microtip, delegates):
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 1, True)))                    # version
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(epoch, 4, True)))                # epoch number
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 4, True)))                    # delegate epoch_num
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 4, True)))                    # sequence
    b2b.update(binascii.unhexlify(previous))                                     # previous
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(epoch, 4, True)))                # tip - epoch
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(epoch, 4, True)))                # tip - sequence
    b2b.update(binascii.unhexlify(microtip))                                     # tip - hash
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 16)))                         # transaction_fee_pool
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 16)))                         # total_supply
    for delegate in delegates:
        b2b = hash_delegate(b2b, delegate)                                       # delegates
    b2b.update(binascii.unhexlify(qlmdb3.hexstr(0, 8)))                          # total rbs
    return b2b

with open('master_list.json') as fmaster:
        master = json.load(fmaster)

delegates = []
sequence = 1
previous = "2A610E54BD32E19E9955624622D7D48316F02153D6F2F9A4CFDEF5E79686E138"
for filename in sorted(os.listdir('./accounts')):
    with open('./accounts/'+filename) as f:
        data = json.load(f)

    user = filename.split('.')[0]
    #######################################################################################
    ## CHECK AGAINST MASTER LIST
    #######################################################################################
    assert master[user]['amount'] == data['funding_info']['amount'], 'FAIL funding info mismatch'
    assert master[user]['vote'] == data['delegate_info']['vote'], 'FAIL delegate_info vote mismatch'
    assert master[user]['stake'] == data['delegate_info']['stake'], 'FAIL delegate_info stake mismatch'
    assert master[user]['stake'] == data['startrep']['stake'], 'FAIL startrep stake mismatch'
    assert master[user]['stake'] == data['announce']['stake'], 'FAIL announce stake mismatch'
    
    #######################################################################################
    ## GENERATE TRANSACTIONS
    #######################################################################################
    # Verify signature to ensure validity
    y = data['funding_info']
    h = blake2b(digest_size=32)
    h.update(binascii.unhexlify(y['account']))
    h.update(binascii.unhexlify(qlmdb3.hexstr(int(y['amount']), 16)))
    account_hash = binascii.hexlify(h.digest()).decode('ascii')
    
    vkey = ed25519_blake2b.VerifyingKey(bytes.fromhex(y['account']))
    try:
        vkey.verify(bytes.fromhex(y['signature']), bytes.fromhex(account_hash))
    except:
        print("FAIL ACCOUNT: invalid signature by account {}, retry".format(y['account']))
        sys.exit()
    
    # Create send request and sign with genesis prv key
    h = blake2b(digest_size=32)
    h = hash_send(h, y, sequence, previous)
    fin_hash = binascii.hexlify(h.digest()).decode('ascii').upper()
    
    sk = ed25519_blake2b.SigningKey(keydata)
    hashdata = bytes.fromhex(fin_hash)
    sig = sk.sign(hashdata)
    hexSig = sig.hex().upper()
    acc.append({'account': y['account'].upper(),
                'amount': y['amount'],
                'previous': previous.upper(),
                'sequence': sequence,
                'signature': hexSig
    })

    sequence += 1
    previous = fin_hash
    
    #######################################################################################
    ## GENERATE START REPRESENTING
    #######################################################################################
    # Verify signature to ensure validity
    y = data['startrep']
    h = blake2b(digest_size=32)
    h = hash_startrep(h, y)
    startrep_hash = binascii.hexlify(h.digest()).decode('ascii')
    
    vkey = ed25519_blake2b.VerifyingKey(bytes.fromhex(y['origin']))
    try:
        vkey.verify(bytes.fromhex(y['signature']), bytes.fromhex(startrep_hash))
        startrep.append(y)
    except:
        print("FAIL START REPRESENTING: invalid signature by account {}, retry".format(y['origin']))
        sys.exit()

    #######################################################################################
    ## GENERATE ANNOUNCE CANDIDACY
    #######################################################################################
    # Verify signature to ensure validity
    y = data['announce']
    h = blake2b(digest_size=32)
    h = hash_announce(h, y)
    announce_hash = binascii.hexlify(h.digest()).decode('ascii')
    
    vkey = ed25519_blake2b.VerifyingKey(bytes.fromhex(y['origin']))
    try:
        vkey.verify(bytes.fromhex(y['signature']), bytes.fromhex(announce_hash))
        announce.append(y)
    except:
        print("FAIL ANNOUNCE CANDIDACY: invalid signature by account {}, retry".format(y['origin']))
        sys.exit()

    #######################################################################################
    ## GENERATE DELEGATE INFO FOR EPOCH
    #######################################################################################
    # Verify signature on  delegate info to ensure validity
    if (len(delegates) <=31):
        y = data['delegate_info']
        h = blake2b(digest_size=32)
        h = hash_delegate(h, y)
        delinfo_hash = binascii.hexlify(h.digest()).decode('ascii')
        
        vkey = ed25519_blake2b.VerifyingKey(bytes.fromhex(y['account']))
        try:
            vkey.verify(bytes.fromhex(y['signature']), bytes.fromhex(delinfo_hash))
            delegates.append(y)
        except:
            print("FAIL DELEGATE INFO: invalid signature by account {}, retry".format(y['account']))
            sys.exit()
    
        
previous = qlmdb3.hexstr(0, 32)
epoch_previous = qlmdb3.hexstr(0, 32)

#######################################################################################
## GENERATE MICROBLOCKS/EPOCHS
#######################################################################################
for i in range(3):
    h = blake2b(digest_size=32)
    h = hash_micro(h, i, previous)
    micro_hash = binascii.hexlify(h.digest()).decode('ascii').upper()
    
    micros.append({'epoch_number': i,
                   'sequence': i,
                   'previous': previous,
                   'hash': micro_hash})
    previous = micro_hash

    h = blake2b(digest_size=32)
    h = hash_epoch(h, i, epoch_previous, micro_hash, delegates)
    epoch_hash = binascii.hexlify(h.digest()).decode('ascii').upper()
    
    epochs.append({'epoch_number': i,
                   'previous': epoch_previous,
                   'microtip': micro_hash,
                   'hash': epoch_hash,
                   'delegates': delegates})
    
    epoch_previous = epoch_hash

#######################################################################################
## CREATE FINAL FILE
#######################################################################################
final = {'accounts':acc,
         'micros':micros,
         'epochs':epochs,
         'start':startrep,
         'announce':announce}

## Hash for entire genlogos file
h = blake2b(digest_size=32)

for entry in acc:
    h = hash_send(h, entry, entry['sequence'], entry['previous'])
    
for entry in micros:
    h = hash_micro(h, entry['epoch_number'], entry['previous'])

for entry in epochs:
    h = hash_epoch(h, entry['epoch_number'], entry['previous'], entry['microtip'], entry['delegates'])
    
for entry in startrep:
    h = hash_startrep(h, entry)

for entry in announce:
    h = hash_announce(h, entry)

## Sign entire file with genesis priv key
final_hash = binascii.hexlify(h.digest()).decode('ascii').upper()
sk = ed25519_blake2b.SigningKey(keydata)
hashdata = bytes.fromhex(final_hash)
sig = sk.sign(hashdata)
hexSig = sig.hex().upper()

final['signature'] = hexSig
fwlogos.write(json.dumps(final, indent=4))
fwlogos.close()
fmaster.close()
