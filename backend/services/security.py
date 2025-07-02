from datetime import datetime, timedelta
from typing import Optional, Union
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config.settings import settings
from models.auth import TokenData


# Контекст для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


class SecurityService:
    """Сервис для работы с безопасностью"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Хэширование пароля"""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Создание JWT токена"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> TokenData:
        """Проверка JWT токена"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
            token_data = TokenData(user_id=user_id)
            return token_data
        except JWTError:
            raise credentials_exception

    @staticmethod
    def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
        """Получение ID текущего пользователя из токена"""
        token_data = SecurityService.verify_token(credentials.credentials)
        return token_data.user_id

    @staticmethod
    def get_current_user_id_optional(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    ) -> Optional[str]:
        """Получение ID пользователя из токена (опционально)"""
        if credentials:
            try:
                token_data = SecurityService.verify_token(credentials.credentials)
                return token_data.user_id
            except Exception:
                return None
        return None


# Создаем экземпляр сервиса
security_service = SecurityService()
