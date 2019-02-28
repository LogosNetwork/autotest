# autotest
Contains code for running end-to-end distributed testing

## Test environment setup

It is highly recommended to run ATI with Python3.5+ (previous versions untested, setup guide [here](https://docs.python-guide.org/starting/install3/linux/) for 3.6 and [here](https://tecadmin.net/install-python-3-7-on-ubuntu-linuxmint/) 3.7). 

In addition, it is best practice to use `virtualenvwrapper` (see [Basic Installation](https://virtualenvwrapper.readthedocs.io/en/latest/install.html#basic-installation) and [Shell Startup File](https://virtualenvwrapper.readthedocs.io/en/latest/install.html#shell-startup-file) on the official docs) in order to keep different Python development environments isolated. After installing virtualenvwrapper, set up your ATI environment with `mkvirtualenv -p $(which python3) autotest`. To exit python virtualenv, run `deactivate`. To re-enter, run `workon autotest` (command line prompt now looks like `(autotest) $ `).

If everything is correctly set up, running `python -V` should output `Python 3.x.y` where `x >= 5`. Install required python packages by running `pip install -r requirements.txt` (in the root `autotest` directory).

## How to run
#### Deploy cluster:
i. goto `autotest/deploy/distributed` and upload binary
```
$ ./upload_s3.sh -l <path_to_build_binary>
```
ii. launch cluster
```
$ ./deploy_cluster.sh <cluster_name> -n <num_nodes> -e t2.micro
```

#### Run tests:
i. go to `autotest/autotest`
```
(autotest) $ python run_test.py <cluster_name>
```

#### Skipping tests
If you want to skip certain tests temporarily, e.g. a test named `test_to_skip`, simply locate where it is defined, then add a `skip` decorator like so
```
    @skip
    def test_to_skip:
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

Each test case must return `True` or `False` to indicate if test succeeds.

#### Rerun after each test
If you want a test to be rerun after each test case finishes, e.g. a database sanity checker, then add a `rerun_needed` decorator like so
```
    @rerun_needed
    def test_to_rerun:
``` 
Then this test won't be run standalone, but rather after each of the other standalone tests completes. As a concrete example, if out of tests A, B, C test A has `@rerun_needed`, then a possible execution sequence will be `(B -> A) -> (C -> A)`.
