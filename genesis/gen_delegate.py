import qlmdb3
import binascii
import json
from pyblake2 import blake2b
import ed25519_blake2b



## GENERATE TRANSACTIONS

with open('fake_del.json') as f:
    data = json.load(f)

a = 0
    
for y in data['accounts']:
    fw = open('accounts/genaccount'+"{0:0>2}".format(a)+'.json','w')
    keydata = bytes.fromhex(y['private'])
    sk = ed25519_blake2b.SigningKey(keydata)
    fw.write('{\n')
    
    h = blake2b(digest_size=32)
    h.update(qlmdb3.fromaccount(y['account']))                        # destination 
    h.update(binascii.unhexlify(qlmdb3.hexstr(int(y['amount']), 16))) # amount
    fin_hash = binascii.hexlify(h.digest()).decode('ascii')

    keydata = bytes.fromhex(y['private'])
    sk = ed25519_blake2b.SigningKey(keydata)
    hashdata = bytes.fromhex(fin_hash)
    sig = sk.sign(hashdata)
    hexSig = sig.hex().upper()
    fw.write('\t\"transaction\": \n\t{\n')
    fw.write('\t\t\"account\": \"{}\", \"amount\": \"{}\", \"signature\": \"{}\"\n'.format(binascii.hexlify(qlmdb3.fromaccount(y['account'])).decode('ascii'),y['amount'],hexSig))
    fw.write('\t},\n')
    
    ## GENERATE DELEGATE INFORMATION
    h = blake2b(digest_size=32)
    h.update(qlmdb3.fromaccount(y['account']))                             # account
    h.update(binascii.unhexlify(qlmdb3.hexstr(int(y['stake']), 16)))       # stake
    h.update(binascii.unhexlify(qlmdb3.hexstr(int(y['vote']), 16)))        # vote
    h.update(binascii.unhexlify(y['bls_pub']))                             # bls
    h.update(binascii.unhexlify(y['ecies']))                               # ecies
    
    delinfo_hash = binascii.hexlify(h.digest()).decode('ascii')
    hashdata = bytes.fromhex(delinfo_hash)
    sig = sk.sign(hashdata)
    hexSig = sig.hex().upper()
    fw.write('\t\"delegate_info\": \n\t{\n')
    fw.write('\t\t\"account\": \"{}\", \"stake\": \"{}\", \"vote\": \"{}\", \"bls_pub\": \"{}\", \"ecies\": \"{}\", \"signature\": \"{}\"\n'.format(binascii.hexlify(qlmdb3.fromaccount(y['account'])).decode('ascii'),y['stake'],y['vote'],y['bls_pub'],y['ecies'],hexSig))
    fw.write('\t},\n')
    
    ## GENERATE ANNOUNCE CANDIDACY
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
    h.update(binascii.unhexlify(y['ecies']))                                # ecies
    h.update(binascii.unhexlify(qlmdb3.hexstr(100, 1)))                     # levy percentage
    announce_hash = binascii.hexlify(h.digest()).decode('ascii')
    #print(announce_hash)
    hashdata = bytes.fromhex(announce_hash)
    sig = sk.sign(hashdata)
    hexSig = sig.hex().upper()
    fw.write('\t\"announce\": \n\t{\n')
    fw.write('\t\t\"origin\": \"{}\", \"stake\": \"{}\", \"bls\": \"{}\", \"ecies\": \"{}\", \"signature\": \"{}\"\n'.format(binascii.hexlify(qlmdb3.fromaccount(y['account'])).decode('ascii'),y['stake'],y['bls_pub'],y['ecies'],hexSig))
    fw.write('\t},\n')
    
    ## GENERATE START REPRESENTING
    
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
    fin_hash = binascii.hexlify(h.digest()).decode('ascii')

    print(binascii.hexlify(qlmdb3.fromaccount(y['account'])))
    #print(qlmdb3.hexstr(int(y['stake']), 16))
    #print(qlmdb3.hexstr(100, 1))
    print(fin_hash)
    hashdata = bytes.fromhex(fin_hash)
    sig = sk.sign(hashdata)
    hexSig = sig.hex().upper()
    print(hexSig)
    fw.write('\t\"start\": \n\t{\n')
    fw.write('\t\t\"origin\": \"{}\", \"stake\": \"{}\", \"signature\": \"{}\"\n'.format(binascii.hexlify(qlmdb3.fromaccount(y['account'])).decode('ascii'),y['stake'],hexSig))
    fw.write('\t}\n')
    fw.write('}\n')
    fw.close()

    a += 1
    
