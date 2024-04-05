from sshtunnel import SSHTunnelForwarder
from motor.motor_asyncio import AsyncIOMotorClient


async def query_mongodb(ssh_host=None,
                        ssh_port=None,
                        ssh_username=None,
                        ssh_key_path=None,
                        mongo_host=None,
                        mongo_port=None,
                        db_name=None,
                        collection=None,
                        pipeline=None,
                        ):
    ssh_host = ssh_host or '162.55.103.170'
    ssh_port = ssh_port or 22
    ssh_username = ssh_username or 'root'
    ssh_key_path = ssh_key_path or '~/.ssh/id_rsa'

    mongo_host = mongo_host or '127.0.0.1'
    mongo_port = mongo_port or 27017

    db_name = db_name or 'exchangeV2'
    collection = collection or 'derivative_trades'

    server = SSHTunnelForwarder(
        (ssh_host, ssh_port),
        ssh_username=ssh_username,
        ssh_pkey=ssh_key_path,
        remote_bind_address=(mongo_host, mongo_port)
    )

    server.start()
    uri = f"mongodb://localhost:{server.local_bind_port}/?directConnection=true"
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=20000)
    db = client.get_database(db_name)

    result = await db.get_collection(collection).aggregate(pipeline).to_list(10000000)
    # result = await db[collection].find_one()

    server.stop()
    client.close()

    return result
