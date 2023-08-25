from pydantic import BaseModel
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.models import Model


class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=255)
    hashed_password = fields.CharField(max_length=255)


class UserRegister(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str = None


class Book(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255)
    author = fields.CharField(max_length=255)
    date = fields.DateField()
    description = fields.TextField()

    class Meta:
        table = "books"


class Status(BaseModel):
    message: str


BookPydantic = pydantic_model_creator(Book, name="BookCreate")
BookIn_Pydantic = pydantic_model_creator(Book, name="BookIn", exclude_readonly=True)
# class BookCreate(BaseModel):
#     id: int
#     title: Union[str, None] = None
#     author: Union[str, None] = None
#     date: Union[datetime, None] = Body(default=None)
#     description: Union[str, None] = None
