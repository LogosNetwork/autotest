from utils import *
from orchestration import *
import random
import json
import qlmdb3

class TestCaseMixin:
    def test_10_token_requests(self):
        supply = 1234567890123456789
        dist = 12345
        fee = eval(str(60)+'0'*MLGS_DEC)
        logos = 2345678901234567890123456789
        token_fee = 100

        print('======================================================================')
        print('TOKEN ISSUANCE')
        print('======================================================================')
        account_before = self.nodes[0].account_info(self.account_list[1]['account'])
        account_prev = account_before['frontier']
        d_id = designated_delegate(self.account_list[1]['public'],account_prev)
        created = self.nodes[d_id].block_create_issuance(
            total_supply=supply,
            private_key=self.account_list[1]['private'],
            previous=account_prev,
            fee_type='flat',
            fee_rate=0,
            symbol='TOKREQ',
            name='test_token-requests',
            controllers=[{"account":self.account_list[1]['account'], "privileges": ["distribute", "burn", "issuance", "withdraw_fee", "withdraw_logos", "revoke", "update_issuer_info", "change_freeze", "update_controller", "change_modify_freeze", "freeze", "adjust_fee"]}],
            settings=["revoke", "issuance", "modify_freeze", "freeze", "adjust_fee"],
            fee=fee
        )
        coin = eval(created['request'])
        token_account = qlmdb3.toaccount(qlmdb3.unhexlify(coin['token_id']))
        
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at issuance')
            
        account_check = self.nodes[0].account_info(self.account_list[1]['account'])
        if eval(account_check['balance']) != eval(account_before['balance'])-fee:
            print("sender logos amount fails check")
            return False
        account_prev = created['hash']
        
        print('======================================================================')
        print("FUND TOKEN WITH LOGOS")
        print('======================================================================')
        gen_prev = self.nodes[0].account_info()['frontier']
        d_id = designated_delegate(g_pub, gen_prev)
        created = self.nodes[d_id].block_create(
            previous=gen_prev,
            txns=[{"destination":token_account, "amount":logos}]
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at fund')

        print('======================================================================')
        print("DISTRIBUTE TOKEN")
        print('======================================================================')
        account_before = self.nodes[0].account_info(self.account_list[1]['account'])
        token_before = self.nodes[0].account_info(token_account)
        token_prev =  token_before['frontier']
        d_id = designated_delegate(self.account_list[1]['public'], token_prev)
        created = self.nodes[0].block_create_distribute(
            private_key=self.account_list[1]['private'],
            previous=token_prev,
            fee=fee,
            token_id=coin['token_id'],
            transaction={"destination" : self.account_list[1]['account'], "amount": dist }
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at distribute')
        token_prev = created['hash']
        
        account_check = self.nodes[0].account_info(self.account_list[1]['account'])
        token_check = self.nodes[0].account_info(token_account)
        # check token 
        if eval(token_check['token_balance'])!=(supply-dist) or eval(token_check['balance'])!=eval(token_before['balance'])-fee:
            print("token_account balance fails")
            return False
        # check account
        if eval(account_check['tokens'][coin['token_id']]['balance']) != dist:
            print("account token balance fails")
            return False
        
        print('======================================================================')
        print("TOKEN SEND WITH FLAT FEE")
        print('======================================================================')
        account_before = self.nodes[0].account_info(self.account_list[1]['account'])
        token_before = self.nodes[0].account_info(token_account)
        d_id = designated_delegate(self.account_list[1]['public'], account_prev)
        created = self.nodes[d_id].block_create_token_send(
            private_key=self.account_list[1]['private'],
            previous=account_prev,
            token_id=coin['token_id'],
            fee=fee,
            token_fee=token_fee,
            transactions=[{"destination":self.account_list[2]['account'], "amount":"2"},
                          {"destination":self.account_list[3]['account'], "amount":"3"},
                          {"destination":self.account_list[4]['account'], "amount":"4"},
                          {"destination":self.account_list[5]['account'], "amount":"5"},
                          {"destination":self.account_list[6]['account'], "amount":"6"},
                          {"destination":self.account_list[7]['account'], "amount":"7"},
                          {"destination":self.account_list[8]['account'], "amount":"8"},
                          {"destination":self.account_list[9]['account'], "amount":"9"}]
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at send')

        account_check = self.nodes[0].account_info(self.account_list[1]['account'])
        token_check = self.nodes[0].account_info(token_account)
        total_sent = 0
        for i in range(2, 10):
            dest_check = self.nodes[0].account_info(self.account_list[i]['account'])
            #check dest
            if eval(dest_check['tokens'][coin['token_id']]['balance'])!=i: return False
            total_sent += i
            
        #check sender
        if eval(account_check['tokens'][coin['token_id']]['balance']) != eval(account_before['tokens'][coin['token_id']]['balance'])-total_sent-token_fee:
            print("sender token amount fails check")
            return False
        if eval(account_check['balance']) != eval(account_before['balance'])-fee:
            print("sender logos amount fails check")
            return False

        #check token_account
        if eval(token_check['token_fee_balance'])!=eval(token_before['token_fee_balance'])+token_fee:
            print("token_account token fee balance fails check")
            return False
        
        print('======================================================================')
        print('BURN TOKEN')
        print('======================================================================')
        burn = 10000
        token_before = self.nodes[0].account_info(token_account)
        token_prev = token_before['frontier']
        d_id = designated_delegate(self.account_list[1]['public'], token_prev)
        created = self.nodes[d_id].block_create_burn(
            private_key=self.account_list[1]['private'],
            previous=token_prev,
            amount=burn,
            token_id=coin['token_id'],
            fee=fee
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at burn')

        token_check = self.nodes[0].account_info(token_account)

        if eval(token_check['token_balance'])!=eval(token_before['token_balance'])-burn or eval(token_check['total_supply'])!=eval(token_before['total_supply'])-burn:
            print("token_account balance/supply fails check")
            return False
        if eval(token_check['balance'])!=eval(token_before['balance'])-fee:
            print("token_account fee balance fails check")
            return False

        print('======================================================================')
        print('ISSUE ADDITIONAL TOKEN')
        print('======================================================================')
        issue_add = 1000000
        token_before = self.nodes[0].account_info(token_account)
        token_prev = token_before['frontier']
        d_id = designated_delegate(self.account_list[1]['public'], token_prev)
        created = self.nodes[d_id].block_create_additional_issuance(
            private_key=self.account_list[1]['private'],
            previous=token_prev,
            amount=issue_add,
            token_id=coin['token_id'],
            fee=fee
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at issue additional')

        token_check = self.nodes[0].account_info(token_account)

        if eval(token_check['token_balance'])!=eval(token_before['token_balance'])+issue_add or eval(token_check['total_supply'])!=eval(token_before['total_supply'])+issue_add:
            print("token_account balance/supply fails check")
            return False

        if eval(token_check['balance'])!=eval(token_before['balance'])-fee:
            print("token_account fee balance fails check")
            return False
        
        print('======================================================================')
        print('WITHDRAW FEE')
        print('======================================================================')
        account_before = self.nodes[0].account_info(self.account_list[1]['account'])
        token_before = self.nodes[0].account_info(token_account)
        token_prev = token_before['frontier']
        d_id = designated_delegate(self.account_list[1]['public'], token_prev)
        created = self.nodes[d_id].block_create_withdraw(
            type='withdraw_fee',
            private_key=self.account_list[1]['private'],
            previous=token_prev,
            transaction={"destination":self.account_list[1]['account'], "amount":token_fee},
            token_id=coin['token_id'],
            fee=fee
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at withdraw fee')

        account_check = self.nodes[0].account_info(self.account_list[1]['account'])
        token_check = self.nodes[0].account_info(token_account)

        if eval(token_check['token_fee_balance'])!=eval(token_before['token_fee_balance'])-token_fee:
            print("token_account balance/supply fails check")
            return False
        if eval(token_check['balance'])!=eval(token_before['balance'])-fee:
            print("token_account fee balance fails check")
            return False
        
        if eval(account_check['tokens'][coin['token_id']]['balance']) != eval(account_before['tokens'][coin['token_id']]['balance'])+token_fee:
            print("sender token amount fails check")
            return False

        print('======================================================================')
        print('WITHDRAW LOGOS')
        print('======================================================================')
        withdraw_logos = 123
        account_before = self.nodes[0].account_info(self.account_list[1]['account'])
        token_before = self.nodes[0].account_info(token_account)
        token_prev = token_before['frontier']
        d_id = designated_delegate(self.account_list[1]['public'], token_prev)
        created = self.nodes[d_id].block_create_withdraw(
            type='withdraw_logos',
            private_key=self.account_list[1]['private'],
            previous=token_prev,
            transaction={"destination":self.account_list[1]['account'], "amount":withdraw_logos},
            token_id=coin['token_id'],
            fee=fee
            
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at withdraw logos')

        account_check = self.nodes[0].account_info(self.account_list[1]['account'])
        token_check = self.nodes[0].account_info(token_account)

        if eval(token_check['balance'])!=eval(token_before['balance'])-withdraw_logos-fee:
            print("token_account balance/supply fails check")
            return False

        if eval(account_check['balance']) != eval(account_before['balance'])+withdraw_logos:
            print("sender token amount fails check")
            return False

        print('======================================================================')
        print('REVOKE')
        print('======================================================================')
        revoke = 9
        account_before = self.nodes[0].account_info(self.account_list[1]['account'])
        revoke_before = self.nodes[9].account_info(self.account_list[9]['account'])
        token_before = self.nodes[0].account_info(token_account)
        token_prev = token_before['frontier']
        d_id = designated_delegate(self.account_list[1]['public'], token_prev)
        created = self.nodes[d_id].block_create_revoke(
            private_key=self.account_list[1]['private'],
            previous=token_prev,
            source=self.account_list[9]['account'],
            transaction={"destination":self.account_list[1]['account'], "amount":revoke},
            token_id=coin['token_id'],
            fee=fee
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at revoke')

        account_check = self.nodes[0].account_info(self.account_list[1]['account'])
        revoke_check = self.nodes[9].account_info(self.account_list[9]['account'])
        token_check = self.nodes[0].account_info(token_account)

        if eval(account_check['tokens'][coin['token_id']]['balance']) != eval(account_before['tokens'][coin['token_id']]['balance'])+revoke:
            print("dest amount fails check")
            return False

        if eval(revoke_check['tokens'][coin['token_id']]['balance']) != eval(revoke_before['tokens'][coin['token_id']]['balance'])-revoke:
            print("src amount fails check")
            return False

        if eval(token_check['balance'])!=eval(token_before['balance'])-fee:
            print("token_account fee balance fails check")
            return False
        
        print('======================================================================')
        print('UPDATE ISSUER INFO')
        print('======================================================================')
        info = "this is the update"
        token_before = self.nodes[0].account_info(token_account)
        token_prev = token_before['frontier']
        d_id = designated_delegate(self.account_list[1]['public'], token_prev)
        created = self.nodes[d_id].block_create_update_issuer_info(
            private_key=self.account_list[1]['private'],
            previous=token_prev,
            token_id=coin['token_id'],
            new_info=info,
            fee=fee
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at update issuer info')

        token_check = self.nodes[0].account_info(token_account)

        if token_check['issuer_info'] != info:
            print("info fails check")
            return False
        if eval(token_check['balance'])!=eval(token_before['balance'])-fee:
            print("token_account fee balance fails check")
            return False

        print('======================================================================')
        print('CHANGE SETTING')
        print('======================================================================')
        setting_add = "freeze"
        token_before = self.nodes[0].account_info(token_account)
        token_prev = token_before['frontier']
        d_id = designated_delegate(self.account_list[1]['public'], token_prev)
        created = self.nodes[d_id].block_create_change_setting(
            private_key=self.account_list[1]['private'],
            previous=token_prev,
            value="true",
            setting=setting_add,
            token_id=coin['token_id'],
            fee=fee
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at change setting')

        token_check = self.nodes[0].account_info(token_account)

        before_setting = token_before['settings']
        before_setting.append(setting_add)
        
        if set(token_check['settings']) != set(before_setting):
            print("token_account settings fails check")
            return False
        if eval(token_check['balance'])!=eval(token_before['balance'])-fee:
            print("token_account fee balance fails check")
            return False

        print('======================================================================')
        print('ADD CONTROLLER')
        print('======================================================================')
        controller = {"account":self.account_list[2]['account'], "privileges":['distribute', 'revoke']}
        token_before = self.nodes[0].account_info(token_account)
        token_prev = token_before['frontier']
        d_id = designated_delegate(self.account_list[1]['public'], token_prev)
        created = self.nodes[d_id].block_create_update_controller(
            private_key=self.account_list[1]['private'],
            previous=token_prev,
            action='add',
            token_id=coin['token_id'],
            #controller= {"account":self.account_list[2]['account'], "privileges":['distribute']},
            controller=controller,
            fee=fee
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at add controller')
            
        token_check = self.nodes[0].account_info(token_account)

        if set(token_check['controllers'][1]['privileges']) != set(controller['privileges']):
            print("token_account controller fails check")
            return False
        if eval(token_check['balance'])!=eval(token_before['balance'])-fee:
            print("token_account fee balance fails check")
            return False
        
        print('======================================================================')
        print('REMOVE CONTROLLER PRIVILEGE')
        print('======================================================================')
        controller = {"account":self.account_list[2]['account'], "privileges":['revoke']}
        token_before = self.nodes[0].account_info(token_account)
        token_prev = token_before['frontier']
        d_id = designated_delegate(self.account_list[1]['public'], token_prev)
        created = self.nodes[d_id].block_create_update_controller(
            private_key=self.account_list[1]['private'],
            previous=token_prev,
            action='remove',
            token_id=coin['token_id'],
            #controller= {"account":self.account_list[2]['account'], "privileges":['distribute']},
            controller=controller,
            fee=fee
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at remove controller privilege')
            
        token_check = self.nodes[0].account_info(token_account)

        priv = token_before['controllers'][1]['privileges']
        priv.remove(controller['privileges'][0])
        if set(token_check['controllers'][1]['privileges']) != set(priv):
            print("token_account controller fails check")
            return False
        if eval(token_check['balance'])!=eval(token_before['balance'])-fee:
            print("token_account fee balance fails check")
            return False

        print('======================================================================')
        print('CHANGE IMMUTE SETTING')
        print('======================================================================')
        immute_setting = 'freeze'
        immute_able = 'modify_freeze'
        token_before = self.nodes[0].account_info(token_account)
        token_prev = token_before['frontier']
        d_id = designated_delegate(self.account_list[1]['public'], token_prev)
        created = self.nodes[d_id].block_create_immute_setting(
            private_key=self.account_list[1]['private'],
            previous=token_prev,
            token_id=coin['token_id'],
            setting=immute_setting,
            fee=fee
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at change immute setting')
            
        token_check = self.nodes[0].account_info(token_account)
        
        immute = token_before['settings']
        immute.remove(immute_able)
        
        if set(token_check['settings']) != set(immute):
            print("token_account settings fails check")
            return False
        if eval(token_check['balance'])!=eval(token_before['balance'])-fee:
            print("token_account fee balance fails check")
            return False

        print('======================================================================')
        print('CHANGE USER STATUS')
        print('======================================================================')
        status = 'frozen'
        account_before = self.nodes[0].account_info(self.account_list[3]['account'])
        token_before = self.nodes[0].account_info(token_account)
        token_prev = token_before['frontier']
        d_id = designated_delegate(self.account_list[1]['public'], token_prev)
        created = self.nodes[d_id].block_create_adjust_user_status(
            private_key=self.account_list[1]['private'],
            previous=token_prev,
            token_id=coin['token_id'],
            status=status,
            account=self.account_list[3]['account'],
            fee=fee
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at change user status')

        account_after = self.nodes[0].account_info(self.account_list[3]['account'])
        token_check = self.nodes[0].account_info(token_account)
        
        if account_before['tokens'][coin['token_id']]['frozen'] != 'false' or account_after['tokens'][coin['token_id']]['frozen'] != 'true':
            print("account status fails check")
            return False
        
        if eval(token_check['balance'])!=eval(token_before['balance'])-fee:
            print("token_account fee balance fails check")
            return False
        
        print('======================================================================')
        print('ADJUST FEE')
        print('======================================================================')
        fee_type = 'percentage'
        fee_rate = '20'
        token_before = self.nodes[0].account_info(token_account)
        token_prev = token_before['frontier']
        d_id = designated_delegate(self.account_list[1]['public'], token_prev)
        created = self.nodes[d_id].block_create_adjust_fee(
            private_key=self.account_list[1]['private'],
            previous=token_prev,
            token_id=coin['token_id'],
            fee_type=fee_type,
            fee_rate=fee_rate,
            fee=fee
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at change immute setting')

        account_after = self.nodes[0].account_info(self.account_list[3]['account'])
        token_check = self.nodes[0].account_info(token_account)
        
        if token_before['fee_type'] != 'flat' or token_check['fee_type'] != fee_type or token_check['fee_rate'] != fee_rate:
            print("token_account fee type/rate fails check")
            return False
        if eval(token_check['balance'])!=eval(token_before['balance'])-fee:
            print("token_account fee balance fails check")
            return False

        print('======================================================================')
        print('TOKEN SEND WITH PERCENTAGE FEE')
        print('======================================================================')
        token_fee = 2
        account_before = self.nodes[0].account_info(self.account_list[1]['account'])
        account_prev = account_before['frontier']
        token_before = self.nodes[0].account_info(token_account)
        d_id = designated_delegate(self.account_list[1]['public'], account_prev)
        created = self.nodes[d_id].block_create_token_send(
            private_key=self.account_list[1]['private'],
            previous=account_prev,
            token_id=coin['token_id'],
            fee=fee,
            token_fee=token_fee,
            transactions=[{"destination":self.account_list[10]['account'], "amount":"10"}]
        )
        self.nodes[d_id].process(created['request'])
        if not self.wait_for_requests_persistence([created['hash']]):
            sys.stderr.write('Creation stopped at send')

        account_check = self.nodes[0].account_info(self.account_list[1]['account'])
        token_check = self.nodes[0].account_info(token_account)
        total_sent = 0
        for i in range(2, 10):
            dest_check = self.nodes[0].account_info(self.account_list[i]['account'])
            #check dest
            if eval(dest_check['tokens'][coin['token_id']]['balance'])!=i: return False
            total_sent += i
            
        #check sender
        if eval(account_check['tokens'][coin['token_id']]['balance']) != eval(account_before['tokens'][coin['token_id']]['balance'])-total_sent-token_fee:
            print("sender token amount fails check")
            return False
        if eval(account_check['balance']) != eval(account_before['balance'])-fee:
            print("sender logos amount fails check")
            return False

        #check token_account
        if eval(token_check['token_fee_balance'])!=eval(token_before['token_fee_balance'])+token_fee:
            print("token_account token fee balance fails check")
            return False
        
        return True
