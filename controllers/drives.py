
from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict
from pydantic import BaseModel, Field
from datetime import date, time

router = APIRouter(
    prefix="/drives",
    tags=["drives"]
)


class TestDriveData(BaseModel):
    user_id: int = Field(..., description="ID użytkownika")
    car_id: int = Field(..., description="ID samochodu")
    test_drive_date: date = Field(..., description="Data jazdy próbnej")
    test_drive_time: time = Field(..., description="Godzina jazdy próbnej")
    status: str = Field(default="scheduled", description="Status rezerwacji")


@router.get("/car/{car_id}", response_model=List[Dict])
async def get_car_test_drives(car_id: int, request: Request):
    """
    Zwraca jazdy próbne dla danego samochodu na podstawie jego ID.
    """
    query = """
        SELECT 
            t.test_drive_date, 
            t.test_drive_time
        FROM test_drives t
        WHERE t.car_id = $1
        ORDER BY t.test_drive_date, t.test_drive_time
    """
    try:
        async with request.app.state.pgpool.acquire() as conn:
            rows = await conn.fetch(query, car_id)

            # Konwertujemy dane do listy słowników
            result = [
                {
                    "test_drive_date": row["test_drive_date"].strftime("%Y-%m-%d"),
                    "test_drive_time": row["test_drive_time"].strftime("%H:%M:%S"),
                }
                for row in rows
            ]

            return result

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Błąd podczas pobierania jazd próbnych dla samochodu o ID {car_id}: {e}"
        )


@router.get("/", response_model=List[Dict])
async def get_all_test_drives(request: Request):
    """
    Zwraca wszystkie jazdy próbne z informacją
    o imieniu i nazwisku użytkownika oraz marce i modelu samochodu.
    """
    query = """
        SELECT 
            t.id, 
            t.test_drive_date, 
            t.test_drive_time,
            t.status,
            t.created_at,
            u.first_name AS user_first_name,
            u.last_name AS user_last_name,
            c.brand AS car_brand,
            c.model AS car_model
        FROM test_drives t
        JOIN users u ON t.user_id = u.id
        JOIN cars c ON t.car_id = c.id
        ORDER BY t.id
    """
    try:
        async with request.app.state.pgpool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas pobierania jazd próbnych: {e}")


@router.get("/{test_drive_id}", response_model=Dict)
async def get_test_drive_by_id(test_drive_id: int, request: Request):
    """
    Zwraca jedną jazdę próbną (po id) z informacją
    o imieniu i nazwisku użytkownika oraz marce i modelu samochodu.
    """
    query = """
        SELECT 
            t.id, 
            t.test_drive_date, 
            t.test_drive_time,
            t.status,
            t.created_at,
            u.first_name AS user_first_name,
            u.last_name AS user_last_name,
            c.brand AS car_brand,
            c.model AS car_model
        FROM test_drives t
        JOIN users u ON t.user_id = u.id
        JOIN cars c ON t.car_id = c.id
        WHERE t.id = $1
    """
    try:
        async with request.app.state.pgpool.acquire() as conn:
            row = await conn.fetchrow(query, test_drive_id)
            if row:
                return dict(row)
            else:
                raise HTTPException(status_code=404, detail="Jazda próbna o podanym ID nie istnieje.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd podczas pobierania jazdy próbnej: {e}")


@router.post("/", response_model=Dict)
async def create_test_drive(test_drive_data: TestDriveData, request: Request):
    print("DEBUG: Otrzymane test_drive_data:", test_drive_data.dict())

    insert_query = """
        INSERT INTO test_drives 
            (user_id, car_id, test_drive_date, test_drive_time, status)
        VALUES 
            ($1, $2, $3, $4, $5)
        RETURNING id
    """
    select_query = """
        SELECT 
            t.id, 
            t.test_drive_date, 
            t.test_drive_time,
            t.status,
            t.created_at,
            u.first_name AS user_first_name,
            u.last_name AS user_last_name,
            c.brand AS car_brand,
            c.model AS car_model
        FROM test_drives t
        JOIN users u ON t.user_id = u.id
        JOIN cars c ON t.car_id = c.id
        WHERE t.id = $1
    """
    try:
        async with request.app.state.pgpool.acquire() as conn:
            # Wstaw nowy test drive
            new_id = await conn.fetchval(
                insert_query,
                test_drive_data.user_id,
                test_drive_data.car_id,
                test_drive_data.test_drive_date,
                test_drive_data.test_drive_time,
                test_drive_data.status
            )

            # Odczytaj pełne informacje o utworzonej jeździe
            row = await conn.fetchrow(select_query, new_id)
            return dict(row)

    except asyncpg.exceptions.UniqueViolationError:
        raise HTTPException(status_code=400, detail="Rezerwacja na ten czas jest już zajęta.")

    except Exception as e:
        import traceback
        traceback.print_exc()  # Logowanie szczegółów błędu w konsoli
        raise HTTPException(status_code=500, detail=f"Błąd podczas dodawania jazdy próbnej: {e}")
    

    
@router.delete("/{test_id}")
async def delete_car(test_id: int, request: Request):
    """
    Usuwa samochód o podanym ID z bazy danych.
    """
    try:
        async with request.app.state.pgpool.acquire() as conn:
            delete_query = "DELETE FROM test_drives WHERE id = $1"
            result = await conn.execute(delete_query, test_id)

            # W zależności od używanej biblioteki / wersji asyncpg,
            # `execute` może zwracać np. "DELETE 0" lub liczbę usuniętych wierszy.
            # Sprawdźmy, czy coś zostało usunięte:
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Samochód nie został znaleziony.")

            return {"message": "Samochód został usunięty pomyślnie."}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Wystąpił błąd podczas usuwania samochodu: {e}"
        )