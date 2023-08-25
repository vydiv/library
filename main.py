from typing import List

from fastapi import Depends, FastAPI
from fastapi import Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from tortoise.contrib.fastapi import register_tortoise

from auth import create_access_token, SECRET_KEY, ALGORITHM
from models import BookPydantic, Book, BookIn_Pydantic, Status, UserRegister, User, Token, TokenData
from auth import get_user, get_password_hash, verify_password

app = FastAPI()
DATABASE_URL = "sqlite://db.sqlite3"

register_tortoise(
    app,
    db_url=DATABASE_URL,
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# @app.post("/book/")
# async def create_book(book: BookCreate):
#     book_obj = await Book.create(
#         title=book.title,
#         author=book.author,
#         date=book.date,
#         description=book.description
#     )
#     return book_obj

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

from fastapi import HTTPException, status


async def save_user(username: str, hashed_password: str):
    user = await User.create(username=username, hashed_password=hashed_password)
    return user


@app.post("/register/")
async def register(user: UserRegister):
    # Проверка на существование пользователя
    if await get_user(user.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    hashed_password = get_password_hash(user.password)

    # Сохраните пользователя в базе данных
    # Здесь вам нужно реализовать функцию save_user или аналогичную, чтобы сохранить данные пользователя в вашей базе данных.
    new_user = await save_user(username=user.username, hashed_password=hashed_password)

    return new_user  # или можно возвращать только определенные поля, например, {"username": new_user.username}


@app.post("/token/", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await get_user(form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


@app.post("/book/", response_model=BookPydantic)
async def create_book(book: BookIn_Pydantic, current_user: User = Depends(get_current_user)):
    book_obj = await Book.create(**book.dict(exclude_unset=True))
    return await BookPydantic.from_tortoise_orm(book_obj)


@app.get("/book/", response_model=List[BookPydantic])
async def get_books():
    return await BookPydantic.from_queryset(Book.all())


@app.get("/book/{book_id}/", response_model=BookPydantic)
async def get_book(book_id: int):
    return await BookPydantic.from_queryset_single(Book.get(id=book_id))


@app.put("/book/{book_id}/", response_model=BookPydantic, )
async def update_book(book_id: int, book: BookIn_Pydantic, current_user: User = Depends(get_current_user)):
    await Book.filter(id=book_id).update(**book.dict(exclude_unset=True))
    return await BookPydantic.from_queryset_single(Book.get(id=book_id))


@app.delete("/book/{book_id}/", response_model=Status)
async def delete_book(book_id: int, current_user: User = Depends(get_current_user)):
    deleted_count = await Book.filter(id=book_id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    return Status(message=f"Deleted book {book_id}")


@app.get("/search/")
async def search_books(author: str = Query(None), title: str = Query(None)):
    query = Book.all()
    if author:
        query = query.filter(author__icontains=author)  # поиск по части автора
    if title:
        query = query.filter(title__icontains=title)  # поиск по названию
    return await query
