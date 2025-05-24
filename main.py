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


@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = db.query(model.User).filter(model.User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    new_user = model.User(username=username, hashed_password=hash_password(password))
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(model.User).filter(model.User.username == username).first()
    if user and verify_password(password, user.hashed_password):
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie("user", username)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

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
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    quantity: int = Form(...),
    db: Session = Depends(get_db)
):
    user = request.cookies.get("user")
    if not user:
        raise HTTPException(status_code=403, detail="Login required")

    new_item = model.Item(name=name, description=description, price=price, quantity=quantity)
    db.add(new_item)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/delete/{item_id}")
def delete_item_ui(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = request.cookies.get("user")
    if not user:
        raise HTTPException(status_code=403, detail="Login required to delete items")

    item = db.query(model.Item).filter(model.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if user != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete items")

    db.delete(item)
    db.commit()
    return RedirectResponse(url="/", status_code=303)