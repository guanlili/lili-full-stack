import json
import datetime
import uuid
from typing import List, Optional, Any
from sqlmodel import Session, select, delete
from app.core.security import get_password_hash, verify_password
from app.models import CacheEntry, SearchHistory, ScholarSearchResults, User, UserCreate, UserUpdate, Item, ItemCreate

# Cache CRUD

def get_cache_entry(*, session: Session, key: str) -> Optional[CacheEntry]:
    statement = select(CacheEntry).where(CacheEntry.key == key)
    return session.exec(statement).first()

def create_cache_entry(*, session: Session, key: str, result: ScholarSearchResults) -> CacheEntry:
    cache = CacheEntry(
        key=key,
        result_json=json.dumps(result.dict()),
    )
    session.add(cache)
    session.commit()
    session.refresh(cache)
    return cache

def delete_cache_entry(*, session: Session, key: str) -> None:
    cache = get_cache_entry(session=session, key=key)
    if cache:
        session.delete(cache)
        session.commit()

# Search History CRUD

def create_history_entry(*, session: Session, key: str, url: Optional[str], summary: Optional[str], source: str) -> SearchHistory:
    history = SearchHistory(
        key=key,
        url=url,
        result_summary=summary,
        source=source,
    )
    session.add(history)
    session.commit()
    session.refresh(history)
    return history

def list_history(*, session: Session, keyword: Optional[str] = None, start_date: Optional[datetime.datetime] = None, end_date: Optional[datetime.datetime] = None) -> List[SearchHistory]:
    statement = select(SearchHistory)
    if keyword:
        statement = statement.where(SearchHistory.key.contains(keyword))
    if start_date:
        statement = statement.where(SearchHistory.created_at >= start_date)
    if end_date:
        statement = statement.where(SearchHistory.created_at <= end_date)
    return session.exec(statement).all()

def delete_history_entry(*, session: Session, history_id: str) -> None:
    history = session.get(SearchHistory, history_id)
    if history:
        # Also delete cache entry with same key
        delete_cache_entry(session=session, key=history.key)
        session.delete(history)
        session.commit()

def clear_history(*, session: Session) -> None:
    session.exec(delete(CacheEntry))
    session.exec(delete(SearchHistory))
    session.commit()



def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item
