print("🚀 Initialisation de MongoDB...");
db = db.getSiblingDB(process.env.MONGO_DB_NAME || "Auto_ML_V2"); // Sélectionne la DB de l'ENV
db.createUser({
  user: process.env.MONGO_USER,
  pwd: process.env.MONGO_PASS,
  roles: [{ role: "readWrite", db: process.env.MONGO_DB_NAME || "Auto_ML_V2" }]
});
print("✅ Utilisateur créé avec succès !");
