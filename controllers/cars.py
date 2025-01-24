
from fastapi import APIRouter, HTTPException, Request
from typing import List
from pydantic import BaseModel

router = APIRouter(
    prefix="/cars",
    tags=["cars"]
)

class Car(BaseModel):
    make: str
    model: str
    year: int
    price: float


@router.get("/", response_model=List[dict])
async def get_all_cars(request: Request):
  try:
    async with request.app.state.pgpool.acquire() as connection:
      query = "SELECT * FROM cars"
      rows = await connection.fetch(query)
      cars = [dict(row) for row in rows]
      return cars
  except Exception as e:
    print("Błąd podczas pobierania samochodów:", e)
    raise HTTPException(
        status_code=500,
        detail="Wystąpił błąd podczas pobierania samochodów"
    )

@router.get("/{car_id}")
async def get_car_by_id(car_id: int, request: Request):
  try:
    async with request.app.state.pgpool.acquire() as connection:
      query = "SELECT * FROM cars WHERE id = $1"
      rows = await connection.fetch(query, car_id)

      if not rows:
          raise HTTPException(status_code=404, detail="Samochód nie został znaleziony")

      car = dict(rows[0])
    return car
  except Exception as e:
    print("Błąd podczas pobierania samochodu:", e)
    raise HTTPException(
      status_code=500,
      detail="Wystąpił błąd podczas pobierania samochodu"
    )

@router.post("/")
async def add_car(car: Car, request: Request):
  try:
    async with request.app.state.pgpool.acquire() as connection:
      query = """
        INSERT INTO cars (make, model, year, price)
        VALUES ($1, $2, $3, $4)
        RETURNING id
      """
      result = await connection.fetchrow(query, car.make, car.model, car.year, car.price)

      if not result:
        raise HTTPException(
          status_code=500,
          detail="Nie udało się dodać samochodu do bazy danych"
        )

      car_id = result["id"]
    return {"id": car_id, "message": "Samochód został dodany pomyślnie"}

  except Exception as e:
    print("Błąd podczas dodawania samochodu:", e)
    raise HTTPException(
      status_code=500,
      detail="Wystąpił błąd podczas dodawania samochodu"
    )

@router.delete("/{car_id}")
async def delete_car(car_id: int, request: Request):
    """
    Usuwa samochód o podanym ID z bazy danych.
    """
    try:
        async with request.app.state.pgpool.acquire() as conn:
            delete_query = "DELETE FROM cars WHERE id = $1"
            result = await conn.execute(delete_query, car_id)

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