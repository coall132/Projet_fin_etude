from pymongo import MongoClient

def get_db_mongo(db_name, host, port, user, password):
    try:
        mongo_uri = f"mongodb://{user}:{password}@{host}:{port}/{db_name}?authSource={db_name}"
        client = MongoClient(mongo_uri)
        db = client[db_name]
        return db, client
    except Exception as e:
        print(f"Erreur de connexion à MongoDB : {e}")
        return None, None
