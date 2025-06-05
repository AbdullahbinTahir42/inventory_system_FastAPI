from fastapi import FastAPI, Depends, HTTPException, Query, Request, Form, Path
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import model, schemas
from database import SessionLocal, engine, Base
from utils import hash_password, verify_password
from pydantic import ValidationError

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

def is_admin(request: Request, db: Session):
    username = request.cookies.get("user")
    if not username:
        return False
    user = db.query(model.User).filter(model.User.username == username).first()
    return user and (user.username == "admin" or user.nickname == "admin")

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("user")
    return response

@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request, db: Session = Depends(get_db)):
    if not is_admin(request, db):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    if not is_admin(request, db):
        return RedirectResponse(url="/", status_code=303)

    existing_user = db.query(model.User).filter(model.User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    new_user = model.User(username=username, hashed_password=hash_password(password), email=email)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

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
    username = request.cookies.get("user")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    user = db.query(model.User).filter(model.User.username == username).first()
    items = db.query(model.Item).all()
    return templates.TemplateResponse("items.html", {"request": request, "items": items, "user": user})

@app.get("/item/{item_id}", response_class=HTMLResponse)
def item_detail_ui(item_id: int, request: Request, db: Session = Depends(get_db)):
    username = request.cookies.get("user")
    user = db.query(model.User).filter(model.User.username == username).first()
    item = db.query(model.Item).filter(model.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return templates.TemplateResponse("item.html", {"request": request, "item": item, "user": user})

@app.get("/add", response_class=HTMLResponse)
def add_item_form_ui(request: Request, db: Session = Depends(get_db)):
    if not is_admin(request, db):
        return RedirectResponse(url="/")
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
    if not is_admin(request, db):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        item_data = schemas.ItemBase(
            name=name,
            description=description,
            price=price,
            quantity=quantity
        )
    except ValidationError:
        raise HTTPException(status_code=400, detail="Invalid item data")

    new_item = model.Item(**item_data.model_dump())
    db.add(new_item)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/delete/{item_id}")
def delete_item_ui(item_id: int, request: Request, db: Session = Depends(get_db)):
    if not is_admin(request, db):
        return RedirectResponse(url="/")
    item = db.query(model.Item).filter(model.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/edit/{item_id}", response_class=HTMLResponse)
def edit_item_form(item_id: int, request: Request, db: Session = Depends(get_db)):
    if not is_admin(request, db):
        return RedirectResponse(url="/")
    item = db.query(model.Item).filter(model.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return templates.TemplateResponse("edit_item.html", {"request": request, "item": item})

@app.post("/edit/{item_id}")
def update_item(
    item_id: int = Path(...),
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    quantity: int = Form(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    if not is_admin(request, db):
        raise HTTPException(status_code=403, detail="Only admin can edit items")
    item = db.query(model.Item).filter(model.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    try:
        item_data = schemas.ItemBase(
            name=name,
            description=description,
            price=price,
            quantity=quantity
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    item.name = item_data.name
    item.description = item_data.description
    item.price = item_data.price
    item.quantity = item_data.quantity
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/grant_access", response_class=HTMLResponse)
def access_ui(request: Request, db: Session = Depends(get_db)):
    if request.cookies.get("user") != "admin":
        return RedirectResponse(url="/")
    users = db.query(model.User).filter(model.User.username != "admin").all()
    return templates.TemplateResponse("user_access.html", {"request": request, "users": users})

@app.post("/grant_access")
def grant_access(
    request: Request,
    username: str = Form(...),
    db: Session = Depends(get_db)
):
    if not is_admin(request, db):
        return RedirectResponse(url="/")
    user = db.query(model.User).filter(model.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.nickname = None if user.nickname == "admin" else "admin"
    db.commit()
    return RedirectResponse(url="/grant_access", status_code=303)
