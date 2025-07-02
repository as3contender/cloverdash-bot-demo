from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
import logging

from models.auth import Token, User, UserCreate, TelegramAuth, LoginRequest
from services.user_service import user_service
from services.security import security_service
from config.settings import settings

logger = logging.getLogger(__name__)

# Создаем роутер для аутентификации
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate):
    """
    Регистрация нового пользователя
    """
    try:
        # Проверяем, существует ли пользователь с таким email
        if user_in.email:
            existing_user = await user_service.get_user_by_email(user_in.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким email уже существует"
                )

        # Проверяем, существует ли пользователь с таким username
        if user_in.username:
            existing_user = await user_service.get_user_by_username(user_in.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким username уже существует"
                )

        # Проверяем, существует ли пользователь с таким Telegram ID
        if user_in.telegram_id:
            existing_user = await user_service.get_user_by_telegram_id(user_in.telegram_id)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким Telegram ID уже существует"
                )

        # Создаем пользователя
        user = await user_service.create_user(user_in)
        logger.info(f"User registered successfully: {user.id}")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при регистрации пользователя"
        )


@auth_router.post("/login", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    OAuth2 совместимый логин, получение токена доступа для последующих запросов
    """
    try:
        user = await user_service.authenticate_user(form_data.username, form_data.password)
        if not user:
            logger.warning(f"Failed login attempt for: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email/username или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = security_service.create_access_token(data={"sub": user.id}, expires_delta=access_token_expires)

        logger.info(f"User logged in successfully: {user.id}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при входе в систему")


@auth_router.post("/login/json", response_model=Token)
async def login_json(login_data: LoginRequest):
    """
    Альтернативный логин через JSON (для клиентов, которые не поддерживают OAuth2PasswordRequestForm)
    """
    try:
        user = await user_service.authenticate_user(login_data.username, login_data.password)
        if not user:
            logger.warning(f"Failed login attempt for: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email/username или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = security_service.create_access_token(data={"sub": user.id}, expires_delta=access_token_expires)

        logger.info(f"User logged in successfully: {user.id}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JSON login error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при входе в систему")


@auth_router.post("/telegram", response_model=Token)
async def telegram_auth(telegram_auth: TelegramAuth):
    """
    Аутентификация или регистрация пользователя через Telegram
    """
    try:
        # Пытаемся найти существующего пользователя
        user = await user_service.authenticate_telegram_user(telegram_auth.telegram_id)

        if not user:
            # Если пользователь не найден, создаем нового
            logger.info(f"Creating new Telegram user: {telegram_auth.telegram_id}")
            user = await user_service.create_telegram_user(telegram_auth)

        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = security_service.create_access_token(data={"sub": user.id}, expires_delta=access_token_expires)

        logger.info(f"Telegram user authenticated: {user.id}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        }

    except Exception as e:
        logger.error(f"Telegram auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при аутентификации через Telegram"
        )


@auth_router.get("/me", response_model=User)
async def get_current_user(user_id: str = Depends(security_service.get_current_user_id)):
    """
    Получение информации о текущем пользователе
    """
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении информации о пользователе"
        )
