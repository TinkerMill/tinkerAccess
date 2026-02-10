#[cfg(feature = "ssr")]
use sea_orm::{ConnectionTrait, Database, DatabaseConnection, DbBackend, DbErr};

#[cfg(feature = "ssr")]
pub async fn db_setup() -> Result<DatabaseConnection, DbErr> {
    const DATABASE_URL : &str =
        "sqlite:/home/craisis/Projects/tinkerAccess/tinker-access-server-rs/db.sqlite";
    const DB_NAME : &str = "";
    let db = Database::connect(DATABASE_URL).await?;

    let db = match db.get_database_backend() {
        DbBackend::MySql => {
            let url = format!("{}/{}", DATABASE_URL, DB_NAME);
            Database::connect(&url).await?
        }
        DbBackend::Postgres => {
            let url = format!("{}/{}", DATABASE_URL, DB_NAME);
            Database::connect(&url).await?
        }
        DbBackend::Sqlite => db,
    };

    Ok(db)
}
