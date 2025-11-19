"""
Gestion des étudiants avec leurs facultés et promotions
Stockage dans SQLite3
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from db import fetch_one, fetch_all, execute_query

# Définition des facultés et leurs promotions disponibles
FACULTIES = {
    "Informatique": ["L1", "L2", "L3", "L4", "M1", "M2"],
    "Ecole Superieur d'Architecture et Urbanisme": ["Prepa", "L1", "L2", "L3", "M1", "M2"],
    "Droit": ["L1", "L2", "L3", "M1", "M2"],
    "SAE": ["L1", "L2", "L3", "M1", "M2"],
    "Science Technologique": ["Prepa", "L1", "L2", "L3", "M1", "M2"],
    "SIC": ["L1", "L2", "L3", "M1", "M2"],
    "Medecine": ["L1", "L2", "L3", "M1", "M2", "D1", "D2", "D3"]  # Ajout des années de médecine
}

ALL_PROMOTIONS = set()
for promotions in FACULTIES.values():
    ALL_PROMOTIONS.update(promotions)


@dataclass
class Student:
    """Représente un étudiant."""
    id: str
    nom: str
    email: str
    telephone: Optional[str] = None
    langue: str = "fr"
    faculte: str = ""
    promotion: str = ""
    canal_prefere: str = "email"
    actif: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'étudiant en dictionnaire."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Student':
        """Crée un étudiant depuis un dictionnaire."""
        # Filtrer uniquement les champs du dataclass
        valid_fields = {'id', 'nom', 'email', 'telephone', 'langue', 'faculte', 'promotion', 'canal_prefere', 'actif'}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


class StudentsManager:
    """Gestionnaire des étudiants."""
    
    def __init__(self):
        self._students: Dict[str, Student] = {}
        self._load_students()
    
    def _load_students(self):
        """Charge les étudiants depuis la base de données SQLite."""
        try:
            students_data = fetch_all("SELECT * FROM students")
            for student_data in students_data:
                student = Student.from_dict(dict(student_data))
                self._students[student.id] = student
            
            # Si aucun étudiant, créer des exemples
            if not self._students:
                self._create_sample_students()
        except Exception as e:
            print(f"[STUDENTS] Erreur lors du chargement: {e}")
            self._create_sample_students()
    
    def _create_sample_students(self):
        """Crée quelques étudiants d'exemple pour le démarrage."""
        sample_students = [
            Student("etudiant1", "Jean Dupont", "jean.dupont@univ.fr", "+33123456789", "fr", "Informatique", "L1"),
            Student("etudiant2", "Marie Martin", "marie.martin@univ.fr", "+33987654321", "fr", "Informatique", "L2"),
            Student("etudiant3", "Pierre Durand", "pierre.durand@univ.fr", None, "en", "Droit", "M1"),
            Student("etudiant4", "Sophie Bernard", "sophie.bernard@univ.fr", "+33555666777", "fr", "SAE", "L3"),
        ]
        
        for student in sample_students:
            # Vérifier si l'étudiant existe déjà
            existing = fetch_one("SELECT id FROM students WHERE id = ?", (student.id,))
            if not existing:
                execute_query("""
                    INSERT INTO students (id, nom, email, telephone, langue, faculte, promotion, canal_prefere, actif)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    student.id, student.nom, student.email, student.telephone,
                    student.langue, student.faculte, student.promotion,
                    student.canal_prefere, student.actif
                ))
            self._students[student.id] = student
        
        print(f"[STUDENTS] {len(sample_students)} etudiants d'exemple crees")
    
    def get_all_students(self) -> List[Student]:
        """Récupère tous les étudiants."""
        return list(self._students.values())
    
    def get_student(self, student_id: str) -> Optional[Student]:
        """Récupère un étudiant par son ID."""
        return self._students.get(student_id)
    
    def add_student(self, student: Student):
        """Ajoute un étudiant."""
        execute_query("""
            INSERT INTO students (id, nom, email, telephone, langue, faculte, promotion, canal_prefere, actif)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student.id, student.nom, student.email, student.telephone,
            student.langue, student.faculte, student.promotion,
            student.canal_prefere, student.actif
        ))
        self._students[student.id] = student
    
    def update_student(self, student_id: str, **kwargs):
        """Met à jour un étudiant."""
        if student_id not in self._students:
            raise ValueError(f"Étudiant {student_id} non trouvé")
        
        student = self._students[student_id]
        
        # Construire la requête UPDATE dynamiquement
        set_clauses = []
        params = []
        for key, value in kwargs.items():
            if hasattr(student, key):
                setattr(student, key, value)
                set_clauses.append(f"{key} = ?")
                params.append(value)
        
        if set_clauses:
            params.append(student_id)
            query = f"UPDATE students SET {', '.join(set_clauses)} WHERE id = ?"
            execute_query(query, tuple(params))
        
        return student
    
    def delete_student(self, student_id: str):
        """Supprime un étudiant."""
        execute_query("DELETE FROM students WHERE id = ?", (student_id,))
        if student_id in self._students:
            del self._students[student_id]
    
    def filter_students(
        self,
        facultes: Optional[List[str]] = None,
        promotions: Optional[List[str]] = None,
        actif_only: bool = True
    ) -> List[Student]:
        """
        Filtre les étudiants selon les critères en utilisant SQL.
        
        Args:
            facultes: Liste des facultés à inclure (None = toutes)
            promotions: Liste des promotions à inclure (None = toutes)
            actif_only: Ne retourner que les étudiants actifs
        
        Returns:
            Liste des étudiants correspondant aux critères
        """
        # Construire la requête SQL dynamiquement
        query = "SELECT * FROM students WHERE 1=1"
        params = []
        
        if actif_only:
            query += " AND actif = 1"
        
        if facultes:
            placeholders = ','.join(['?' for _ in facultes])
            query += f" AND faculte IN ({placeholders})"
            params.extend(facultes)
        
        if promotions:
            placeholders = ','.join(['?' for _ in promotions])
            query += f" AND promotion IN ({placeholders})"
            params.extend(promotions)
        
        results = fetch_all(query, tuple(params))
        return [Student.from_dict(dict(row)) for row in results]
    
    def get_faculties(self) -> List[str]:
        """Retourne la liste des facultés."""
        return list(FACULTIES.keys())
    
    def get_promotions_for_faculty(self, faculty: str) -> List[str]:
        """Retourne les promotions disponibles pour une faculté."""
        return FACULTIES.get(faculty, [])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne des statistiques sur les étudiants via SQL."""
        # Total et actifs
        total_result = fetch_one("SELECT COUNT(*) as total, SUM(CASE WHEN actif = 1 THEN 1 ELSE 0 END) as actifs FROM students")
        
        stats = {
            "total": total_result['total'] if total_result else 0,
            "actifs": total_result['actifs'] if total_result else 0,
            "par_faculte": {},
            "par_promotion": {}
        }
        
        # Statistiques par faculté
        faculties = fetch_all("""
            SELECT faculte, COUNT(*) as count 
            FROM students 
            WHERE faculte IS NOT NULL AND faculte != ''
            GROUP BY faculte
        """)
        for row in faculties:
            stats["par_faculte"][row['faculte']] = row['count']
        
        # Statistiques par promotion
        promotions = fetch_all("""
            SELECT promotion, COUNT(*) as count 
            FROM students 
            WHERE promotion IS NOT NULL AND promotion != ''
            GROUP BY promotion
        """)
        for row in promotions:
            stats["par_promotion"][row['promotion']] = row['count']
        
        return stats


# Instance globale
students_manager = StudentsManager()

