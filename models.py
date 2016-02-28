from sqlalchemy import Table, Column, Integer, String, ForeignKey, DateTime
from database import metadata

users = Table('users', metadata,
              Column('id', Integer, primary_key=True),
              Column('username', String(100), unique=True),
              Column('password', String(100)),
              Column('created_at', DateTime),
              Column('updated_at', DateTime),
              )

posts = Table('posts', metadata,
              Column('id', Integer, primary_key=True),
              Column('user_id', Integer, ForeignKey("users.id"), nullable=False),
              Column('title', String(250)),
              Column('description', String(1000)),
              Column('tags', String(250)),
              Column('created_at', DateTime),
              Column('updated_at', DateTime),
              )

