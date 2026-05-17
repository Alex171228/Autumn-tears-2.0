const appDbName = process.env.MONGO_DB_NAME || "webapp_robot";
const appUsername = process.env.MONGO_APP_USERNAME;
const appPassword = process.env.MONGO_APP_PASSWORD;

if (!appUsername || !appPassword) {
  throw new Error("MONGO_APP_USERNAME and MONGO_APP_PASSWORD must be set");
}

const appDb = db.getSiblingDB(appDbName);

if (!appDb.getUser(appUsername)) {
  appDb.createUser({
    user: appUsername,
    pwd: appPassword,
    roles: [{ role: "readWrite", db: appDbName }],
  });
}
