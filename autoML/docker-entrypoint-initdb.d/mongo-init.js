// Sélectionner la base de données cible
const db = db.getSiblingDB('Auto_ML_V2');

// Créer un utilisateur avec les permissions appropriées
db.createUser({
  user: process.env.MONGO_USER,
  pwd: process.env.MONGO_PASS,
  roles: [
    { role: 'readWrite', db: 'Auto_ML_V2' },
    { role: 'dbAdmin', db: 'Auto_ML_V2' }
  ]
});

// Créer une collection et insérer un document de test
const collection = db.getCollection('maCollection');
collection.insertOne({ nom: 'test' });
