# autotest
Contains code for running end-to-end distributed testing

## How to run
#### Deploy cluster:
i. goto autotest/deploy/distributed and upload binary
```
$ ./upload_s3.sh -l <path_to_build_binary>
```
ii. launch cluster
```
$ ./deploy_cluster.sh <cluster_name> -n <num_nodes> -e t2.micro
```

#### Run tests:
i. goto autotest/autotest
```
$ python3 run_test.py <cluster_name>
```
<br>

## Adding Tests
All tests to be placed in dir:
```
autotest/autotest/test_cases
```
Name test case in following format:
```
test_<test_name>.py
```

Start your file with the following:
```
from utils import *

class TestCaseMixin:

	def test_<test_name>:
	

```
Have test return True/False
