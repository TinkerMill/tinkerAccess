#[cfg(feature = "ssr")]
use sea_orm::{ConnectionTrait, Database, DatabaseConnection, DbBackend, DbErr};

#[cfg(feature = "ssr")]
pub async fn db_setup() -> Result<DatabaseConnection, DbErr> {
    let database_url = std::env::var("DATABASE_URL").unwrap_or("sqlite:./db.sqlite".to_string());
    const DB_NAME : &str = "";
    let db = Database::connect(&database_url).await?;

    let db = match db.get_database_backend() {
        DbBackend::MySql => {
            let url = format!("{}/{}", database_url, DB_NAME);
            Database::connect(&url).await?
        }
        DbBackend::Postgres => {
            let url = format!("{}/{}", database_url, DB_NAME);
            Database::connect(&url).await?
        }
        DbBackend::Sqlite => db,
    };

    Ok(db)
}
