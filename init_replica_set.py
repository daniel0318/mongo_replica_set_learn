from pymongo import MongoClient
from pymongo.errors import OperationFailure

client = MongoClient('mongodb://localhost:27018', directConnection=True)

repl_set_config = {
    "_id": "rs0",
    "members": [
        {"_id": 0, "host": "mongo1:27017", "priority": 2},
        {"_id": 1, "host": "mongo2:27017"},
        {"_id": 2, "host": "mongo3:27017"},
        {"_id": 3, "host": "mongo4:27017"},
        {"_id": 4, "host": "mongo-arbiter:27017", "arbiterOnly": True, "priority": 0}
    ]
}

# Attempt to initialize the replica set
try:
    client.admin.command("replSetInitiate", repl_set_config)
    print("Replica set initialized successfully")
except OperationFailure as e:
    if "already initialized" in str(e):
        print("Replica set already initialized")
    else:
        print(f"Initialization failed: {e}")

# Check the replica set status
try:
    status = client.admin.command("replSetGetStatus")
    print("Replica set status:")
    for member in status['members']:
        print(f"  {member['name']}: {member['stateStr']}")
except Exception as e:
    print(f"Failed to check replica set status: {e}")
