"""
Module de gestion de la base de données SQLite3
Fournit les fonctions de connexion et d'interaction avec la base de données
"""
import sqlite3
import os
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple


DATABASE_FILE = "notifications.db"


@contextmanager
def get_db_connection():
    """
    Context manager pour obtenir une connexion à la base de données.
    Gère automatiquement le commit/rollback et la fermeture.
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
    """
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
    
    # Activer le mode WAL pour meilleure concurrence
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")  # Activer les contraintes FK
    
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_query(query: str, params: Tuple = ()) -> None:
    """
    Exécute une requête SQL sans retour de résultat.
    Utile pour INSERT, UPDATE, DELETE.
    
    Args:
        query: Requête SQL (avec ? pour les paramètres)
        params: Tuple des paramètres
    """
    with get_db_connection() as conn:
        conn.execute(query, params)


def execute_many(query: str, params_list: List[Tuple]) -> None:
    """
    Exécute une requête SQL plusieurs fois avec différents paramètres.
    Utile pour les insertions en masse.
    
    Args:
        query: Requête SQL
        params_list: Liste de tuples de paramètres
    """
    with get_db_connection() as conn:
        conn.executemany(query, params_list)


def fetch_one(query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
    """
    Récupère un seul résultat de la base de données.
    
    Args:
        query: Requête SQL SELECT
        params: Tuple des paramètres
        
    Returns:
        Dictionnaire représentant la ligne ou None si aucun résultat
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        result = cursor.execute(query, params).fetchone()
        return dict(result) if result else None


def fetch_all(query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
    """
    Récupère tous les résultats d'une requête.
    
    Args:
        query: Requête SQL SELECT
        params: Tuple des paramètres
        
    Returns:
        Liste de dictionnaires représentant les lignes
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        results = cursor.execute(query, params).fetchall()
        return [dict(row) for row in results]


def execute_script(script: str) -> None:
    """
    Exécute un script SQL complet (plusieurs requêtes).
    Utile pour les migrations.
    
    Args:
        script: Script SQL contenant plusieurs requêtes
    """
    with get_db_connection() as conn:
        conn.executescript(script)


def init_db(force: bool = False) -> None:
    """
    Initialise la base de données en créant toutes les tables.
    
    Args:
        force: Si True, supprime et recrée toutes les tables
    """
    if force and os.path.exists(DATABASE_FILE):
        print(f"[DB] Suppression de l'ancienne base de données: {DATABASE_FILE}")
        os.remove(DATABASE_FILE)
    
    migrations_file = os.path.join("migrations", "001_initial_schema.sql")
    
    if not os.path.exists(migrations_file):
        print(f"[DB] Fichier de migration introuvable: {migrations_file}")
        return
    
    print(f"[DB] Initialisation de la base de données...")
    
    with open(migrations_file, 'r', encoding='utf-8') as f:
        schema = f.read()
    
    execute_script(schema)
    print(f"[DB] Base de donnees initialisee: {DATABASE_FILE}")


def db_exists() -> bool:
    """
    Vérifie si la base de données existe.
    
    Returns:
        True si le fichier de base de données existe
    """
    return os.path.exists(DATABASE_FILE)


def get_table_names() -> List[str]:
    """
    Récupère la liste de toutes les tables dans la base de données.
    
    Returns:
        Liste des noms de tables
    """
    query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """
    results = fetch_all(query)
    return [row['name'] for row in results]


def get_table_info(table_name: str) -> List[Dict[str, Any]]:
    """
    Récupère les informations sur les colonnes d'une table.
    
    Args:
        table_name: Nom de la table
        
    Returns:
        Liste des informations sur les colonnes
    """
    query = f"PRAGMA table_info({table_name})"
    return fetch_all(query)


def table_exists(table_name: str) -> bool:
    """
    Vérifie si une table existe dans la base de données.
    
    Args:
        table_name: Nom de la table
        
    Returns:
        True si la table existe
    """
    query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """
    result = fetch_one(query, (table_name,))
    return result is not None


def get_last_insert_id() -> Optional[int]:
    """
    Récupère l'ID de la dernière insertion.
    
    Returns:
        ID de la dernière ligne insérée ou None
    """
    result = fetch_one("SELECT last_insert_rowid() as id")
    return result['id'] if result else None


# ==================== FONCTIONS UTILITAIRES ====================

def backup_database(backup_file: str = None) -> str:
    """
    Crée une sauvegarde de la base de données.
    
    Args:
        backup_file: Nom du fichier de backup (optionnel)
        
    Returns:
        Chemin du fichier de backup créé
    """
    if not backup_file:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_{timestamp}.db"
    
    with get_db_connection() as conn:
        backup_conn = sqlite3.connect(backup_file)
        conn.backup(backup_conn)
        backup_conn.close()
    
    print(f"[DB] Backup cree: {backup_file}")
    return backup_file


def get_database_stats() -> Dict[str, Any]:
    """
    Récupère des statistiques sur la base de données.
    
    Returns:
        Dictionnaire contenant les statistiques
    """
    stats = {
        "database_file": DATABASE_FILE,
        "exists": db_exists(),
        "tables": {},
        "total_size": 0
    }
    
    if db_exists():
        stats["total_size"] = os.path.getsize(DATABASE_FILE)
        stats["tables"] = {}
        
        for table in get_table_names():
            count_query = f"SELECT COUNT(*) as count FROM {table}"
            result = fetch_one(count_query)
            stats["tables"][table] = result['count'] if result else 0
    
    return stats


if __name__ == "__main__":
    # Test de connexion
    print("=" * 60)
    print("Test du module db.py")
    print("=" * 60)
    
    if db_exists():
        print(f"\n[OK] Base de donnees trouvee: {DATABASE_FILE}")
        print(f"\nTables disponibles:")
        for table in get_table_names():
            print(f"  - {table}")
        
        print(f"\nStatistiques:")
        stats = get_database_stats()
        print(f"  Taille: {stats['total_size']} bytes")
        print(f"  Nombre de tables: {len(stats['tables'])}")
        for table, count in stats['tables'].items():
            print(f"    - {table}: {count} enregistrements")
    else:
        print(f"\n[INFO] Base de donnees non trouvee: {DATABASE_FILE}")
        print("Executez init_db() pour creer la base de donnees")
    
    print("\n" + "=" * 60)
