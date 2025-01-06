from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict
from pydantic import BaseModel

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

class User(BaseModel):
    login: str
    email: str
    phone: int
    name: float

@router.get("/", response_model =List[dict])
async def get_users(request: Request):
  try:
    async with request.app.state.pgpool.acquire() as connection:
      query = "select * from users"
      rows = await connection.fetch(query)
      users = [dict(user) for user in rows]
      return users
  except Exception as e:
    print("blad podczas pobierania uzytkownikow", e)
    raise HTTPException(
       status_code= 500,
       detail = "blad podczas pobierania uzytkownikow"
    )
@router.get("/{user_id}")
async def get_user_by_id(user_id: int, request: Request):
  try:
    async with request.app.state.pgpool.acquire() as connection:
      query = "select * from users where id = $1"
      row =await connection.fetch(query,user_id)

      if not row:
        raise HTTPException(status_code=404, detail="Uzytkownik nie został znaleziony")

      user = dict(row[0])
    return user
  except Exception as e:
    print("Błąd podczas pobierania uzytkownika:", e)
    raise HTTPException(
      status_code=500,
      detail="Wystąpił błąd podczas pobierania uzytkownika"
    )

@router.post("/")
async def add_user(user: dict, request: Request):

  try:
    async with request.app.state.pgpool.acquire() as conn:
      query = """
        INSERT INTO users 
            (login, password_hash, email, phone, first_name, last_name, preferred_test_drive_time, created_at)
        VALUES
            ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id
      """
      record = await conn.fetchrow(
        query,
        user.get("login"),
        user.get("password_hash"),
        user.get("email"),
        user.get("phone"),
        user.get("first_name"),
        user.get("last_name"),
        user.get("preferred_test_drive_time"),  
        user.get("created_at")     
      )            

      return {"message": "User added", "user_id": record["id"]}

  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Błąd podczas dodawania użytkownika: {e}")

@router.get("/{user_id}/test_drives", response_model=List[Dict])
async def get_user_test_drives(user_id: int, request: Request):
    """
    Zwraca listę jazd próbnych przypisanych do konkretnego użytkownika (user_id).
    """

    # (Opcjonalnie) Najpierw możesz sprawdzić, czy dany użytkownik istnieje:
    check_user_query = "SELECT id FROM users WHERE id = $1"
    test_drives_query = """
        SELECT
            t.id AS test_drive_id,
            t.test_drive_date,
            t.test_drive_time,
            t.status,
            t.created_at,
            c.brand AS car_brand,
            c.model AS car_model
        FROM test_drives t
        JOIN cars c ON t.car_id = c.id
        WHERE t.user_id = $1
        ORDER BY t.test_drive_date, t.test_drive_time
    """

    try:
        async with request.app.state.pgpool.acquire() as conn:
            # Sprawdź, czy użytkownik istnieje
            user_row = await conn.fetchrow(check_user_query, user_id)
            if not user_row:
                raise HTTPException(status_code=404, detail="Użytkownik nie istnieje.")

            # Pobierz jazdy próbne dla tego użytkownika
            rows = await conn.fetch(test_drives_query, user_id)
            return [dict(row) for row in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas pobierania jazd próbnych: {e}")
    
@router.delete("/{user_id}")
async def delete_car(user_id: int, request: Request):
    """
    Usuwa samochód o podanym ID z bazy danych.
    """
    try:
        async with request.app.state.pgpool.acquire() as conn:
            delete_query = "DELETE FROM users WHERE id = $1"
            result = await conn.execute(delete_query, user_id)

            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Samochód nie został znaleziony.")

            return {"message": "Samochód został usunięty pomyślnie."}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Wystąpił błąd podczas usuwania samochodu: {e}"
        )