## Smoke Tests

Below is a list of tests each covering chunks of software requirements. They are to serve as the first round of broad-sweeping tests for general software behavior. Passing them merely means there are no blatant bugs in a given software build. Please run the itemized tests to make sure no edge case failure scenarios exist. 

Each test case is executed sequentially. In addition to the individual success condition checks below, database invariants will also be checked after each test item is run.

| Test Name | Test Summary | Success Condition |
| --- | --- | --- |
| single_txn_primary_process | Generate a single send transaction and send it to the designated delegate to process | desig. delegate queues to primary list; send is persisted in request block |
| single_txn_backup_process | Generate a single send transaction and send it to a non-designated delegate to process | backup delegate queues to secondary list, queue to primary list after timeout ; send is persisted in request block |
| flood_transactions | Generate one send transaction from each of multiple accounts to a different new destination account and send all to the desig. delegates to process | All transactions are persisted; new accounts are created |
| flood_receives | Generate one send transaction from each of multiple accounts to the same destination account and send all to the desig. delegates to process | All transactions are persisted; receives are correctly inserted |
| archive | After a few request blocks, micro blocks and epochs are generated, run database membership and invariant checks | All transactions in request blocks are persisted (all other DB invariants are preserved) |
| epoch_transition | When epoch transition takes place, delegates are retired/persisted/initiated as planned, and can pass all above tests | delegate indices and keys are correctly updated; all tests above pass when rerun after epoch transition. |
| \<test\>_standalone_tx_acceptor | Repeat tests 1-4 above but through standalone TxAcceptor | same tests pass under the same conditions |
| single_txn_reject | Generate a single send transaction and send it to the designated delegate to process, one or more backups are triggered to erroneously reject | send is persisted in request block if rejection tally is below threshold; if at or above, primary proposes an empty batch block, which should pass consensus |
