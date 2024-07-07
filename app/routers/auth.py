# app/routers/auth.py
from typing import Annotated
from datetime import datetime
from fastapi import APIRouter, Response, Depends, BackgroundTasks, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.models import User, BlackListToken
from app.core.database import DBSessionDep
from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException, AuthFailedException
from app.utils.mail import user_mail_event
from app.utils.hash import hash_password, verify_password
from app.utils.authUtils import (
    mail_token,
    create_token_pair,
    refresh_token_state,
    decode_access_token,
    add_refresh_token_cookie,
    authenticateToken
)

from app.schemas.user import (
    User as UserSchema,
    UserRegister,
    ForgotPasswordSchema,
    PasswordResetSchema,
    PasswordUpdateSchema,
    UserUpdate,
)
from app.schemas.jwt import JwtTokenSchema, SuccessResponseScheme, TokenPair
from app.schemas.mail import MailBodySchema, MailTaskSchema

router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"],
    responses={404: {"description": "Not found"}},
)

@router.post("/register", response_model=UserSchema)
async def register(
    data: UserRegister,
    bg_task: BackgroundTasks,
    db: DBSessionDep,
):
    # check if phone number already registered
    user = await User.find_by_phone(db=db, phone=data.phone)
    if user:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    # check if email already registered
    user = await User.find_by_email(db=db, email=data.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered to another number")
        
    # save user to db
    user_data = data.model_dump(exclude={"confirm_password"})
    user = await User.create(db=db, **user_data)

    # send verify email
    user = await User.find_by_phone(db=db, phone=data.phone)
    user_schema = UserSchema.model_validate(user.__dict__)
    verify_token = mail_token(user_schema)

    mail_task_data = MailTaskSchema(
        user=user_schema, body=MailBodySchema(type="verify", token=verify_token)
    )
    bg_task.add_task(user_mail_event, mail_task_data)

    return user_schema


@router.get("/verify", response_model=SuccessResponseScheme)
async def verify(
    token: str,
    db: DBSessionDep
):
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")

    await user.patch(db=db, phone=user.phone, is_disabled=False)
    return {"msg": "Successfully activated"}


@router.post("/token", response_model=TokenPair)
async def login(
    data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    db: DBSessionDep,
):    
    user = await User.authenticate(
        db=db, phone=data.username, password=data.password
    )
    if not user:
        raise BadRequestException(detail="Phone or password not correct")
    if user.is_disabled:
        raise ForbiddenException(detail="Please Verfiy Email")
    user = UserSchema.model_validate(user.__dict__)
    token_pair = create_token_pair(user=user)
    add_refresh_token_cookie(response=response, token=token_pair.refresh.token)
    
    return token_pair


@router.post("/token/refresh")
async def refresh_token(refresh_token: str):
    try:
        new_access_token = refresh_token_state(refresh_token)
    except:
        raise AuthFailedException(detail="Failed to refresh")

    return {"access_token": new_access_token}


@router.post("/logout", response_model=SuccessResponseScheme)
async def logout(
    token: str,
    db: DBSessionDep,
):
    payload = await decode_access_token(token=token, db=db)
    token_data = {"id": payload["jti"], "expire": datetime.utcfromtimestamp(payload["exp"])}
    black_listed = BlackListToken(id=payload["jti"], expire=datetime.utcfromtimestamp(payload["exp"]))
    await black_listed.create(db=db, **token_data)

    return {"msg": "Successfully logged out"}


@router.post("/forgot-password", response_model=SuccessResponseScheme)
async def forgot_password(
    data: ForgotPasswordSchema,
    bg_task: BackgroundTasks,
    db: DBSessionDep,
):
    user = await User.find_by_email(db=db, email=data.email)
    if not user:
        return {"msg": "Email is not registered in our database. Please check the email or register for a new account"}
    else:
        user_schema = UserSchema.model_validate(user.__dict__)
        reset_token = mail_token(user_schema)

        mail_task_data = MailTaskSchema(
            user=user_schema,
            body=MailBodySchema(type="password-reset", token=reset_token),
        )
        bg_task.add_task(user_mail_event, mail_task_data)

    return {"msg": "Reset token sent successfully. Please check your email"}


@router.post("/password-reset", response_model=SuccessResponseScheme)
async def password_reset_token(
    token: str,
    data: PasswordResetSchema,
    db: DBSessionDep,
):
    payload = await decode_access_token(token=token, db=db)
    user = await User.find_by_email(db=db, email=payload["sub"])
    if not user:
        raise NotFoundException(detail="User not found")
    hashed_password = hash_password(data.password)
    await user.patch(db=db, phone=user.phone, password=hashed_password)

    return {"msg": "Password successfully updated"}


@router.post("/password-update", response_model=SuccessResponseScheme)
async def password_update(
    token: str,
    data: PasswordUpdateSchema,
    db: DBSessionDep,
):
    # JWT Authentication
    user = await authenticateToken(db=db, token=token)
    if not user:
        raise NotFoundException(detail="User not found")

    # Validate old password
    if not verify_password(data.old_password, user.password):
        return {"msg": "Old Password Error"}

    hashed_password = hash_password(data.password)
    await user.patch(db=db, phone=user.phone, password=hashed_password)

    return {"msg": "Successfully updated"}


@router.post("/update", response_model=SuccessResponseScheme)
async def update_user(
    data: UserUpdate,
    token: str,
    db: DBSessionDep,
):
    # Decode the access token to get the phone number
    payload = await decode_access_token(token=token, db=db)
    phone = payload["sub"]

    # Fetch the user from the database
    user = await User.find_by_phone(db=db, phone=phone)
    if not user:
        raise NotFoundException(detail="User not found")

    # Update the user with the provided data
    updated_user = await User.patch(db=db, phone=phone, **data.dict(exclude_unset=True))

    return {"msg": "Info Updated Successfully"}
