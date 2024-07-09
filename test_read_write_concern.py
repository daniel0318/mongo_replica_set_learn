import time
import subprocess
import pytest

from pymongo import MongoClient
from pymongo.errors import OperationFailure
from pymongo import WriteConcern
from pymongo.read_concern import ReadConcern

mongodb_uri = "mongodb://localhost:27018/?replicaSet=rs0"
insert_many_documents = [
    {"name": "Alice", "age": 30, "city": "New York"},
    {"name": "Bob", "age": 25, "city": "San Francisco"},
    {"name": "Charlie", "age": 35, "city": "Los Angeles"}
]
def handle_connect_from_network(handle, container_name):
    command = ["docker", "network", handle, _network_name, container_name]
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as e:
        pass

_network_name = "mongo-cluster"

# Setup and Teardown
@pytest.fixture(scope="function")
def mongo_collection():
    # Setup: ensure every mongo replicat is connected and clean the collection
    for i in range(1, 4+1):
        handle_connect_from_network("connect", f"mongo{i}")
    client = MongoClient(mongodb_uri, directConnection=True)
    db = client.test_database
    collection = db.test_collection
    collection.delete_many({})
   
    yield collection

    # Teardown: Do nothing

def test_normal_insert(mongo_collection):
    try:
        result = mongo_collection.insert_many(insert_many_documents)
    except OperationFailure as e:
        pytest.fail(f"Insertion failed: {e}")

    found_documents = list(mongo_collection.find())
    assert len(found_documents) == 3

@pytest.mark.parametrize("write_concern_value", 
        [
            1,          # expected unblock
            "majority", # expected block 
        ]
    )
@pytest.mark.timeout(5)
def test_write_majority_w1(mongo_collection, write_concern_value):
    handle_connect_from_network("disconnect", "mongo3")
    handle_connect_from_network("disconnect", "mongo4")

    # Because lost 2 nodes, insert will block until majority nodes connected
    result = mongo_collection.with_options(write_concern=WriteConcern(write_concern_value)).insert_many(insert_many_documents)
    found_documents = list(mongo_collection.find())
    assert len(found_documents) == 3

def test_read_majority_w1(mongo_collection):
    
    # INSERT 2 documents with write:1
    result = mongo_collection.with_options(write_concern=WriteConcern(1))\
        .insert_many(insert_many_documents[0:2])

    # read documents with two type of read concerns
    local_found_docs = list(mongo_collection.with_options(read_concern=ReadConcern("local")).find())
    majority_found_docs = list(mongo_collection.with_options(read_concern=ReadConcern("majority")).find())
    
    # with read:local SHOULD get 2, bc client is MASTER
    assert len(local_found_docs) == 2
    # with read:majority SHOULD get 0, bc other node not sync yet
    assert len(majority_found_docs) == 0

    # sleep 3 seconds, then other nodes should sync, if no accident 
    time.sleep(3)
    
    local_found_docs = list(mongo_collection.with_options(read_concern=ReadConcern("local")).find())
    majority_found_docs = list(mongo_collection.with_options(read_concern=ReadConcern("majority")).find())
    assert len(local_found_docs) == 2
    assert len(majority_found_docs) == 2
    
    handle_connect_from_network("disconnect", "mongo3")
    handle_connect_from_network("disconnect", "mongo4")
    
    # INSERT the third document
    result = mongo_collection.with_options(write_concern=WriteConcern(1))\
        .insert_many(insert_many_documents[2:])

    local_found_docs = list(mongo_collection.with_options(read_concern=ReadConcern("local")).find())
    majority_found_docs = list(mongo_collection.with_options(read_concern=ReadConcern("majority")).find())
    # with read:local SHOULD get 3, because client is MASTER
    assert len(local_found_docs) == 3
    # with read:majority SHOULD get 2, because two node disconnect, 
    # the third document doesn't belong to majority
    assert len(majority_found_docs) == 2

    time.sleep(3)

    local_found_docs = list(mongo_collection.with_options(read_concern=ReadConcern("local")).find())
    majority_found_docs = list(mongo_collection.with_options(read_concern=ReadConcern("majority")).find())
    # AFTER the sleep, still remains the same
    assert len(local_found_docs) == 3
    assert len(majority_found_docs) == 2



if __name__ == "__main__":
    pytest.main(["-v", __file__])

