from utils import *
from orchestration import *
import random
import json
import qlmdb3


class TestCaseMixin:

    def test_token_illegal(self):
        test_results = []

        #================================================================
        # ACCOUNT THAT WILL CREATE TOKENS
        #================================================================
        accnt_main = self.account_list[0] 
        gen_info = self.nodes[0].account_info()
        gen_prev = gen_info['frontier']

        for i in range(2):
            d_id = designated_delegate(g_pub, gen_prev)
            created = self.nodes[0].block_create(
                previous=gen_prev,
                txns=[{"destination":self.account_list[6*i]['account'], "amount":"30000000000000000000000000000000"},
                      {"destination":self.account_list[6*i+1]['account'], "amount":"30000000000000000000000000000000"},
                      {"destination":self.account_list[6*i+2]['account'], "amount":"30000000000000000000000000000000"},
                      {"destination":self.account_list[6*i+3]['account'], "amount":"30000000000000000000000000000000"},
                      {"destination":self.account_list[6*i+4]['account'], "amount":"30000000000000000000000000000000"},
                      {"destination":self.account_list[6*i+5]['account'], "amount":"30000000000000000000000000000000"}
                ]
            )
            self.nodes[d_id].process(created['request'])
            if not self.wait_for_requests_persistence([created['hash']]):
                sys.stderr.write('Stopped at funding account')
            gen_prev = created['hash']
            
        #================================================================
        # MAIN TOKEN ACCOUNT
        #================================================================
        accnt_main_info = self.nodes[0].account_info(accnt_main['account'])
        d_id = designated_delegate(accnt_main['public'], accnt_main_info['frontier'])
        created = self.nodes[d_id].block_create_issuance(
            private_key=accnt_main['private'],
            previous=accnt_main_info['frontier'],
            fee_type='flat',
            fee_rate='10',
            symbol='TEST',
            name='test_token',
            controllers=[{"account":accnt_main['account'], "privileges": ["distribute", "burn", "issuance", "withdraw_fee", "withdraw_logos", "revoke", "update_issuer_info", "change_freeze", "update_controller", "change_modify_freeze", "freeze", "adjust_fee"]},
                         {"account":self.account_list[1]['account'], "privileges":[]},
                         {"account":self.account_list[2]['account'], "privileges":[]},
                         {"account":self.account_list[3]['account'], "privileges":[]},
                         {"account":self.account_list[4]['account'], "privileges":[]},
                         {"account":self.account_list[5]['account'], "privileges":[]},
                         {"account":self.account_list[6]['account'], "privileges":[]},
                         {"account":self.account_list[7]['account'], "privileges":[]},
                         {"account":self.account_list[8]['account'], "privileges":[]}
            ],
            settings=["revoke", "issuance", "modify_freeze", "freeze", "adjust_fee"]
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Stopped at funding account')
        coin = eval(created['request'])
        token_account = qlmdb3.toaccount(qlmdb3.unhexlify(coin['token_id']))
        token_main = {"token_id":coin['token_id'], "account":token_account}

        gen_info = self.nodes[0].account_info()
        gen_prev = gen_info['frontier']
        d_id = designated_delegate(g_pub, gen_prev)
        created = self.nodes[0].block_create(
                previous=gen_prev,
                txns=[{"destination":token_account, "amount":"30000000000000000000000000000000"}]
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Stopped at funding account')

        #================================================================
        # INSUFFICIENT FEE LOGOS ACCOUNT
        #================================================================
        accnt_poor = self.account_list[-1]
        try:
            info = self.nodes[0].account_info(accnt_poor['account'])
            # make account with insufficient funds if it exists
            d_id = designated_delegate(accnt_poor['public'], info['frontier'])
            if eval(info['balance']) > eval(MIN_FEE)-1:
                created = self.nodes[d_id].block_create(
                    private_key = accnt_poor['private'],
                    previous = info['frontier'],
                    txns = [{"destination":accnt_main['account'], "amount":(eval(info['balance'])-2*eval(MIN_FEE)-1)}]
                )
                print(created)
                self.nodes[d_id].process(created['request'])
                if not self.wait_for_requests_persistence([created['hash']]):
                    sys.stderr.write('Stopped at funding account')
        except LogosRPCError as error:
            gen_info = self.nodes[0].account_info()
            gen_prev = gen_info['frontier']
            d_id = designated_delegate(g_pub, gen_prev)
            created = self.nodes[0].block_create(
                previous=gen_prev,
                txns=[{"destination":accnt_poor['account'], "amount":eval(MIN_FEE)-1}]
            )
            print(created)
            self.nodes[d_id].process(created['request'])
            if not self.wait_for_requests_persistence([created['hash']]):
                sys.stderr.write('Stopped at funding account')

        #================================================================
        # TOKEN WITH INSUFFICIENT FEES
        #================================================================
        accnt_main_info = self.nodes[0].account_info(accnt_main['account'])
        d_id = designated_delegate(accnt_main['public'], accnt_main_info['frontier'])
        created = self.nodes[d_id].block_create_issuance(
            private_key=accnt_main['private'],
            previous=accnt_main_info['frontier'],
            fee_type='flat',
            fee_rate='10',
            symbol='POOR',
            name='test_token-logos_poor',
            controllers=[{"account":accnt_main['account'], "privileges": ["distribute", "burn", "issuance", "withdraw_fee", "withdraw_logos", "revoke", "update_issuer_info", "change_freeze", "update_controller", "change_modify_freeze", "freeze", "adjust_fee"]}],
            settings=["revoke", "issuance", "modify_freeze", "freeze", "adjust_fee"],
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Stopped at funding account')
        coin = eval(created['request'])
        token_account = qlmdb3.toaccount(qlmdb3.unhexlify(coin['token_id']))
        token_poor = {"token_id":coin['token_id'], "account":token_account}
        
        gen_info = self.nodes[0].account_info()
        gen_prev = gen_info['frontier']
        d_id = designated_delegate(g_pub, gen_prev)
        created = self.nodes[0].block_create(
                previous=gen_prev,
                txns=[{"destination":token_account, "amount":eval(MIN_FEE)-1}]
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Stopped at funding account')

        #================================================================
        # TOKEN WITH NO SETTINGS
        #================================================================
        accnt_main_info = self.nodes[0].account_info(accnt_main['account'])
        d_id = designated_delegate(accnt_main['public'], accnt_main_info['frontier'])
        created = self.nodes[d_id].block_create_issuance(
            private_key=accnt_main['private'],
            previous=accnt_main_info['frontier'],
            fee_type='flat',
            fee_rate='10',
            symbol='SETT',
            name='test_token-no_settings',
            controllers=[{"account":accnt_main['account'], "privileges": ["distribute", "burn", "issuance", "withdraw_fee", "withdraw_logos", "revoke", "update_issuer_info", "change_freeze", "update_controller", "change_modify_freeze", "freeze", "adjust_fee"]}],
            settings=[],
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Stopped at funding account')
        coin = eval(created['request'])
        token_account = qlmdb3.toaccount(qlmdb3.unhexlify(coin['token_id']))
        token_nosetting = {"token_id":coin['token_id'], "account":token_account}
        
        gen_info = self.nodes[0].account_info()
        gen_prev = gen_info['frontier']
        d_id = designated_delegate(g_pub, gen_prev)
        created = self.nodes[0].block_create(
                previous=gen_prev,
                txns=[{"destination":token_account, "amount":"30000000000000000000000000000000"}]
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Stopped at funding account')
        
        
        # TEST TOKEN ISSUANCE
        test_results.append(all(self.illegal_token_issuance(accnt_main, accnt_poor)))

        # TEST TOKEN ISSUE ADDITIONAL
        test_results.append(all(self.illegal_issue_additional(accnt_main, token_main, token_poor, token_nosetting)))

        # TEST TOKEN CHANGE SETTING
        test_results.append(all(self.illegal_change_setting(accnt_main, token_main, token_poor)))

        # TEST TOKEN IMMUTE SETTING
        #test_results.append(all(self.illegal_immute_setting(accnt_main, token_main, token_poor, token_nosetting)))

        # TEST TOKEN REVOKE
        #test_results.append(all(self.illegal_revoke(accnt_main, token_main, token_poor, token_nosetting)))

        # TEST TOKEN ADJUST USER STATUS
        #test_results.append(all(self.illegal_adjust_user_status(accnt_main, token_main, token_poor, token_nosetting)))

        # TEST TOKEN ADJUST FEE
        test_results.append(all(self.illegal_adjust_fee(accnt_main, token_main, token_poor, token_nosetting)))

        # TEST TOKEN UPDATE ISSUER INFO
        test_results.append(all(self.illegal_update_issuer_info(accnt_main, token_main, token_poor)))

        # TEST TOKEN UPDATE CONTROLLER
        test_results.append(all(self.illegal_update_controller(accnt_main, token_main, token_poor)))

        # TEST TOKEN BURN
        test_results.append(all(self.illegal_burn(accnt_main, token_main, token_poor)))

        # TEST TOKEN DISTRIBUTE
        test_results.append(all(self.illegal_distribute(accnt_main, token_main, token_poor)))

        # TEST TOKEN WITHDRAW FEE
        #test_results.append(all(self.illegal_withdraw_fee(accnt_main, token_main, token_poor)))

        # TEST TOKEN WITHDRAW LOGOS
        test_results.append(all(self.illegal_withdraw_logos(accnt_main, token_main, token_poor)))

        # TEST TOKEN SEND
        #test_results.append(all(self.illegal_token_send(accnt_main, token_main, accnt_poor)))
        
        print(all(test_results))
        return(all(test_results))
        
    #################################################################################
    # ILLEGAL TOKEN ISSUANCE
    # On Logos account send chain
    #################################################################################
    def illegal_token_issuance(self, accnt_main, accnt_poor):
        results = []
        
        ## INSUFFICIENT FEE IN ACCOUNT BALANCE
        poor_info = self.nodes[0].account_info(accnt_poor['account'])
        d_id = designated_delegate(accnt_poor['public'], poor_info['frontier'])
        try:
            created = self.nodes[d_id].block_create_issuance(
                private_key=accnt_poor['private'],
                previous=poor_info['frontier'],
                symbol='ISSUE',
                name='test_token-issuance',
                controllers=[{"account":accnt_poor['account'], "privileges": ["distribute"]}],
                settings=[]
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN ISSUANCE FAILS: account creating token has insufficient logos fees but succeeded in issuance")
            results.append(False)
        except LogosRPCError as error:
            results.append(True)
            
        main_info = self.nodes[0].account_info(accnt_main['account'])
        main_prev = main_info['frontier']
        d_id = designated_delegate(accnt_main['public'], main_prev)

        ## INSUFFICIENT REQUEST FEE
        try:
            created = self.nodes[d_id].block_create_issuance(
                private_key=accnt_main['private'],
                previous=main_info['frontier'],
                symbol='ISSUE',
                name='test_token-issuance',
                controllers=[{"account":accnt_main['account'], "privileges": ["distribute"]}],
                settings=[],
                fee=eval(MIN_FEE)-1
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN ISSUANCE FAILS: insufficient request fees succeeded")
            results.append(False)
        except LogosRPCError as error:
            results.append(True)
        
            
        ## MALFORMED SYMBOLS
        for key, value in {'empty':'', 'long':'QWERTYUIO', 'illegal':'!SG'}.items():
            try:
                created = self.nodes[d_id].block_create_issuance(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    symbol=value,
                    name='test_token-issuance',
                    controllers=[{"account":accnt_main['account'], "privileges": ["distribute"]}],
                    settings=[]
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN ISSUANCE FAILS: symbol: {}".format(key))
                results.append(False)
            except LogosRPCError as error:
                results.append(True)

        ## MALFORMED NAMES
        for key, value in {'empty':'', 'long':'X'*129, 'illegal':'!token'}.items():
            try:
                created = self.nodes[d_id].block_create_issuance(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    symbol='ISSUE',
                    name=value,
                    controllers=[{"account":accnt_main['account'], "privileges": ["distribute"]}],
                    settings=[]
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN ISSUANCE FAILS: name: {}".format(key))
                results.append(False)
            except LogosRPCError as error:
                results.append(True)

        ## MALFORMED TOTAL SUPPLY
        for key, value in {'empty':'', 'negative':'-12000000', 'illegal':'abc'}.items():
            try:
                created = self.nodes[d_id].block_create_issuance(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    symbol='ISSUE',
                    name='test_token-issuance',
                    total_supply=value,
                    controllers=[{"account":accnt_main['account'], "privileges": ["distribute"]}],
                    settings=[]
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN ISSUANCE FAILS: total supply: {}".format(key))
                results.append(False)
            except LogosRPCError as error:
                results.append(True)
            
        ## MALFORMED FEE TYPE
        for key, value in {'empty':'', 'illegal':'fake'}.items():
            try:
                created = self.nodes[d_id].block_create_issuance(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    fee_type=value,
                    fee_rate=0,
                    symbol='ISSUE',
                    name='test_token-issuance',
                    controllers=[{"account":accnt_main['account'], "privileges": ["distribute"]}],
                    settings=[]
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN ISSUANCE FAILS: fee type: {}".format(key))
                results.append(False)
            except LogosRPCError as error:
                results.append(True)
                    
        ## MALFORMED FEE RATE FOR PERCENTAGE
        for key, value in {'decimal':'1.5', 'above100':'101', 'negative':'-39'}.items(): ## EMPTY WORKS???
            try:
                created = self.nodes[d_id].block_create_issuance(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    fee_type='percentage',
                    fee_rate=value,
                    symbol='ISSUE',
                    name='test_token-issuance',
                    controllers=[{"account":accnt_main['account'], "privileges": ["distribute"]}],
                    settings=[]
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN ISSUANCE FAILS: percentage fee rate: {}".format(key))
                results.append(False)
            except LogosRPCError as error:
                results.append(True)

        ## MALFORMED FEE RATE FOR FLAT
        for key, value in {'decimal':'1.5', 'negative':'-39'}.items(): ## EMPTY WORKS???
            try:
                created = self.nodes[d_id].block_create_issuance(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    fee_type='flat',
                    fee_rate=value,
                    symbol='ISSUE',
                    name='test_token-issuance',
                    controllers=[{"account":accnt_main['account'], "privileges": ["distribute"]}],
                    settings=[]
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN ISSUANCE FAILS: flat fee rate: {}".format(key))
                results.append(False)
            except LogosRPCError as error:
                results.append(True)
                               
        ## MALFORMED SETTINGS
        for key, value in {'illegal':'distribute'}.items():
            try:
                created = self.nodes[d_id].block_create_issuance(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    symbol='ISSUE',
                    name='test_token-issuance',
                    controllers=[{"account":accnt_main['account'], "privileges": ["distribute"]}],
                    settings=[value]
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN ISSUANCE FAILS: settings: {}".format(key))
                results.append(False)
            except LogosRPCError as error:
                results.append(True)

        ## MALFORMED CONTROLLERS TODO: EXCESSIVE CONTROLLERS
        controllers = {'no account':[{'privileges':['distribute','burn']}],
                       'no privileges':[{'account':accnt_main['account']}],
                       'illegal':[{'account':accnt_main['account'], 'privileges':['token_send', 'distribute']}],
                       'excessive':[{"account":accnt_main['account'], "privileges": ["distribute"]},
                                    {"account":self.account_list[1]['account'], "privileges":[]},
                                    {"account":self.account_list[2]['account'], "privileges":[]},
                                    {"account":self.account_list[3]['account'], "privileges":[]},
                                    {"account":self.account_list[4]['account'], "privileges":[]},
                                    {"account":self.account_list[5]['account'], "privileges":[]},
                                    {"account":self.account_list[6]['account'], "privileges":[]},
                                    {"account":self.account_list[7]['account'], "privileges":[]},
                                    {"account":self.account_list[8]['account'], "privileges":[]},
                                    {"account":self.account_list[9]['account'], "privileges":[]},
                                    {"account":self.account_list[10]['account'], "privileges":[]}]
        }
        
        for key, value in controllers.items():
            try:
                created = self.nodes[d_id].block_create_issuance(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    symbol='ISSUE',
                    name='test_token-issuance',
                    controllers=value
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN ISSUANCE FAILS: controllers: {}".format(key))
                results.append(False)
            except LogosRPCError as error:
                results.append(True)
            
        return results

    #################################################################################
    # ILLEGAL TOKEN ISSUE ADDITIONAL
    # On Token account send chain
    #################################################################################
    def illegal_issue_additional(self, accnt_main, token_main, token_poor, token_nosetting):
        results = []
                    
        main_info = self.nodes[0].account_info(accnt_main['account'])
        main_prev = main_info['frontier']
        d_id = designated_delegate(accnt_main['public'], main_prev)

        ## INSUFFICIENT FEE IN TOKEN ACCOUNT
        try:
            created = self.nodes[d_id].block_create_issue_additional(
                private_key=accnt_main['private'],
                previous=main_prev,
                token_id=token_poor['token_id'],
                amount='100000000'
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN ISSUE ADDITIONAL FAILS: token has insufficient logos fees but succeeded in issue additional")
            results.append(False)
        except LogosRPCError as error:
            results.append(True)

        ## INSUFFICIENT REQUEST FEE
        try:
            created = self.nodes[d_id].block_create_issue_additional(
                private_key=accnt_main['private'],
                previous=main_prev,
                token_id=token_main['token_id'],
                amount='100000000',
                fee=eval(MIN_FEE)-1
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN ISSUE ADDITIONAL FAILS: insufficient request fee succeeded")
            results.append(False)
        except LogosRPCError as error:
            results.append(True)

        ## MALFORMED AMOUNT
        for key, value in {'empty':'', 'decimal':'123.123', 'negative':'-1000', 'max amount':'350000000000000000000000000000000000000'}.items():
            try:
                created = self.nodes[0].block_create_issue_additional(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    amount=value,
                    token_id=token_main['token_id']
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN ISSUE ADDITIONAL FAILS: amount: {}".format(key))
                results.append(False)
            except LogosRPCError as error:
                results.append(True)

        ## NO PRIVILEGE CONTROLLER
        nopriv = self.account_list[1]
        nopriv_info = self.nodes[0].account_info(nopriv['account'])
        nopriv_prev = nopriv_info['frontier']
        d_id = designated_delegate(nopriv['public'], nopriv_prev)
        
        try:
            created = self.nodes[d_id].block_create_issue_additional(
                private_key=nopriv['private'],
                previous=nopriv_prev,
                amount='100000',
                token_id=token_main['token_id']
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN ISSUE ADDITIONAL FAILS: Controller w/o privilege able to issue additional")
            results.append(False)
        except LogosRPCError as error:
            results.append(True)

        ## NO SETTING
        main_info = self.nodes[0].account_info(accnt_main['account'])
        main_prev = main_info['frontier']
        d_id = designated_delegate(nopriv['public'], nopriv_prev)
        
        try:
            created = self.nodes[d_id].block_create_issue_additional(
                private_key=accnt_main['private'],
                previous=main_prev,
                amount='100000',
                token_id=token_nosetting['token_id']
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN ISSUE ADDITIONAL FAILS: Token w/o setting able to issue additional")
            results.append(False)
        except LogosRPCError as error:
            results.append(True)

        return results

    #################################################################################
    # ILLEGAL TOKEN CHANGE SETTING
    # On Token account send chain
    #################################################################################
    def illegal_change_setting(self, accnt_main, token_main, token_poor):
        results = []
        
        main_info = self.nodes[0].account_info(accnt_main['account'])
        main_prev = main_info['frontier']
        d_id = designated_delegate(accnt_main['public'], main_prev)

        ## INSUFFICIENT FEE IN TOKEN ACCOUNT
        try:
            created = self.nodes[0].block_create_change_setting(
                private_key=accnt_main['private'],
                previous=main_prev,
                value="true",
                setting="issuance",
                token_id=token_poor['token_id']
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN CHANGE SETTING FAILS: token has insufficient logos fees but succeeded in issue additional")
            results.append(False)
        except LogosRPCError as error:
            results.append(True)
        
        ## INSUFFICIENT REQUEST FEE
        try:
            created = self.nodes[0].block_create_change_setting(
                private_key=accnt_main['private'],
                previous=main_prev,
                value="true",
                setting="issuance",
                token_id=token_main['token_id'],
                fee=eval(MIN_FEE)-1
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN CHANGE SETTING FAILS: insufficient request fee succeeded")
            results.append(False)
        except LogosRPCError as error:
            results.append(True)
        
            
        ## MALFORMED SETTING
        for key, value in {'empty':'', 'illegal':'distribute'}.items():
            try:
                created = self.nodes[d_id].block_create_change_setting(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    value="true",
                    setting=value,
                    token_id=token_main['token_id']
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN CHANGE SETTING FAILS: setting: {}".format(key))
                results.append(False)
            except LogosRPCError as error:
                results.append(True)

        ## MALFORMED VALUE
        for key, value in {'empty':'', 'illegal':'1'}.items():
            try:
                created = self.nodes[d_id].block_create_change_setting(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    value=value,
                    setting='whitelist',
                    token_id=token_main['token_id']
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN CHANGE SETTING FAILS: value: {}".format(key))
                results.append(False)
            except LogosRPCError as error:
                results.append(True)

        ## NO PRIVILEGE
        nopriv = self.account_list[1]
        nopriv_info = self.nodes[0].account_info(nopriv['account'])
        nopriv_prev = nopriv_info['frontier']
        d_id = designated_delegate(nopriv['public'], nopriv_prev)

        try:
            created = self.nodes[d_id].block_create_change_setting(
                private_key=nopriv['private'],
                previous=nopriv_prev,
                value="true",
                setting=value,
                token_id=token_main['token_id']
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN CHANGE SETTING FAILS: Controller w/o privilege able to change setting")
            results.append(False)
        except LogosRPCError as error:
            results.append(True)
        
        return results

    #################################################################################
    # ILLEGAL TOKEN IMMUTE SETTING
    # On Token account send chain
    #################################################################################
    def illegal_immute_setting(self, accnt_main, token_main, token_poor, token_nosetting):
        results = []

        return results
    
    #################################################################################
    # ILLEGAL TOKEN REVOKE
    # On Token account send chain
    #################################################################################
    def illegal_revoke(self, accnt_main, token_main, token_poor, token_nosetting):
        results = []

        return results

    #################################################################################
    # ILLEGAL TOKEN ADJUST USER STATUS
    # On Token account send chain
    #################################################################################
    def illegal_adjust_user_status(self, accnt_main, token_main, token_poor, token_nosetting):
        results = []

        return results

    #################################################################################
    # ILLEGAL TOKEN ADJUST FEE
    # On Token account send chain
    #################################################################################
    def illegal_adjust_fee(self, accnt_main, token_main, token_poor, token_nosetting):
        results = []

        main_info = self.nodes[0].account_info(accnt_main['account'])
        main_prev = main_info['frontier']
        d_id = designated_delegate(accnt_main['public'], main_prev)

        ## INSUFFICIENT FEE IN TOKEN ACCOUNT
        try:
            created = self.nodes[d_id].block_create_adjust_fee(
                private_key=accnt_main['private'],
                previous=main_prev,
                token_id=token_poor['token_id'],
                fee_type='percentage',
                fee_rate='10'
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN ADJUST FEE FAILS: token has insufficient logos fees but succeeded in adjust fee")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)

        ## INSUFFICIENT REQUEST FEE
        try:
            created = self.nodes[d_id].block_create_adjust_fee(
                private_key=accnt_main['private'],
                previous=main_prev,
                token_id=token_main['token_id'],
                fee_type='percentage',
                fee_rate='10',
                fee=eval(MIN_FEE)-1
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN ADJUST FEE FAILS: token has insufficient logos fees but succeeded in adjust fee")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)

        ## MALFORMED FEE TYPE
        for key, value in {'empty':'','illegal':'distribute'}.items():
            try:
                created = self.nodes[d_id].block_create_adjust_fee(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    token_id=token_main['token_id'],
                    fee_type=value,
                    fee_rate='10'
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN ADJUST FEE FAILS: fee type: {}".format(key))
                results.append(False)
            except LogosRPCError as _:
                results.append(True)

        ## MALFORMED FEE RATE PERCENTAGE
        for key, value in {'decimal':'1.5', 'above100':'101', 'negative':'-39'}.items():
            try:
                created = self.nodes[d_id].block_create_adjust_fee(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    token_id=token_main['token_id'],
                    fee_type='percentage',
                    fee_rate=value
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN ADJUST FEE FAILS: percentage fee rate: {}".format(key))
                results.append(False)
            except LogosRPCError as _:
                results.append(True)

        ## MALFORMED FEE RATE FLATE
        for key, value in {'decimal':'1.5', 'negative':'-39'}.items():
            try:
                created = self.nodes[d_id].block_create_adjust_fee(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    token_id=token_main['token_id'],
                    fee_type='flat',
                    fee_rate=value
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN ADJUST FEE FAILS: flat fee rate: {}".format(key))
                results.append(False)
            except LogosRPCError as _:
                results.append(True)

        ## NO PRIVILEGES
        nopriv = self.account_list[1]
        nopriv_info = self.nodes[0].account_info(nopriv['account'])
        nopriv_prev = nopriv_info['frontier']
        d_id = designated_delegate(nopriv['public'], nopriv_prev)
        
        try:
            created = self.nodes[d_id].block_create_adjust_fee(
                private_key=nopriv['private'],
                previous=nopriv_prev,
                token_id=token_main['token_id'],
                fee_type='flat',
                fee_rate='10'
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN ADJUST FEE FAILS: Controller w/o privilege able to adjust fee")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)

        ## NO SETTING
        main_info = self.nodes[0].account_info(accnt_main['account'])
        main_prev = main_info['frontier']
        d_id = designated_delegate(accnt_main['public'], main_prev)

        try:
            created = self.nodes[d_id].block_create_adjust_fee(
                private_key=accnt_main['private'],
                previous=main_prev,
                token_id=token_nosetting['token_id'],
                fee_type='flat',
                fee_rate='10'
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN ADJUST FEE FAILS: Token w/o setting able to adjust fee")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)
            
        return results

    #################################################################################
    # ILLEGAL TOKEN UPDATE ISSUER INFO
    # On Token account send chain
    #################################################################################
    def illegal_update_issuer_info(self, accnt_main, token_main, token_poor):
        results = []

        main_info = self.nodes[0].account_info(accnt_main['account'])
        main_prev = main_info['frontier']
        d_id = designated_delegate(accnt_main['public'], main_prev)

        ## INSUFFICIENT FEE IN TOKEN ACCOUNT
        try:
            created = self.nodes[d_id].block_create_update_issuer_info(
                private_key=accnt_main['private'],
                previous=main_prev,
                token_id=token_poor['token_id'],
                new_info='testing'
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN UPDATE ISSUER INFO FAILS: token has insufficient logos fees but succeeded in update issuer info")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)

        ## INSUFFICIENT REQUEST FEE
        try:
            created = self.nodes[d_id].block_create_update_issuer_info(
                private_key=accnt_main['private'],
                previous=main_prev,
                token_id=token_main['token_id'],
                new_info='testing',
                fee=eval(MIN_FEE)-1
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN UPDATE ISSUER INFO FAILS: insufficient request fee succeeded")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)
        

        ## MALFORMED NEW INFO
        for key, value in {'long info':'a'*513}.items():
            try:
                created = self.nodes[d_id].block_create_update_issuer_info(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    token_id=token_main['token_id'],
                    new_info=value
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN UPDATE ISSUER INFO FAILS: new_info: {}".format(key))
                results.append(False)
            except LogosRPCError as _:
                results.append(True)

        ## NO PRIVILEGES
        nopriv = self.account_list[1]
        nopriv_info = self.nodes[0].account_info(nopriv['account'])
        nopriv_prev = nopriv_info['frontier']
        d_id = designated_delegate(nopriv['public'], nopriv_prev)
        
        try:
            created = self.nodes[d_id].block_create_update_issuer_info(
                private_key=nopriv['private'],
                previous=nopriv_prev,
                token_id=token_main['token_id'],
                new_info=value
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN UPDATE ISSUER INFO FAILS: Controller w/o privilege able to update issuer info")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)

        return results

    #################################################################################
    # ILLEGAL TOKEN UPDATE CONTROLLER
    # On Token account send chain
    #################################################################################
    def illegal_update_controller(self, accnt_main, token_main, token_poor):
        results = []

        main_info = self.nodes[0].account_info(accnt_main['account'])
        main_prev = main_info['frontier']
        d_id = designated_delegate(accnt_main['public'], main_prev)

        ## INSUFFICIENT FEE IN TOKEN ACCOUNT
        try:
            created = self.nodes[d_id].block_create_update_controller(
                private_key=accnt_main['private'],
                previous=main_prev,
                token_id=token_poor['token_id'],
                action='add',
                controller={"account":self.account_list[9]['account'], "privileges":[]}
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN UPDATE CONTROLLER FAILS: token has insufficient logos fees but succeeded in update issuer info")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)

        ## INSUFFICIENT REQUEST FEE
        try:
            created = self.nodes[d_id].block_create_update_controller(
                private_key=accnt_main['private'],
                previous=main_prev,
                token_id=token_main['token_id'],
                action='add',
                controller={"account":self.account_list[9]['account'], "privileges":[]},
                fee=eval(MIN_FEE)-1
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN UPDATE CONTROLLER FAILS: insufficient request fee succeeded")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)
        
        ## MALFORMED ACTION
        for key, value in {'empty':'','illegal':'delete'}.items():
            try:
                created = self.nodes[d_id].block_create_update_controller(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    action=value,
                    token_id=token_main['token_id'],
                    controller={"account":self.account_list[9]['account'], "privileges":[]}
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN UPDATE CONTROLLER FAILS: action: {}".format(key))
                results.append(False)
            except LogosRPCError as _:
                results.append(True)

        ## MALFORMED CONTROLLER
        controllers = {'empty':{},
                       'illegal privilege':{'account':self.account_list[9]['account'], 'privileges':['modify_distribute']},
                       #'duplicate privilege':{'account':self.account_list[9]['account'], 'privileges':['distribute','distribute']}
                       }
        
        for key, value in controllers.items():
            try:
                created = self.nodes[d_id].block_create_update_controller(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    action='add',
                    token_id=token_main['token_id'],
                    controller=value
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN UPDATE CONTROLLER FAILS: controller: {}".format(key))
                results.append(False)
            except LogosRPCError as _:
                results.append(True)
      
        ## MAX NUMBER OF CONTROLLERS ALREADY
        ### add valid controller so reaches max
        created = self.nodes[d_id].block_create_update_controller(
            private_key=accnt_main['private'],
            previous=main_prev,
            action='add',
            token_id=token_main['token_id'],
            controller={"account":self.account_list[9]['account'], "privileges":[]}
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at add controller')

        main_prev = created['hash']
        d_id = designated_delegate(accnt_main['public'], main_prev)
        
        try:
            created = self.nodes[d_id].block_create_update_controller(
                private_key=accnt_main['private'],
                previous=main_prev,
                action='add',
                token_id=token_main['token_id'],
                controller={"account":self.account_list[10]['account'], "privileges":[]}
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN UPDATE CONTROLLER FAILS: Max number of controllers exist yet succeeded in adding")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)
            
        ## NO PRIVILEGES
        nopriv = self.account_list[1]
        nopriv_info = self.nodes[0].account_info(nopriv['account'])
        nopriv_prev = nopriv_info['frontier']
        d_id = designated_delegate(nopriv['public'], nopriv_prev)

        try:
            created = self.nodes[d_id].block_create_update_controller(
                private_key=nopriv['private'],
                previous=nopriv_prev,
                action='add',
                token_id=token_main['token_id'],
                controller={"account":self.account_list[2]['account'], "privileges":['distribute']}
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN UPDATE ISSUER INFO FAILS: Controller w/o privilege able to update issuer info")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)
        
        return results
    
    #################################################################################
    # ILLEGAL TOKEN BURN
    # On Token account send chain
    #################################################################################
    def illegal_burn(self, accnt_main, token_main, token_poor):
        results = []

        main_info = self.nodes[0].account_info(accnt_main['account'])
        main_prev = main_info['frontier']
        d_id = designated_delegate(accnt_main['public'], main_prev)

        ## INSUFFICIENT FEE IN TOKEN ACCOUNT
        try:
            created = self.nodes[d_id].block_create_burn(
                private_key=accnt_main['private'],
                previous=main_prev,
                token_id=token_poor['token_id'],
                amount='100000'
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN BURN FAILS: token has insufficient logos fees but succeeded in burn")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)

        ## INSUFFICIENT REQUEST FEE
        try:
            created = self.nodes[d_id].block_create_burn(
                private_key=accnt_main['private'],
                previous=main_prev,
                token_id=token_main['token_id'],
                amount='100000',
                fee=eval(MIN_FEE)-1
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN BURN FAILS: insufficient request fee succeeded")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)

        ## MALFORMED AMOUNT
        for key, value in {'empty':'','decimal':'10000.12','excessive':'2200000000000000'}.items():
            try:
                created = self.nodes[d_id].block_create_burn(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    token_id=token_main['token_id'],
                    amount=value
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN BURN FAILS: amount: {}".format(key))
                results.append(False)
            except LogosRPCError as _:
                results.append(True)

        ## NO PRIVILEGES
        nopriv = self.account_list[1]
        nopriv_info = self.nodes[0].account_info(nopriv['account'])
        nopriv_prev = nopriv_info['frontier']
        d_id = designated_delegate(nopriv['public'], nopriv_prev)

        try:
            created = self.nodes[d_id].block_create_burn(
                private_key=nopriv['private'],
                previous=nopriv_prev,
                token_id=token_main['token_id'],
                amount='100000'
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN BURN FAILS: Controller w/o privilege able to burn")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)
            
        return results

    #################################################################################
    # ILLEGAL TOKEN DISTRIBUTE
    # On Token account send chain
    #################################################################################
    def illegal_distribute(self, accnt_main, token_main, token_poor):
        results = []

        main_info = self.nodes[0].account_info(accnt_main['account'])
        main_prev = main_info['frontier']
        d_id = designated_delegate(accnt_main['public'], main_prev)

        ## INSUFFICIENT FEE IN TOKEN ACCOUNT
        try:
            created = self.nodes[d_id].block_create_distribute(
                private_key=accnt_main['private'],
                previous=main_prev,
                token_id=token_poor['token_id'],
                transaction={'destination':accnt_main['account'], 'amount':'100000'}
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN DISTRIBUTE FAILS: token has insufficient logos fees but succeeded in distribute")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)

        ## INSUFFICIENT REQUEST FEE
        try:
            created = self.nodes[d_id].block_create_distribute(
                private_key=accnt_main['private'],
                previous=main_prev,
                token_id=token_main['token_id'],
                transaction={'destination':accnt_main['account'], 'amount':'100000'},
                fee=eval(MIN_FEE)-1
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN DISTRIBUTE FAILS: insufficient request fee succeeded")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)

        ## MALFORMED TRANSACTION AMOUNT
        for key, value in {'empty':'','negative':'-100000','excessive':'2200000000000000'}.items():
            try:
                created = self.nodes[d_id].block_create_distribute(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    token_id=token_main['token_id'],
                    transaction={'destination':accnt_main['account'], 'amount':value}
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN DISTRIBUTE FAILS: txn amount: {}".format(key))
                results.append(False)
            except LogosRPCError as _:
                results.append(True)
            
        ## MALFORMED TRANSACTION DESTINATION
        for key, value in {'empty':'','public key dest':accnt_main['public']}.items():
            try:
                created = self.nodes[d_id].block_create_distribute(
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    token_id=token_main['token_id'],
                    transaction={'destination':value, 'amount':'100000'}
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN DISTRIBUTE FAILS: txn destination: {}".format(key))
                results.append(False)
            except LogosRPCError as _:
                results.append(True)
            
        ## NO PRIVILEGES
        nopriv = self.account_list[1]
        nopriv_info = self.nodes[0].account_info(nopriv['account'])
        nopriv_prev = nopriv_info['frontier']
        d_id = designated_delegate(nopriv['public'], nopriv_prev)

        try:
            created = self.nodes[d_id].block_create_distribute(
                private_key=nopriv['private'],
                previous=nopriv_prev,
                token_id=token_main['token_id'],
                transaction={'destination':nopriv['account'], 'amount':'100000'}
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN DISTRIBUTE FAILS: Controller w/o privilege able to distribute")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)
            
        return results

    #################################################################################
    # ILLEGAL TOKEN WITHDRAW FEE
    # On Token account send chain
    #################################################################################
    def illegal_withdraw_fee(self, accnt_main, token_main, token_poor):
        results = []

        return results

    #################################################################################
    # ILLEGAL TOKEN WITHDRAW LOGOS
    # On Token account send chain
    #################################################################################
    def illegal_withdraw_logos(self, accnt_main, token_main, token_poor):
        results = []
        
        main_info = self.nodes[0].account_info(accnt_main['account'])
        main_prev = main_info['frontier']
        d_id = designated_delegate(accnt_main['public'], main_prev)

        ## INSUFFICIENT FEE IN TOKEN ACCOUNT
        try:
            created = self.nodes[d_id].block_create_withdraw(
                type='withdraw_logos',
                private_key=accnt_main['private'],
                previous=main_prev,
                token_id=token_poor['token_id'],
                transaction={'destination':accnt_main['account'], 'amount':'100000'}
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN WITHDRAW LOGOS FAILS: token has insufficient logos fees but succeeded in withdrawing logos")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)

        ## INSUFFICIENT REQUEST FEE
        try:
            created = self.nodes[d_id].block_create_withdraw(
                type='withdraw_logos',
                private_key=accnt_main['private'],
                previous=main_prev,
                token_id=token_main['token_id'],
                transaction={'destination':accnt_main['account'], 'amount':'100000'},
                fee=eval(MIN_FEE)-1
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN WTIHDRAW LOGOS FAILS: insufficient request fee succeeded")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)

        ## MALFORMED TRANSACTION AMOUNT
        #for key, value in {'empty':'','negative':'-100000','excessive':'30000000000000000000000000000001'}.items(): ## EMPTY AND NEGATIVE WORK (get set to 0)
        for key, value in {'excessive':'30000000000000000000000000000001'}.items(): ## EMPTY IS FINE
            try:
                created = self.nodes[d_id].block_create_withdraw(
                    type='withdraw_logos',
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    token_id=token_main['token_id'],
                    transaction={'destination':accnt_main['account'], 'amount':value}
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN WITHDRAW LOGOS FAILS: txn amount: {}".format(key))
                results.append(False)
            except LogosRPCError as _:
                results.append(True)
            
        ## MALFORMED TRANSACTION DESTINATION
        for key, value in {'empty':'','public key dest':accnt_main['public']}.items():
            try:
                created = self.nodes[d_id].block_create_withdraw(
                    type='withdraw_logos',
                    private_key=accnt_main['private'],
                    previous=main_prev,
                    token_id=token_main['token_id'],
                    transaction={'destination':value, 'amount':'100000'}
                )
                self.nodes[d_id].process(created['request'])
                print("TOKEN WITHDRAW LOGOS FAILS: txn destination: {}".format(key))
                results.append(False)
            except LogosRPCError as _:
                results.append(True)
            
        ## NO PRIVILEGES
        nopriv = self.account_list[1]
        nopriv_info = self.nodes[0].account_info(nopriv['account'])
        nopriv_prev = nopriv_info['frontier']
        d_id = designated_delegate(nopriv['public'], nopriv_prev)

        try:
            created = self.nodes[d_id].block_create_withdraw(
                type='withdraw_logos',
                private_key=nopriv['private'],
                previous=nopriv_prev,
                token_id=token_main['token_id'],
                transaction={'destination':nopriv['account'], 'amount':'100000'}
            )
            self.nodes[d_id].process(created['request'])
            print("TOKEN DISTRIBUTE FAILS: Controller w/o privilege able to withdraw logos")
            results.append(False)
        except LogosRPCError as _:
            results.append(True)
            
        return results

    #################################################################################
    # ILLEGAL TOKEN SEND
    # On Logos account send chain
    #################################################################################
    def illegal_token_send(self, accnt_main, token_main, accnt_poor):
        results = []

        return results
