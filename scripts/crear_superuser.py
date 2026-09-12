import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.usuario import Usuario
from app.security import hash_password

def crear_superuser():

    db= SessionLocal()

    username=input("Username: ").strip()
    email=input("Email: ").strip()
    nombre=input("Nombre: ").strip()
    password=input("Password (min 8 caracteres): ").strip()

    if len(password)<8:
        print(f"❌ La contraseña debe tener al menos 8 caracteres")
        return

    if db.query(Usuario).filter(Usuario.username==username).first():
        print(f"❌ El username '{username}' ya existe")
        return

    superuser =Usuario(
        username=username,
        email=email,
        password_hash=hash_password(password),
        nombre_completo=nombre,
        rol="superuser",
        activo=True,
        requiere_cambio_password=False # El superuser inicial no requiere cambio de password
    )

    db.add(superuser)
    db.commit()
    db.refresh(superuser)
    db.close()

    print(f"\n✅ Superuser creado:")
    print(f"   ID: {superuser.id}")
    print(f"   Username: {superuser.username}")
    print(f"   Email: {superuser.email}")
    print(f"   Rol: {superuser.rol}")

if __name__ == "__main__":
    crear_superuser()

    