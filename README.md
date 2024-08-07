# mongo_replica_set_learn

- In order to know basic about replica set and read/write concern
- Use docker-compose to demo MongoDB replica set environment
- Then test how read/write behaves when some secondary nodes crashed

<img width="567" alt="image" src="https://github.com/daniel0318/mongo_replica_set_learn/assets/10074834/c1390299-e7c9-4a34-ae3d-9b91a781ac0d">

### Launch Services
- clone & setup environment
```
git clone git@github.com:daniel0318/mongo_replica_set_learn.git
cd mongo_replica_set_learn
python3 -m venv .venv
source .venv/bin/activate
docker-compose up --build -d
```

- init replicate set
```
python init_replica_set.py
pytest -s --verbose test_read_write_concern.py
```
```
Expected result
=========================================================== short test summary info ===========================================================
FAILED test_read_write_concern.py::test_write_majority_w1[majority] - Failed: Timeout >5.0s
======================================================== 1 failed, 3 passed in 15.81s =========================================================
the failed one is expected timeout
```


### Explaining

[init_replica_set.py](https://github.com/daniel0318/mongo_replica_set_learn/blob/main/init_replica_set.py)
- setup 5 nodes of replicate set, 1 as primary, 3 as secondary, 1 as arbiter

[test_read_write_concern.py](https://github.com/daniel0318/mongo_replica_set_learn/blob/main/test_read_write_concern.py)
- use pytest to test how read/write concern behave when some secondary nodes disconnect
- arbiter will handle voting the primary, when over half nodes lost connection

def test_write_majority_w1:
- when disconnect 2 nodes, write=1 pass
- when disconnect 2 nodes, write=majority blocked
  
def test_read_majority_w1:
- read=local will get self node value
- read=majority will get >=half node value, so need a while to wait nodes sync value
- after >= half nodes lost connection, read=majority only read those values when majority nodes alive, ignore values inserted after nodes crash

## conclusion
1. write=1 and read=local will respond quickly but ignore other node's value or eventually changed to correct value after a while
2. write=majority will block when >=half nodes down
3. read=majority won't show values not sync with >= half nodes

