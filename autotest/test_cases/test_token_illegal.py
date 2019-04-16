from utils import *
from orchestration import *
import random
import json
import qlmdb3


class TestCaseMixin:

    #malformed_amt = {'decimal':'1234.1', 'negative':'-1234', 'empty':''}
    #malformed_dest = {'empty':'', 'publickey':'E41C9CFF2C98A049519C516E275F216A22A2C28290322A6504679F7C323F63D6'}
    
    def test_token_issuance_illegal(self):
        print(self.nodes[0].account_info(self.account_list[1]['account']))
        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        '''
        gen_info = self.nodes[0].account_info()
        created = self.nodes[0].block_create(
            previous=gen_info['frontier'],
            transactions=[{"destination":self.account_list[1]['account'], "amount":"3000000000000000000000000000000000000"}]
        )

        
        self.nodes[0].process(created['request'])
        sleep(7)
        '''
        #print(account_info)

        print("long symbol")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='QWERTYUIO',
                name='sgcoin',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}],
                settings=["revoke"]
            )
            
            #self.nodes[0].process(created['request'])
            self.nodes[0].process(created)
            print('symbol: too long symbol check fails')
            #return False
        except LogosRPCError as error:
            print(error)

        print("illegal symbol")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='!SG',
                name='sgcoin',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}],
                settings=["revoke"]
            )
            self.nodes[0].process(created['request'])
            print('symbol: illegal symbol char')
        except LogosRPCError as error:
            print(error)

        print("empty symbol")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='',
                name='sgcoin',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}],
                settings=["revoke"]
            )
            self.nodes[0].process(created['request'])
            print('symbol: empty symbol fails')
        except LogosRPCError as error:
            print(error)    


        print("no name")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                symbol='SG',
                name='',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}],
                settings=["revoke"]
            )
            self.nodes[0].process(created['request'])
            print('name: fails')
        except LogosRPCError as error:
            print(error)

        print("total supply: empty")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='SG',
                name='sgcoin',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}],
                settings=["revoke"],
                total_supply=''
            )
            self.nodes[0].process(created['request'])
            print('supply: fails')
        except LogosRPCError as error:
            print(error)

        
        print("total supply: decimal")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='SG',
                name='sgcoin',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}],
                settings=["revoke"],
                total_supply='1234.12'
            )
            self.nodes[0].process(created['request'])
            print('supply: fails')
        except LogosRPCError as error:
            print(error)

        print("total supply: negative")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='SG',
                name='sgcoin',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}],
                settings=["revoke"],
                total_supply='-1234'
            )
            self.nodes[0].process(created['request'])
            print('name: fails')
        except LogosRPCError as error:
            print(error)

        '''
        print("total supply: int")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='TEST',
                name='tscoin1',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}],
                settings=["revoke"],
                total_supply=1200000000000
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('name: fails')
        except LogosRPCError as error:
            print(error)

        '''
        
        print("total supply: no amount")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='TEST2',
                name='testcoin2',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}],
                settings=["revoke"],
                total_supply=''
            )
            self.nodes[0].process(created['request'])
            print('total supply: fails')
        except LogosRPCError as error:
            print(error)

        '''
        print("fee_type: Uppercase")
        try:
            print(prev)
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='TEST3',
                name='testcoin3',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}],
                settings=["revoke"],
                fee_type='Flat'
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('fee_type: fails')
        except LogosRPCError as error:
            print(error)
        '''
        print("fee_type: empty")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='TEST3',
                name='testcoin3',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}],
                settings=["revoke"],
                fee_type=''
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('fee_type: fails')
        except LogosRPCError as error:
            print(error)

        print("fee_type: empty")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='TEST3',
                name='testcoin3',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}],
                settings=["revoke"],
                fee_type=''
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('fee_type: fails')
        except LogosRPCError as error:
            print(error)

        print("fee_rate: above100")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='TEST3',
                name='testcoin3',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}],
                settings=["revoke"],
                fee_type='percentage',
                fee_rate='101'
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('fee_rate: fails')
        except LogosRPCError as error:
            print(error)


        print("fee_rate: decimal")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='TEST3',
                name='testcoin3',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}],
                settings=["revoke"],
                fee_rate='1.5'
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('fee_rate: fails')
        except LogosRPCError as error:
            print(error)
        
        print("fee_rate: negative")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='TEST3',
                name='testcoin3',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}],
                settings=["revoke"],
                fee_rate='-39'
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('fee_rate: fails')
        except LogosRPCError as error:
            print(error)

        '''
        print("fee_rate: empty")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='TEST3',
                name='testcoin3',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}],
                settings=["revoke"],
                fee_rate=''
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('fee_rate: fails')
        except LogosRPCError as error:
            print(error)   
        '''
        '''
        print("settings: empty")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='TEST3',
                name='testcoin3',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}]
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('fee_rate: fails')
        except LogosRPCError as error:
            print(error)   
        '''
        print("settings: incorrect")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                settings=['distribute'],
                symbol='TEST3',
                name='testcoin3',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}]
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('fee_rate: fails')
        except LogosRPCError as error:
            print(error)
        '''
        print("settings: duplicate")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                settings=['revoke', 'revoke'],
                symbol='TEST3',
                name='testcoin3',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn","distribute"]}]
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('fee_rate: fails')
        except LogosRPCError as error:
            print(error) 
        '''
        '''
        print("controllers: empty")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='TEST3',
                name='testcoin3',
                controllers=[],
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('fee_rate: fails')
        except LogosRPCError as error:
            print(error)
        '''

        print("controllers: no account")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='TEST3',
                name='testcoin3',
                controllers=[{"privileges": ["burn","distribute"]}],
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('fee_rate: fails')
        except LogosRPCError as error:
            print(error)

        print("controllers: no privileges")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='TEST3',
                name='testcoin3',
                controllers=[{"account":self.account_list[1]['account']}],
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('fee_rate: fails')
        except LogosRPCError as error:
            print(error)
        

        print("controllers: no privileges")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='TEST3',
                name='testcoin3',
                controllers=[{"account":self.account_list[1]['account']}],
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('fee_rate: fails')
        except LogosRPCError as error:
            print(error)

        print("controllers: invalid privileges")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='TEST3',
                name='testcoin3',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["token_send", "burn","distribute"]}],
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('fee_rate: fails')
        except LogosRPCError as error:
            print(error)

        '''
        print("controllers: duplicate privileges")
        try:
            created = self.nodes[0].block_create_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                symbol='TEST3',
                name='testcoin3',
                controllers=[{"account":self.account_list[1]['account'], "privileges": ["burn", "burn","distribute"]}],
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('fee_rate: fails')
        except LogosRPCError as error:
            print(error)
        '''
        

    def test_additional_issuance_illegal(self):
        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        print("creating valid token account")
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TEST3',
            name='testcoin3',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["issuance", "burn","distribute"]},
            {"account":self.account_list[2]['account'], "privileges": ["burn","distribute"]}],
            settings=["revoke", "issuance"]
        )
        print(created)
        coin = eval(created['request'])
        self.nodes[0].process(created['request'])

        try:
            print("issue_additional: empty amount")
            created = self.nodes[0].block_create_additional_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                amount="",
                token_id=coin['token_id']
            )
            
            self.nodes[0].process(created['request'])
            print('issue_additional: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("issue_additional: decimal amount")
            created = self.nodes[0].block_create_additional_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                amount="123.123",
                token_id=coin['token_id']
            )
            
            self.nodes[0].process(created['request'])
            print('issue_additional: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("issue_additional: negative amount")
            created = self.nodes[0].block_create_additional_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                amount="-1000",
                token_id=coin['token_id']
            )
            
            self.nodes[0].process(created['request'])
            print('issue_additional: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("issue_additional: max amount")
            created = self.nodes[0].block_create_additional_issuance(
                key=self.account_list[1]['private'],
                previous=prev,
                amount="350000000000000000000000000000000000000",
                token_id=coin['token_id']
            )
            
            self.nodes[0].process(created['request'])
            print('issue_additional: fails')
        except LogosRPCError as error:
            print(error)
            
        try:
            print("issue_additional: no privilege controller")
            created = self.nodes[0].block_create_additional_issuance(
                key=self.account_list[2]['private'],
                previous=prev,
                amount="1000",
                token_id=coin['token_id']
            )
            
            self.nodes[0].process(created['request'])
            print('issue_additional: fails')
        except LogosRPCError as error:
            print(error)

    def test_change_setting(self):
        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        print("creating valid token account")
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TEST3',
            name='testcoin3',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["issuance", "burn","distribute", "change_issuance"]},
            {"account":self.account_list[2]['account'], "privileges": ["burn","distribute"]}],
            settings=["revoke", "modify_issuance"]
        )
        print(created)
        coin = eval(created['request'])
        self.nodes[0].process(created['request'])

        try:
            print("change_setting: illegal setting")
            created = self.nodes[0].block_create_change_setting(
                key=self.account_list[1]['private'],
                previous=prev,
                value="True",
                setting="distribute",
                token_id=coin['token_id']
            )
            
            self.nodes[0].process(created['request'])
            print('change_setting: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("change_setting: empty setting")
            created = self.nodes[0].block_create_change_setting(
                key=self.account_list[1]['private'],
                previous=prev,
                value="True",
                setting="",
                token_id=coin['token_id']
            )
            
            self.nodes[0].process(created['request'])
            print('change_setting: fails')
        except LogosRPCError as error:
            print(error)

        try: #TODO: doesn't work (True must also be lowercase)
            print("change_setting: capitalize setting")
            created = self.nodes[0].block_create_change_setting(
                key=self.account_list[1]['private'],
                previous=prev,
                value="True",
                setting="Issuance",
                token_id=coin['token_id']
            )
            
            self.nodes[0].process(created['request'])
            print('change_setting: fails')
        except LogosRPCError as error:
            print(error)

        try: # come back to this
            print("change_setting: capitalize setting")
            created = self.nodes[0].block_create_change_setting(
                key=self.account_list[1]['private'],
                previous=prev,
                value="true",
                setting="issuance",
                token_id=coin['token_id']
            )
            
            self.nodes[0].process(created['request'])
            print('change_setting: fails')
        except LogosRPCError as error:
            print(error)
        
        try: # come back to this
            print("change_setting: malformed value")
            created = self.nodes[0].block_create_change_setting(
                key=self.account_list[1]['private'],
                previous=prev,
                value="0",
                setting="issuance",
                token_id=coin['token_id']
            )
            
            self.nodes[0].process(created['request'])
            print('change_setting: fails')
        except LogosRPCError as error:
            print(error)

        try: # come back to this
            print("change_setting: no value")
            created = self.nodes[0].block_create_change_setting(
                key=self.account_list[1]['private'],
                previous=prev,
                value="",
                setting="issuance",
                token_id=coin['token_id']
            )
            
            self.nodes[0].process(created['request'])
            print('change_setting: fails')
        except LogosRPCError as error:
            print(error)

        
    def test_immute_setting(self):
        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        print("creating valid token account")
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TSET',
            name='testimmutesetting',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["distribute", "issuance", "change_modify_issuance", "revoke", "change_modify_revoke", "freeze", "change_modify_freeze", "change_modify_adjust_fee", "change_modify_whitelist"]},
            {"account":self.account_list[2]['account'], "privileges": ["distribute"]}],
            settings=["revoke", "issuance", "modify_issuance", "modify_revoke", "freeze", "modify_freeze", "modify_adjust_fee", "modify_whitelist"]
        )
        print(created)
        coin = eval(created['request'])
        prev = created['hash']
        token_account = qlmdb3.toaccount(qlmdb3.unhexlify(coin['token_id']))
        self.nodes[0].process(created['request'])
        sleep(10)

        print('FUND TOKENACCOUNT WITH LOGOS')
        gen_info = self.nodes[0].account_info()
        sleep(6)
        
        created = self.nodes[0].block_create(
            previous=gen_info['frontier'],
            transactions=[{"destination":token_account, "amount":"1000000000000000000000000000000000000"}]
        )
        
        self.nodes[0].process(created['request'])
        sleep(10)
        try:
            print("immute setting: un immutable setting")
            created = self.nodes[0].block_create_immute_setting(
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                setting='distribute'
            )
            self.nodes[0].process(created['request'])
        except LogosRPCError as error:
            print(error)

        try:
            print("immute setting: wrong setting")
            created = self.nodes[0].block_create_immute_setting(
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                setting='modify_issuance'
            )
            self.nodes[0].process(created['request'])
            print('immute setting: fail')
        except LogosRPCError as error:
            print(error)
        
        try:
            print("immute setting: empty setting")
            created = self.nodes[0].block_create_immute_setting(
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                setting=''
            )
            self.nodes[0].process(created['request'])
            print('immute setting: fail')
        except LogosRPCError as error:
            print(error)
        ''' works correctly
        try:
            print("immute setting: capitalize setting")
            created = self.nodes[0].block_create_immute_setting(
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                setting='Issuance'
            )
            self.nodes[0].process(created['request'])
            print('immute setting: fail')
        except LogosRPCError as error:
            print(error)
        '''
        try:
            print("immute setting: no change privilege")
            created = self.nodes[0].block_create_immute_setting(
                key=self.account_list[2]['private'],
                previous=prev,
                token_id=coin['token_id'],
                setting='issuance'
            )
            self.nodes[0].process(created['request'])
            print('immute setting: fail')
        except LogosRPCError as error:
            print(error)
        try:
            print("immute setting: no change privilege")
            created = self.nodes[0].block_create_immute_setting(
                key=self.account_list[2]['private'],
                previous=prev,
                token_id=coin['token_id'],
                setting='revoke'
            )
            self.nodes[0].process(created['request'])
        except LogosRPCError as error:
            print(error)
        try:
            print("immute setting: no change privilege")
            created = self.nodes[0].block_create_immute_setting(
                key=self.account_list[2]['private'],
                previous=prev,
                token_id=coin['token_id'],
                setting='freeze'
            )
            self.nodes[0].process(created['request'])
            print('immute setting: fail')
        except LogosRPCError as error:
            print(error)
        try:
            print("immute setting: no change privilege")
            created = self.nodes[0].block_create_immute_setting(
                key=self.account_list[2]['private'],
                previous=prev,
                token_id=coin['token_id'],
                setting='adjust_fee'
            )
            self.nodes[0].process(created['request'])
        except LogosRPCError as error:
            print(error)
        try:
            print("immute setting: no change privilege")
            created = self.nodes[0].block_create_immute_setting(
                key=self.account_list[2]['private'],
                previous=prev,
                token_id=coin['token_id'],
                setting='whitelist'
            )
            self.nodes[0].process(created['request'])
            print('immute setting: fail')
        except LogosRPCError as error:
            print(error)

    def test_revoke(self):
        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        print("creating valid token account")
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TREVOKE',
            name='testrevoke',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["issuance", "burn","distribute", "revoke"]},
            {"account":self.account_list[2]['account'], "privileges": ["distribute"]}],
            settings=["revoke", "modify_issuance"]
        )
        print(created)
        coin = eval(created['request'])
        prev = created['hash']
        token_account = qlmdb3.toaccount(qlmdb3.unhexlify(coin['token_id']))
        self.nodes[0].process(created['request'])
        sleep(10)

        print('FUND TOKENACCOUNT WITH LOGOS')
        gen_info = self.nodes[0].account_info()
        sleep(6)
        
        created = self.nodes[0].block_create(
            previous=gen_info['frontier'],
            transactions=[{"destination":token_account, "amount":"1000000000000000000000000000000000000"}]
        )
        
        self.nodes[0].process(created['request'])

        sleep(10)
        
        print("valid distribute")
        created = self.nodes[0].block_create_tokreq(
            type="distribute",
            key=self.account_list[1]['private'],
            previous=prev,
            token_id=coin['token_id'],
            transaction={"destination" : self.account_list[2]['account'], "amount": "100000000000000" }
        )
        self.nodes[0].process(created['request'])

        sleep(10)
        prev = created['hash']
        
        try:
            print("revoke: empty source")
            created = self.nodes[0].block_create_revoke(
                type="revoke",
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                source="",
                transaction={"destination" : self.account_list[1]['account'], "amount": "1000" }
            )
            self.nodes[0].process(created['request'])
            print('revoke: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("revoke: publickey source")
            created = self.nodes[0].block_create_revoke(
                type="revoke",
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                source=self.account_list[2]['public'],
                transaction={"destination" : self.account_list[1]['account'], "amount": "1000" }
            )
            self.nodes[0].process(created['request'])
            print('revoke: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("revoke: empty destination")
            created = self.nodes[0].block_create_revoke(
                type="revoke",
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                source=self.account_list[2]['account'],
                transaction={"destination" : "", "amount": "1000" }
            )
            self.nodes[0].process(created['request'])
            print('revoke: fails')
        except LogosRPCError as error:
            print(error)
            
        try:
            print("revoke: publickey destination")
            created = self.nodes[0].block_create_revoke(
                type="revoke",
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                source=self.account_list[2]['account'],
                transaction={"destination" : self.account_list[1]['public'], "amount": "1000" }
            )
            self.nodes[0].process(created['request'])
            print('revoke: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("revoke: no amount")
            created = self.nodes[0].block_create_revoke(
                type="revoke",
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                source=self.account_list[2]['account'],
                transaction={"destination" : self.account_list[1]['account'], "amount": "" }
            )
            self.nodes[0].process(created['request'])
            print('revoke: fails')
        except LogosRPCError as error:
            print(error)
        '''
        try:
            print("revoke: decimal amount")
            created = self.nodes[0].block_create_revoke(
                type="revoke",
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                source=self.account_list[2]['account'],
                transaction={"destination" : self.account_list[1]['account'], "amount": "1000.12" }
            )
            self.nodes[0].process(created['request'])
            print('revoke: fails')
        except LogosRPCError as error:
            print(error)
        '''
        try:
            print("revoke: negative amount")
            created = self.nodes[0].block_create_revoke(
                type="revoke",
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                source=self.account_list[2]['account'],
                transaction={"destination" : self.account_list[1]['account'], "amount": "-1000" }
            )
            self.nodes[0].process(created['request'])
            print('revoke: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("revoke: no privileges")
            created = self.nodes[0].block_create_revoke(
                type="revoke",
                key=self.account_list[2]['private'],
                previous=prev,
                token_id=coin['token_id'],
                source=self.account_list[1]['account'],
                transaction={"destination" : self.account_list[2]['account'], "amount": "1000" }
            )
            self.nodes[0].process(created['request'])
            print('revoke: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("revoke: too much")
            created = self.nodes[0].block_create_revoke(
                type="revoke",
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                source=self.account_list[2]['account'],
                transaction={"destination" : self.account_list[1]['account'], "amount": "10000000000000000000000000" }
            )
            self.nodes[0].process(created['request'])
            print('revoke: fails')
        except LogosRPCError as error:
            print(error)
            

            
    def test_adjust_user_status(self):
        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        print("creating valid token account")
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TADJUSER',
            name='testadjustuserstatus',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["withdraw_fee", "issuance", "burn","distribute", "whitelist", "freeze"]},
            {"account":self.account_list[2]['account'], "privileges": ["revoke"]}],
            settings=["revoke", "modify_issuance", "whitelist", "freeze"]
        )
        coin = eval(created['request'])
        prev = created['hash']
        token_account = qlmdb3.toaccount(qlmdb3.unhexlify(coin['token_id']))
        self.nodes[0].process(created['request'])
        sleep(10)

        gen_info = self.nodes[0].account_info()
        sleep(6)
        created = self.nodes[0].block_create(
            previous=gen_info['frontier'],
            transactions=[{"destination":token_account, "amount":"1000000000000000000000000000000000000"}]
        )
        self.nodes[0].process(created['request'])

        sleep(10)
        
        for key, value in {'empty':'','publickey':self.account_list[2]['public']}.items():
            try:
                print("adjust user status: {} destination".format(key))
                created = self.nodes[0].block_create_adjust_user_status(
                    key=self.account_list[1]['private'],
                    previous=prev,
                    token_id=coin['token_id'],
                    status="whitelisted",
                    account=value
                )
                self.nodes[0].process(created['request'])
                print("adjust user status: fail")
            except LogosRPCError as error:
                print(error)

        for key, value in {'empty':'', 'illegal':'unwhitelisted'}.items(): #capital works
            try:
                print("adjust user status: {} status".format(key))
                created = self.nodes[0].block_create_adjust_user_status(
                    key=self.account_list[1]['private'],
                    previous=prev,
                    token_id=coin['token_id'],
                    status=value,
                    account=self.account_list[1]['account']
                )
                self.nodes[0].process(created['request'])
                print("adjust user status: fail")
            except LogosRPCError as error:
                print(error)

        for item in ['whitelisted', 'frozen']:
            try:
                print("adjust user status: no privilege {}".format(item))
                created = self.nodes[0].block_create_adjust_user_status(
                    key=self.account_list[2]['private'],
                    previous=prev,
                    token_id=coin['token_id'],
                    status=item,
                    account=self.account_list[1]['account']
                )
                self.nodes[0].process(created['request'])
                print("adjust user status: fail")
            except LogosRPCError as error:
                print(error)

        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TADJUSE1',
            name='testadjustuserstatus1',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["withdraw_fee", "issuance", "burn","distribute", "whitelist", "freeze"]},
            {"account":self.account_list[2]['account'], "privileges": ["revoke"]}],
            settings=["revoke"]
        )
        coin = eval(created['request'])
        prev = created['hash']
        token_account = qlmdb3.toaccount(qlmdb3.unhexlify(coin['token_id']))
        self.nodes[0].process(created['request'])
        sleep(10)

        gen_info = self.nodes[0].account_info()
        sleep(6)
        created = self.nodes[0].block_create(
            previous=gen_info['frontier'],
            transactions=[{"destination":token_account, "amount":"1000000000000000000000000000000000000"}]
        )
        self.nodes[0].process(created['request'])
        sleep(10)

        for item in ['whitelisted', 'frozen']:
            try:
                print("adjust user status: no setting {}".format(item))
                created = self.nodes[0].block_create_adjust_user_status(
                    key=self.account_list[1]['private'],
                    previous=prev,
                    token_id=coin['token_id'],
                    status=item,
                    account=self.account_list[1]['account']
                )
                self.nodes[0].process(created['request'])
                print("adjust user status: fail")
            except LogosRPCError as error:
                print(error)
                
    def test_adjust_fee(self):
        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        print("creating valid token account")
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TADJFEE',
            name='testadjustfee',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["distribute", "adjust_fee"]},
            {"account":self.account_list[2]['account'], "privileges": ["revoke"]}],
            settings=["revoke", "adjust_fee"]
        )
        coin = eval(created['request'])
        prev = created['hash']
        token_account = qlmdb3.toaccount(qlmdb3.unhexlify(coin['token_id']))
        self.nodes[0].process(created['request'])
        sleep(10)

        gen_info = self.nodes[0].account_info()
        sleep(6)
        created = self.nodes[0].block_create(
            previous=gen_info['frontier'],
            transactions=[{"destination":token_account, "amount":"1000000000000000000000000000000000000"}]
        )
        self.nodes[0].process(created['request'])
        sleep(10)

        for key, value in {'empty':'', 'not valid':'distribute', 'capitalized':'Percentage'}.items():
            try:
                print("adjust fee: {} fee_type".format(key))
                created = self.nodes[0].block_create_adjust_fee(
                    key=self.account_list[1]['private'],
                    previous=prev,
                    token_id=coin['token_id'],
                    fee_type=value,
                    fee_rate='10'
                )
                self.nodes[0].process(created['request'])
                print("adjust fee: fail")
            except LogosRPCError as error:
                print(error)

        for key, value in {'empty':'', 'decimal':'50.1', 'negative':'-10', 'excessive':'101'}.items():
            try:
                print("adjust fee: {} fee_rate".format(key))
                created = self.nodes[0].block_create_adjust_fee(
                    key=self.account_list[1]['private'],
                    previous=prev,
                    token_id=coin['token_id'],
                    fee_type='percentage',
                    fee_rate=value
                )
                self.nodes[0].process(created['request'])
                print("adjust fee: fail")
            except LogosRPCError as error:
                print(error)

        try:
            print("adjust fee: no privilege")
            created = self.nodes[0].block_create_adjust_fee(
            key=self.account_list[2]['private'],
                    previous=prev,
                    token_id=coin['token_id'],
                    fee_type='percentage',
                    fee_rate='10'
            )
            self.nodes[0].process(created['request'])
            print("adjust fee: fail")
        except LogosRPCError as error:
            print(error)

        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        print("creating valid token account")
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TADJFEE',
            name='testadjustfee',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["distribute", "adjust_fee"]},
            {"account":self.account_list[2]['account'], "privileges": ["revoke"]}],
            settings=["revoke"]
        )
        coin = eval(created['request'])
        prev = created['hash']
        token_account = qlmdb3.toaccount(qlmdb3.unhexlify(coin['token_id']))
        self.nodes[0].process(created['request'])
        sleep(10)

        gen_info = self.nodes[0].account_info()
        sleep(6)
        created = self.nodes[0].block_create(
            previous=gen_info['frontier'],
            transactions=[{"destination":token_account, "amount":"1000000000000000000000000000000000000"}]
        )
        self.nodes[0].process(created['request'])
        sleep(10)
        
        try:
            print("adjust fee: no setting")
            created = self.nodes[0].block_create_adjust_fee(
            key=self.account_list[1]['private'],
                    previous=prev,
                    token_id=coin['token_id'],
                    fee_type='percentage',
                    fee_rate='10'
            )
            self.nodes[0].process(created['request'])
            print("adjust fee: fail")
        except LogosRPCError as error:
            print(error)

    def test_update_issuer_info(self):
        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        print("creating valid token account")
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TINFO',
            name='testupinfo',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["issuance", "burn","distribute", "update_issuer_info"]},
            {"account":self.account_list[2]['account'], "privileges": ["distribute"]}],
            settings=["revoke", "modify_issuance"]
        )
        print(created)
        coin = eval(created['request'])
        prev = created['hash']
        self.nodes[0].process(created['request'])
        sleep(10)
        
        try:
            print("update issuer info: long info")
            created = self.nodes[0].block_create_update_issuer_info(
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                new_info="a"*512+"b"
            )
            self.nodes[0].process(created['request'])
            print('update issuer info: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("update issuer info: no privileges")
            created = self.nodes[0].block_create_update_issuer_info(
                key=self.account_list[2]['private'],
                previous=prev,
                token_id=coin['token_id'],
                new_info="a"
            )
            self.nodes[0].process(created['request'])
            print('update issuer info: fails')
        except LogosRPCError as error:
            print(error)
        
        
    def test_update_controller(self):
        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TUPCONT',
            name='testupdatecontroller',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["distribute", "update_controller"]},
                         {"account":self.account_list[2]['account'], "privileges": ["revoke"]}],
            settings=["revoke"]
        )
        coin = eval(created['request'])
        prev = created['hash']
        token_account = qlmdb3.toaccount(qlmdb3.unhexlify(coin['token_id']))
        self.nodes[0].process(created['request'])
        sleep(10)

        gen_info = self.nodes[0].account_info()
        sleep(6)
        created = self.nodes[0].block_create(
            previous=gen_info['frontier'],
            transactions=[{"destination":token_account, "amount":"1000000000000000000000000000000000000"}]
        )
        self.nodes[0].process(created['request'])
        sleep(10)

        for key, value in {'empty':'','not valid':'delete','uppercase':'Add'}.items():
            try:
                print('update controller: {} action')
                created = self.nodes[0].block_create_update_controller(
                    key=self.account_list[1]['private'],
                    previous=prev,
                    action=value,
                    token_id=coin['token_id'],
                    controller={"account":self.account_list[2]['account'], "privileges":['distribute']}
                )
                self.nodes[0].process(created['request'])
                print('update controller: fail')
            except LogosRPCError as error:
                print(error)
                
        try:
            print('update controller: empty controller')
            created = self.nodes[0].block_create_update_controller(
                key=self.account_list[1]['private'],
                previous=prev,
                action='add',
                token_id=coin['token_id'],
                controller={}
            )
            self.nodes[0].process(created['request'])
            print('update controller: fail')
        except LogosRPCError as error:
            print(error)

        try:
            print('update controller: not valid controller')
            created = self.nodes[0].block_create_update_controller(
                key=self.account_list[1]['private'],
                previous=prev,
                action='add',
                token_id=coin['token_id'],
                controller={"account":self.account_list[2]['account'], "privileges":['modify_distribute']}
            )
            self.nodes[0].process(created['request'])
            print('update controller: fail')
        except LogosRPCError as error:
            print(error)

        try:
            print('update controller: duplicate controller')
            created = self.nodes[0].block_create_update_controller(
                key=self.account_list[1]['private'],
                previous=prev,
                action='add',
                token_id=coin['token_id'],
                controller={"account":self.account_list[2]['account'], "privileges":['distribute, distribute']}
            )
            self.nodes[0].process(created['request'])
            print('update controller: fail')
        except LogosRPCError as error:
            print(error)

        try:
            print('update controller: no privilege')
            created = self.nodes[0].block_create_update_controller(
                key=self.account_list[2]['private'],
                previous=prev,
                action='add',
                token_id=coin['token_id'],
                controller={"account":self.account_list[2]['account'], "privileges":['distribute']}
            )
            self.nodes[0].process(created['request'])
            print('update controller: fail')
        except LogosRPCError as error:
            print(error)
        
        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TUPCONT1',
            name='testupdatecontroller1',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["distribute", "update_controller"]},
                         {"account":self.account_list[2]['account'], "privileges": ["revoke"]},
                         {"account":self.account_list[3]['account'], "privileges": ["revoke"]},
                         {"account":self.account_list[4]['account'], "privileges": ["revoke"]},
                         {"account":self.account_list[5]['account'], "privileges": ["revoke"]},
                         {"account":self.account_list[6]['account'], "privileges": ["revoke"]},
                         {"account":self.account_list[7]['account'], "privileges": ["revoke"]},
                         {"account":self.account_list[8]['account'], "privileges": ["revoke"]},
                         {"account":self.account_list[9]['account'], "privileges": ["revoke"]},
                         {"account":self.account_list[10]['account'], "privileges": ["revoke"]}],
            settings=["revoke"]
        )
        coin = eval(created['request'])
        prev = created['hash']
        token_account = qlmdb3.toaccount(qlmdb3.unhexlify(coin['token_id']))
        self.nodes[0].process(created['request'])
        sleep(10)

        gen_info = self.nodes[0].account_info()
        sleep(6)
        created = self.nodes[0].block_create(
            previous=gen_info['frontier'],
            transactions=[{"destination":token_account, "amount":"1000000000000000000000000000000000000"}]
        )
        self.nodes[0].process(created['request'])
        sleep(10)

        try:
            print('update controller: max controller')
            created = self.nodes[0].block_create_update_controller(
                key=self.account_list[1]['private'],
                previous=prev,
                action='add',
                token_id=coin['token_id'],
                controller={"account":self.account_list[11]['account'], "privileges":['distribute']}
            )
            self.nodes[0].process(created['request'])
            print('update controller: fail')
        except LogosRPCError as error:
            print(error)
                
    def test_burn(self):
        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        print("creating valid token account")
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TBURN',
            name='testburn',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["issuance", "burn","distribute"]},
            {"account":self.account_list[2]['account'], "privileges": ["distribute"]}],
            settings=["revoke", "modify_issuance"]
        )
        print(created)
        coin = eval(created['request'])
        prev = created['hash']
        self.nodes[0].process(created['request'])
        sleep(10)
        
        try:
            created = self.nodes[0].block_create_burn(
                type="burn",
                key=self.account_list[1]['private'],
                previous=prev,
                amount="100000",
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
        except LogosRPCError as error:
            print(error)

        try:
            print("burn: decimal amount")
            created = self.nodes[0].block_create_burn(
                type="burn",
                key=self.account_list[1]['private'],
                previous=prev,
                amount="100000.12",
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print('burn: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("burn: negative amount")
            created = self.nodes[0].block_create_burn(
                type="burn",
                key=self.account_list[1]['private'],
                previous=prev,
                amount="-100000",
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print('burn: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("burn: empty amount")
            created = self.nodes[0].block_create_burn(
                type="burn",
                key=self.account_list[1]['private'],
                previous=prev,
                amount="",
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print('burn: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("burn: no privilege")
            created = self.nodes[0].block_create_burn(
                type="burn",
                key=self.account_list[2]['private'],
                previous=prev,
                amount="100",
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print('burn: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("burn: more than total")
            created = self.nodes[0].block_create_burn(
                type="burn",
                key=self.account_list[1]['private'],
                previous=prev,
                amount="2200000000000000",
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print('burn: fails')
        except LogosRPCError as error:
            print(error)

    def test_distribute(self):
        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        print("creating valid token account")
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TDIST',
            name='testdistribute',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["issuance", "burn","distribute"]},
            {"account":self.account_list[2]['account'], "privileges": ["revoke"]}],
            settings=["revoke", "modify_issuance"]
        )
        print(created)
        coin = eval(created['request'])
        prev = created['hash']
        self.nodes[0].process(created['request'])
        sleep(10)

        print("valid")
        created = self.nodes[0].block_create_tokreq(
            type="distribute",
            key=self.account_list[1]['private'],
            previous=prev,
            token_id=coin['token_id'],
            transaction={"destination" : self.account_list[1]['account'], "amount": "100000000000000" }
        )
        self.nodes[0].process(created['request'])

        sleep(7)
        prev = created['hash']
        print("PREV = {}".format(prev))
        '''
        try:
            print("distribute: decimal amount")
            created = self.nodes[0].block_create_tokreq(
                type="distribute",
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                transaction={"destination" : self.account_list[1]['account'], "amount": "20000000000.123" }
            )
            print(created)
            self.nodes[0].process(created['request'])
            print('distribute: fails')
        except LogosRPCError as error:
            print(error)

        prev = created['hash']
        print("PREV = {}".format(prev))
        '''
        try:
            print("distribute: negative amount")
            created = self.nodes[0].block_create_tokreq(
                type="distribute",
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                transaction={"destination" : self.account_list[1]['account'], "amount": "-100000000000000" }
            )
            self.nodes[0].process(created['request'])
            print('distribute: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("distribute: empty amount")
            created = self.nodes[0].block_create_tokreq(
                type="distribute",
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                transaction={"destination" : self.account_list[1]['account'], "amount": "" }
            )
            self.nodes[0].process(created['request'])
            print('distribute: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("distribute: public key destination")
            created = self.nodes[0].block_create_tokreq(
                type="distribute",
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                transaction={"destination" : self.account_list[1]['public'], "amount": "100000000000000" }
            )
            self.nodes[0].process(created['request'])
            print('distribute: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("distribute: empty destination")
            created = self.nodes[0].block_create_tokreq(
                type="distribute",
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                transaction={"destination": "", "amount": "100000000000000" }
            )
            self.nodes[0].process(created['request'])
            print('distribute: fails')
        except LogosRPCError as error:
            print(error)


        try:
            print("distribute: no distribute privilege")
            created = self.nodes[0].block_create_tokreq(
                type="distribute",
                key=self.account_list[2]['private'],
                previous=prev,
                token_id=coin['token_id'],
                transaction={"destination": self.account_list[1]['account'], "amount": "10999999" }
            )
            self.nodes[0].process(created['request'])
            print('distribute: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("distribute: more than max")
            created = self.nodes[0].block_create_tokreq(
                type="distribute",
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                transaction={"destination": self.account_list[1]['account'], "amount": "2200000000000000" }
            )
            self.nodes[0].process(created['request'])
            print('distribute: fails')
        except LogosRPCError as error:
            print(error)

        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        print("creating valid token account")
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TDIST1',
            name='testdistribute1',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["issuance", "burn","distribute"]},
            {"account":self.account_list[2]['account'], "privileges": ["revoke"]}],
            settings=["revoke", "modify_issuance"]
        )
        print(created)
        coin = eval(created['request'])
        prev = created['hash']
        self.nodes[0].process(created['request'])
        sleep(10)
            
    def test_withdraw_fee(self):
        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        print("creating valid token account")
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TWFEE',
            name='testwithdrawfee',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["withdraw_fee", "issuance", "burn","distribute"]},
            {"account":self.account_list[2]['account'], "privileges": ["revoke"]}],
            settings=["revoke", "modify_issuance"]
        )
        print(created)
        coin = eval(created['request'])
        prev = created['hash']
        token_account = qlmdb3.toaccount(qlmdb3.unhexlify(coin['token_id']))
        self.nodes[0].process(created['request'])
        sleep(10)

        gen_info = self.nodes[0].account_info()
        sleep(6)
        
        created = self.nodes[0].block_create(
            previous=gen_info['frontier'],
            transactions=[{"destination":token_account, "amount":"1000000000000000000000000000000000000"}]
        )
        
        self.nodes[0].process(created['request'])

        sleep(10)

        print("valid distribute")
        created = self.nodes[0].block_create_tokreq(
            type="distribute",
            key=self.account_list[1]['private'],
            previous=prev,
            token_id=coin['token_id'],
            transaction={"destination" : self.account_list[1]['account'], "amount": "100000000000000" }
        )
        self.nodes[0].process(created['request'])

        sleep(10)
        created = self.nodes[0].block_create_token_send(
            type="token_send",
            key=self.account_list[1]['private'],
            previous=prev,
            transactions=[{"destination":self.account_list[2]['account'], "amount":"2000000"}],
            token_id=coin['token_id']
        )
        prev = created['hash']
        print(prev)
        self.nodes[0].process(created['request'])
        sleep(10)
        '''
        try:
            print("withdraw fee: decimal amount")
            created = self.nodes[0].block_create_withdraw(
                type="withdraw_fee",
                key=self.account_list[1]['private'],
                previous=prev,
                transaction={"destination":self.account_list[2]['account'], "amount":"20.12"},
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print('withdraw fee: fails')
        except LogosRPCError as error:
            print(error)
        '''
        try:
            print("withdraw fee: negative amount")
            created = self.nodes[0].block_create_withdraw(
                type="withdraw_fee",
                key=self.account_list[1]['private'],
                previous=prev,
                transaction={"destination":self.account_list[2]['account'], "amount":"-20"},
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print('withdraw fee: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("withdraw fee: empty amount")
            created = self.nodes[0].block_create_withdraw(
                type="withdraw_fee",
                key=self.account_list[1]['private'],
                previous=prev,
                transaction={"destination":self.account_list[2]['account'], "amount":""},
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print('withdraw fee: fails')
        except LogosRPCError as error:
            print(error)
            
        try:
            print("withdraw fee: empty destination")
            created = self.nodes[0].block_create_withdraw(
                type="withdraw_fee",
                key=self.account_list[1]['private'],
                previous=prev,
                transaction={"destination":"", "amount":"20"},
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print('withdraw fee: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("withdraw fee: publickey destination")
            created = self.nodes[0].block_create_withdraw(
                type="withdraw_fee",
                key=self.account_list[1]['private'],
                previous=prev,
                transaction={"destination":self.account_list[2]['public'], "amount":"20"},
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print('withdraw fee: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("withdraw fee: no privilege")
            created = self.nodes[0].block_create_withdraw(
                type="withdraw_fee",
                key=self.account_list[2]['private'],
                previous=prev,
                transaction={"destination":self.account_list[2]['account'], "amount":"20"},
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print('withdraw fee: fails')
        except LogosRPCError as error:
            print(error)

        try:
            print("withdraw fee: excessive withdraw")
            created = self.nodes[0].block_create_withdraw(
                type="withdraw_fee",
                key=self.account_list[1]['private'],
                previous=prev,
                transaction={"destination":self.account_list[2]['account'], "amount":"200000000000000000000000000"},
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print('withdraw fee: fails')
        except LogosRPCError as error:
            print(error)

    def test_withdraw_logos(self):
        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        print("creating valid token account")
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TWLOGOS',
            name='testwithdrawlogos',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["withdraw_logos", "withdraw_fee", "issuance", "burn","distribute"]},
            {"account":self.account_list[2]['account'], "privileges": ["revoke"]}],
            settings=["revoke", "modify_issuance"]
        )
        print(created)
        coin = eval(created['request'])
        prev = created['hash']
        token_account = qlmdb3.toaccount(qlmdb3.unhexlify(coin['token_id']))
        self.nodes[0].process(created['request'])
        sleep(10)

        gen_info = self.nodes[0].account_info()
        sleep(6)
        
        created = self.nodes[0].block_create(
            previous=gen_info['frontier'],
            transactions=[{"destination":token_account, "amount":"1000000000000000000000000000000000000"}]
        )
        
        self.nodes[0].process(created['request'])

        sleep(10)

        created = self.nodes[0].block_create_withdraw(
            type="withdraw_logos",
            key=self.account_list[1]['private'],
            previous=prev,
            transaction={"destination":self.account_list[2]['account'], "amount":"300000000000000"},
            token_id=coin['token_id']
        )
        self.nodes[0].process(created['request'])
        
        try:
            print("withdraw logos: decimal amount")
            created = self.nodes[0].block_create_withdraw(
                type="withdraw_logos",
                key=self.account_list[1]['private'],
                previous=prev,
                transaction={"destination":self.account_list[2]['account'], "amount":"300000.123"},
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print("withdraw logos: fail")
        except LogosRPCError as error:
            print(error)

        try:
            print("withdraw logos: negative amount")
            created = self.nodes[0].block_create_withdraw(
                type="withdraw_logos",
                key=self.account_list[1]['private'],
                previous=prev,
                transaction={"destination":self.account_list[2]['account'], "amount":"-300000"},
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print("withdraw logos: fail")
        except LogosRPCError as error:
            print(error)

        try:
            print("withdraw logos: empty amount")
            created = self.nodes[0].block_create_withdraw(
                type="withdraw_logos",
                key=self.account_list[1]['private'],
                previous=prev,
                transaction={"destination":self.account_list[2]['account'], "amount":""},
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print("withdraw logos: fail")
        except LogosRPCError as error:
            print(error)

        try:
            print("withdraw logos: empty destination")
            created = self.nodes[0].block_create_withdraw(
                type="withdraw_logos",
                key=self.account_list[1]['private'],
                previous=prev,
                transaction={"destination":"", "amount":"3000000"},
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print("withdraw logos: fail")
        except LogosRPCError as error:
            print(error)
            
        try:
            print("withdraw logos: publickey destination")
            created = self.nodes[0].block_create_withdraw(
                type="withdraw_logos",
                key=self.account_list[1]['private'],
                previous=prev,
                transaction={"destination":self.account_list[2]['public'], "amount":"3000000"},
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print("withdraw logos: fail")
        except LogosRPCError as error:
            print(error)

        try:
            print("withdraw logos: no privilege")
            created = self.nodes[0].block_create_withdraw(
                type="withdraw_logos",
                key=self.account_list[2]['private'],
                previous=prev,
                transaction={"destination":self.account_list[1]['account'], "amount":"300000"},
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print("withdraw logos: fail")
        except LogosRPCError as error:
            print(error)

        try:
            print("withdraw logos: excessive withdraw")
            created = self.nodes[0].block_create_withdraw(
                type="withdraw_logos",
                key=self.account_list[1]['private'],
                previous=prev,
                transaction={"destination":self.account_list[2]['account'], "amount":"1000000000000000000000000000000000001"},
                token_id=coin['token_id']
            )
            self.nodes[0].process(created['request'])
            print("withdraw logos: fail")
        except LogosRPCError as error:
            print(error)

    def test_token_send(self):
        malformed_amt = {'decimal':'1234.1', 'negative':'-1234', 'empty':''}
        malformed_dest = {'empty':'', 'publickey':'E41C9CFF2C98A049519C516E275F216A22A2C28290322A6504679F7C323F63D6'}
        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        print("creating valid token account")
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TTOKSEND',
            name='testtokensend',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["withdraw_fee", "issuance", "burn","distribute"]},
            {"account":self.account_list[2]['account'], "privileges": ["revoke"]}],
            settings=["revoke", "modify_issuance"]
        )
        print(created)
        coin = eval(created['request'])
        prev = created['hash']
        token_account = qlmdb3.toaccount(qlmdb3.unhexlify(coin['token_id']))
        self.nodes[0].process(created['request'])
        sleep(10)

        gen_info = self.nodes[0].account_info()
        sleep(6)
        created = self.nodes[0].block_create(
            previous=gen_info['frontier'],
            transactions=[{"destination":token_account, "amount":"1000000000000000000000000000000000000"}]
        )
        
        self.nodes[0].process(created['request'])

        sleep(10)

        print("valid distribute")
        for i in range(2):
            created = self.nodes[0].block_create_tokreq(
                type="distribute",
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                transaction={"destination" : self.account_list[i]['account'], "amount": "100000000000000" }
            )
            self.nodes[0].process(created['request'])
            sleep(7)

        '''
        for key, value in malformed_amt.items():
            try:
                print("token send: {} amount".format(key))
                created = self.nodes[0].block_create_token_send(
                    key=self.account_list[1]['private'],
                    previous=prev,
                    token_id=coin['token_id'],
                    transactions=[{"destination":self.account_list[2]['account'], "amount":value }]
                )
                self.nodes[0].process(created['request'])
                print("token send: fail")
            except LogosRPCError as error:
                print(error)
        '''
        for key, value in malformed_dest.items():
            try:
                print("token send: {} destination".format(key))
                created = self.nodes[0].block_create_token_send(
                    key=self.account_list[1]['private'],
                    previous=prev,
                    token_id=coin['token_id'],
                    transactions=[{"destination":value, "amount":"10000" }]
                )
                self.nodes[0].process(created['request'])
                print("token send: fail")
            except LogosRPCError as error:
                print(error)
        '''
        try:
            print("token send: empty transaction")
            created = self.nodes[0].block_create_token_send(
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                transactions=[]
            )
            self.nodes[0].process(created['request'])
            print("token send: fail")
        except LogosRPCError as error:
            print(error)
        '''
        
        try:
            print("token send: too many transaction")
            created = self.nodes[0].block_create_token_send(
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                transactions=[{"destination":self.account_list[3]['account'], "amount":"100000"},
                              {"destination":self.account_list[4]['account'], "amount":"100000"},
                              {"destination":self.account_list[5]['account'], "amount":"100000"},
                              {"destination":self.account_list[6]['account'], "amount":"100000"},
                              {"destination":self.account_list[7]['account'], "amount":"100000"},
                              {"destination":self.account_list[8]['account'], "amount":"100000"},
                              {"destination":self.account_list[9]['account'], "amount":"100000"},
                              {"destination":self.account_list[10]['account'], "amount":"100000"},
                              {"destination":self.account_list[11]['account'], "amount":"100000"}]
            )
            self.nodes[0].process(created['request'])
            print("token send: fail")
        except LogosRPCError as error:
            print(error)
        
        try:
            print("token send: excessive send amount")
            created = self.nodes[0].block_create_token_send(
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                transactions=[{"destination":self.account_list[2]['account'], "amount":"100000000000001"}]
            )
            self.nodes[0].process(created['request'])
            print("token send: fail")
        except LogosRPCError as error:
            print(error)

        '''
        try:
            print("token send: below min fee")
            created = self.nodes[0].block_create_token_send(
                key=self.account_list[1]['private'],
                previous=prev,
                fee='0',
                token_id=coin['token_id'],
                transactions=[{"destination":self.account_list[2]['account'], "amount":"10000"}]
            )
            self.nodes[0].process(created['request'])
            print("token send: fail")
        except LogosRPCError as error:
            print(error)
        '''
        prev = self.nodes[0].account_info(self.account_list[1]['account'])['frontier']
        print("creating valid token account")
        created = self.nodes[0].block_create_issuance(
            key=self.account_list[1]['private'],
            previous=prev,
            symbol='TTKSEND1',
            name='testtokensend1',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["withdraw_fee", "issuance", "burn","distribute", "whitelist", "freeze"]},
            {"account":self.account_list[2]['account'], "privileges": ["revoke"]}],
            settings=["revoke", "modify_issuance", "whitelist", "freeze"]
        )
        print(created)
        coin1 = eval(created['request'])
        prev = created['hash']
        token_account1 = qlmdb3.toaccount(qlmdb3.unhexlify(coin1['token_id']))
        self.nodes[0].process(created['request'])
        sleep(10)

        gen_info = self.nodes[0].account_info()
        sleep(6)
        created = self.nodes[0].block_create(
            previous=gen_info['frontier'],
            transactions=[{"destination":token_account1, "amount":"1000000000000000000000000000000000000"}]
        )
        
        self.nodes[0].process(created['request'])

        sleep(10)
        
        try:
            print("token send: send to foreign tokenaccount")
            created = self.nodes[0].block_create_token_send(
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin['token_id'],
                transactions=[{"destination":token_account1, "amount":"10000"}]
            )
            self.nodes[0].process(created['request'])
            print(created)
            print("token send: fail")
        except LogosRPCError as error:
            print(error)

        created = self.nodes[0].block_create_adjust_user_status(
            key=self.account_list[1]['private'],
            previous=prev,
            token_id=coin1['token_id'],
            status="whitelisted",
            account=self.account_list[1]['account']
        )
        self.nodes[0].process(created['request'])
        sleep(7)

        created = self.nodes[0].block_create_tokreq(
            type="distribute",
            key=self.account_list[1]['private'],
            previous=prev,
            token_id=coin1['token_id'],
            transaction={"destination" : self.account_list[i]['account'], "amount": "100000000000000" }
        )
        self.nodes[0].process(created['request'])
        sleep(7)
        print(self.nodes[0].account_info(self.account_list[1]['account']))

        try:
            print("token send: send to non whitelisted account")
            created = self.nodes[0].block_create_token_send(
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin1['token_id'],
                transactions=[{"destination":self.account_list[2]['account'], "amount":"10000"}]
            )
            self.nodes[0].process(created['request'])
            print("token send: fail")
        except LogosRPCError as error:
            print(error)

        
        created = self.nodes[0].block_create_adjust_user_status(
            key=self.account_list[1]['private'],
            previous=prev,
            token_id=coin1['token_id'],
            status="whitelisted",
            account=self.account_list[3]['account']
        )
        self.nodes[0].process(created['request'])
        sleep(7)

        created = self.nodes[0].block_create_adjust_user_status(
            key=self.account_list[1]['private'],
            previous=prev,
            token_id=coin1['token_id'],
            status="frozen",
            account=self.account_list[3]['account']
        )
        self.nodes[0].process(created['request'])
        sleep(7)

        try:
            print("token send: send to frozen account")
            created = self.nodes[0].block_create_token_send(
                key=self.account_list[1]['private'],
                previous=prev,
                token_id=coin1['token_id'],
                transactions=[{"destination":self.account_list[3]['account'], "amount":"10000"}]
            )
            self.nodes[0].process(created['request'])
            print("token send: fail")
        except LogosRPCError as error:
            print(error)

        
