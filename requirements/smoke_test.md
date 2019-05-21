## Smoke Tests

Below is a list of tests each covering chunks of software requirements. They are to serve as the first round of broad-sweeping tests for general software behavior. Passing them merely means there are no blatant bugs in a given software build. Please run the itemized tests to make sure no edge case failure scenarios exist. 

Each test case is executed sequentially. In addition to the individual success condition checks below, database invariants will also be checked after each test item is run.

| Test Name | Test Summary | Success Condition |
| --- | --- | --- |
 | 00_logos_req | 1. Single send from genesis to genesis<br>2. Single send from genesis to open a new account <br>3. Single send from account to self <br>4. Single send to account to the designated delegate to process <br>5. Single send to account to the backup delegate to process | 1. desig. delegate queues to primary list; send persisted in request block; balances all correct<br>2. desig. delegate queues to primary list; send persisted in request block; balances all correct<br>3. desig. delegate queues to primary list; send persisted in request block; balances all correct<br>4. desig. delegate queues to primary list; send persisted in request block; balances all correct<br>5. backup delegate queues to primary list; send persisted in request block; balances all correct |
| 01_account_creation | Generate x accounts from genesis and then generate one send transaction from each of multiple accounts to a different new destination account and send all to the desig. delegates to process | All transactions are persisted; new accounts are created |
| 02_logos_req_illegal | Generate a single send transaction and send it to the designated delegate to process, one or more backups are triggered to erroneously reject | send is persisted in request block if rejection tally is below threshold; if at or above, primary proposes an empty batch block, which should pass consensus |
| 03_flood_receives | Generate one send transaction from each of multiple accounts to the same destination account and send all to the desig. delegates to process | All transactions are persisted; receives are correctly inserted |
| 05_micro_archive | After a few request blocks, micro blocks is generated, run database membership and invariant checks | All transactions in request blocks are persisted (all other DB invariants are preserved) |
| 06_epoch_transition | When epoch transition takes place, delegates are retired/persisted/initiated as planned, and can pass all above tests | delegate indices and keys are correctly updated; all tests above pass when rerun after epoch transition. |
| \<test\>_standalone_tx_acceptor | Repeat tests 1-4 above but through standalone TxAcceptor | same tests pass under the same conditions |
| db | Run database checker on each node's local database | Pass on all nodes
| 10_token_req | Generate one of each TokenRequest and send to primary delegate to process| All requests are persisted; balances/status all correct|
| 11_token_req_illegal | Negative test cases for each type of TokenRequest | All requests rejected |
| 12_token_req_flood | Generate x tokens, distribute to accounts, generate token send transcations to other accounts, send all to designated delegate to process | All transactions are persisted|