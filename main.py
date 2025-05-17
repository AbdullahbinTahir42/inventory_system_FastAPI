from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import model, schemas
from database import SessionLocal, engine, Base

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
    return {"Welcome To our store"}        

# Create item
@app.post("/items/", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    new_item = model.Item(**item.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

# Get all items
@app.get("/items/", response_model=list[schemas.Item])
def get_items(db: Session = Depends(get_db)):
    return db.query(model.Item).all()

# Get item by ID
@app.get("/items/{item_id}", response_model=schemas.Item)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(model.Item).filter(model.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


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

@app.delete("/items/{item_id}", response_model=schemas.Item)    
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(model.Item).filter(model.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    db.commit()
    return item