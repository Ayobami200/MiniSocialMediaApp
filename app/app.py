import uuid
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Absolute imports from your app folder
from app.database import engine, get_db
from app.models import Base, User, Post
import app.schemas as schemas
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user
from app.images import upload_image, delete_image

# Create Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Social Media API")

# --- AUTH & USER ROUTES ---

@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = get_password_hash(user_data.password)
    verification_token = str(uuid.uuid4())
    
    new_user = User(
        email=user_data.email, 
        hashed_password=hashed_pwd,
        verification_token=verification_token
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.get("/verify-email/{token}")
def verify_email(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    user.is_verified = True
    user.verification_token = None
    db.commit()
    return {"message": "Account successfully verified"}

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    #if not user.is_verified:
        #raise HTTPException(status_code=400, detail="Please verify your email first")
        
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/forgot-password")
def forgot_password(data: schemas.ForgotPassword, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if user:
        reset_token = str(uuid.uuid4())
        user.reset_password_token = reset_token
        db.commit()
        # TODO: Send email here with the reset link
    return {"message": "If that email is in our system, a reset link has been sent."}

@app.post("/reset-password")
def reset_password(data: schemas.ResetPassword, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_password_token == data.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    user.hashed_password = get_password_hash(data.new_password)
    user.reset_password_token = None
    db.commit()
    return {"message": "Password successfully reset"}

# --- POST & IMAGE ROUTES ---

@app.post("/posts/", response_model=schemas.PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    content: str = Form(...), 
    image: UploadFile = File(None), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    image_url = None
    imagekit_file_id = None

    if image:
        file_bytes = await image.read()
        upload_data = upload_image(file_bytes, image.filename)
        image_url = upload_data["url"]
        imagekit_file_id = upload_data["file_id"]

    new_post = Post(
        content=content, 
        image_url=image_url, 
        imagekit_file_id=imagekit_file_id,
        owner_id=current_user.id
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@app.delete("/posts/{post_id}")
def delete_user_post(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
        
    if post.imagekit_file_id:
        try:
            delete_image(post.imagekit_file_id)
        except Exception as e:
            print(f"Failed to delete image from ImageKit: {e}")

    db.delete(post)
    db.commit()
    return {"message": "Post successfully deleted"}

@app.get("/posts/", response_model=List[schemas.PostResponse])
def get_posts(db: Session = Depends(get_db)):
    posts = db.query(Post).all()
    return posts