from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import model, schemas
from database import SessionLocal, engine, Base
from typing import Optional, List

Base.metadata.create_all(bind=engine)  # create tables

app = FastAPI()

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Welcome To our store"}

# Create item
@app.post("/items/", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    new_item = model.Item(**item.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

# Get all items with optional filters
@app.get("/items/", response_model=List[schemas.Item])
def get_items(
    name: Optional[str] = Query(None, description="Filter by item name"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    min_quantity: Optional[int] = Query(None, description="Minimum quantity"),
    db: Session = Depends(get_db)
):
    query = db.query(model.Item)

    if name:
        query = query.filter(model.Item.name.ilike(f"%{name}%"))
    if min_price is not None:
        query = query.filter(model.Item.price >= min_price)
    if max_price is not None:
        query = query.filter(model.Item.price <= max_price)
    if min_quantity is not None:
        query = query.filter(model.Item.quantity >= min_quantity)

    return query.all()

# Get item by ID
@app.get("/items/{item_id}", response_model=schemas.Item)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(model.Item).filter(model.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# Update item
@app.put("/items/{item_id}", response_model=schemas.Item)
def update_item(item_id: int, item: schemas.ItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(model.Item).filter(model.Item.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    for key, value in item.model_dump(exclude_unset=True).items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

# Delete item
@app.delete("/items/{item_id}", response_model=schemas.Item)    
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(model.Item).filter(model.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    return item
