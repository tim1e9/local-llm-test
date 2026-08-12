"""
Utility script to seed test data into the database.
Run this to create sample users and vacation balances.
"""
from datetime import datetime
from db_service import DatabaseService


def seed_database():
    db = DatabaseService('vacation.db')
    current_year = datetime.now().year
    
    # Create admin user
    admin_id = db.create_user('admin', 'admin@example.com', 'System Admin')
    if admin_id:
        db.assign_role_to_user(admin_id, 'ADMIN')
        db.assign_role_to_user(admin_id, 'MANAGER')
        print(f"Created admin user (id={admin_id})")
    
    # Create manager user
    manager_id = db.create_user('jdoe', 'manager@example.com', 'John Doe')
    if manager_id:
        db.assign_role_to_user(manager_id, 'MANAGER')
        print(f"Created manager user (id={manager_id})")
    
    # Create employee users with manager assignment
    emp1_id = db.create_user('janedoe', 'employee1@example.com', 'Jane Doe', manager_id)
    if emp1_id:
        db.assign_role_to_user(emp1_id, 'EMPLOYEE')
        db.create_vacation_balance(emp1_id, current_year, 80)  # 10 days
        print(f"Created employee user (id={emp1_id})")
    
    emp2_id = db.create_user('bobsmith', 'employee2@example.com', 'Bob Smith', manager_id)
    if emp2_id:
        db.assign_role_to_user(emp2_id, 'EMPLOYEE')
        db.create_vacation_balance(emp2_id, current_year, 60)  # 7.5 days
        print(f"Created employee user (id={emp2_id})")
    
    print("Database seeded successfully!")


if __name__ == '__main__':
    seed_database()
