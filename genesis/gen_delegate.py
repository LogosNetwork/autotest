import qlmdb3
import binascii
import json
from pyblake2 import blake2b
import ed25519_blake2b
import os

## GENERATE TRANSACTIONS

with open('fake_del.json') as f:
    data = json.load(f)

directory = 'accounts'
a = 0
account = {}
if not os.path.exists(directory):
    os.makedirs(directory)
    
for y in data['accounts']:
    fw = open(directory+'/genaccount'+"{0:0>2}".format(a)+'.json','w')
    keydata = bytes.fromhex(y['private'])
    sk = ed25519_blake2b.SigningKey(keydata)

    ################################################################################
    ## GENERATE SEND INFORMATION
    ################################################################################
    h = blake2b(digest_size=32)
    h.update(qlmdb3.fromaccount(y['account']))                        # destination 
    h.update(binascii.unhexlify(qlmdb3.hexstr(int(y['amount']), 16))) # amount

    send_hash = binascii.hexlify(h.digest()).decode('ascii')
    hashdata = bytes.fromhex(send_hash)
    sig = sk.sign(hashdata)
    hexSig = sig.hex().upper()
    
    account['transaction'] = {'account': binascii.hexlify(qlmdb3.fromaccount(y['account'])).decode('ascii').upper(),
                              'amount': y['amount'],
                              'signature': hexSig}
    
    ################################################################################
    ## GENERATE DELEGATE INFORMATION
    ################################################################################
    # hash in same order that delegate is hashed in logos_core
    h = blake2b(digest_size=32)
    h.update(qlmdb3.fromaccount(y['account']))                             # account
    h.update(binascii.unhexlify(y['bls_pub']))                             # bls
    h.update(binascii.unhexlify(y['ecies_pub']))                           # ecies
    h.update(binascii.unhexlify(qlmdb3.hexstr(int(y['vote']), 16)))        # rawvote
    h.update(binascii.unhexlify(qlmdb3.hexstr(int(y['stake']), 16)))       # rawstake
    h.update(binascii.unhexlify(qlmdb3.hexstr(int(y['vote']), 16)))        # vote
    h.update(binascii.unhexlify(qlmdb3.hexstr(int(y['stake']), 16)))       # stake
    
    delinfo_hash = binascii.hexlify(h.digest()).decode('ascii')
    hashdata = bytes.fromhex(delinfo_hash)
    sig = sk.sign(hashdata)
    hexSig = sig.hex().upper()
    
    account['delegate_info'] = {'account': binascii.hexlify(qlmdb3.fromaccount(y['account'])).decode('ascii').upper(),
                                'stake': y['stake'],
                                'vote': y['vote'],
                                'bls_pub': y['bls_pub'],
                                'ecies_pub': y['ecies_pub'],
                                'signature': hexSig}
    
    ################################################################################
    ## GENERATE ANNOUNCE CANDIDACY
    ################################################################################
    h = blake2b(digest_size=32)
    h.update(binascii.unhexlify(qlmdb3.hexstr(17, 1)))                      # type
    h.update(qlmdb3.fromaccount(y['account']))                              # origin
    h.update(binascii.unhexlify(qlmdb3.hexstr(0, 32)))                      # previous
    h.update(binascii.unhexlify(qlmdb3.hexstr(0, 16)))                      # fee
    h.update(binascii.unhexlify(qlmdb3.hexstr(0, 4, True)))                 # sequence
    h.update(binascii.unhexlify(qlmdb3.hexstr(0, 4)))                       # epoch
    h.update(binascii.unhexlify(qlmdb3.hexstr(0, 32)))                      # gov previous
    h.update(binascii.unhexlify(qlmdb3.hexstr(int(y['stake']), 16)))        # stake
    h.update(binascii.unhexlify(y['bls_pub']))                              # bls
    h.update(binascii.unhexlify(y['ecies_pub']))                            # ecies
    h.update(binascii.unhexlify(qlmdb3.hexstr(100, 1)))                     # levy percentage

    announce_hash = binascii.hexlify(h.digest()).decode('ascii')
    hashdata = bytes.fromhex(announce_hash)
    sig = sk.sign(hashdata)
    hexSig = sig.hex().upper()
    
    account['announce'] = {'origin': binascii.hexlify(qlmdb3.fromaccount(y['account'])).decode('ascii').upper(),
                           'stake': y['stake'],
                           'bls_pub': y['bls_pub'],
                           'ecies_pub': y['ecies_pub'],
                           'signature': hexSig}
    
    ################################################################################
    ## GENERATE START REPRESENTING
    ################################################################################
    h = blake2b(digest_size=32)
    h.update(binascii.unhexlify(qlmdb3.hexstr(19, 1)))                     # type
    h.update(qlmdb3.fromaccount(y['account']))                             # origin
    h.update(binascii.unhexlify(qlmdb3.hexstr(0, 32)))                     # previous
    h.update(binascii.unhexlify(qlmdb3.hexstr(0, 16)))                     # fee
    h.update(binascii.unhexlify(qlmdb3.hexstr(0, 4, True)))                # sequence
    h.update(binascii.unhexlify(qlmdb3.hexstr(0, 4)))                      # epoch
    h.update(binascii.unhexlify(qlmdb3.hexstr(0, 32)))                     # gov previous
    h.update(binascii.unhexlify(qlmdb3.hexstr(int(y['stake']), 16)))       # stake
    h.update(binascii.unhexlify(qlmdb3.hexstr(100, 1)))                    # levy percentage
    startrep_hash = binascii.hexlify(h.digest()).decode('ascii')

    hashdata = bytes.fromhex(startrep_hash)
    sig = sk.sign(hashdata)
    hexSig = sig.hex().upper()
    
    account['startrep'] = {'origin': binascii.hexlify(qlmdb3.fromaccount(y['account'])).decode('ascii').upper(),
                           'stake': y['stake'],
                           'signature': hexSig}

    fw.write(json.dumps(account, indent=4))
    a += 1
    
fw.close()
