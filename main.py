from fastapi import FastAPI, Depends, HTTPException, Query, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import model, schemas
from database import SessionLocal, engine, Base
from utils import hash_password, verify_password

hashed = hash_password("mysecret")
print(verify_password("mysecret", hashed))  # True


Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def home_ui(request: Request, db: Session = Depends(get_db)):
    items = db.query(model.Item).all()
    return templates.TemplateResponse("items.html", {"request": request, "items": items})


@app.get("/item/{item_id}", response_class=HTMLResponse)
def item_detail_ui(item_id: int, request: Request, db: Session = Depends(get_db)):
    item = db.query(model.Item).filter(model.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return templates.TemplateResponse("item.html", {"request": request, "item": item})


@app.get("/add", response_class=HTMLResponse)
def add_item_form_ui(request: Request):
    return templates.TemplateResponse("add_item.html", {"request": request})


@app.post("/add")
def add_item_ui(
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    quantity: int = Form(...),
    admin: bool = Query(False),
    db: Session = Depends(get_db)
):
    if not admin:
        raise HTTPException(status_code=403, detail="Only admin can add items")
    new_item = model.Item(name=name, description=description, price=price, quantity=quantity)
    db.add(new_item)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/delete/{item_id}")
def delete_item_ui(item_id: int, admin: bool = Query(False), db: Session = Depends(get_db)):
    if not admin:
        raise HTTPException(status_code=403, detail="Only admin can delete items")
    item = db.query(model.Item).filter(model.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return RedirectResponse(url="/", status_code=303)
