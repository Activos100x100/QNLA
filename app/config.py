"""
Configuración centralizada de la aplicación.
Carga todas las variables de entorno y las expone como propiedades.
"""

from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """
    Configuración principal de la aplicación.
    Las variables se cargan desde el archivo .env
    """
    
    # Base de datos
    database_url: str = "postgresql://user:password@localhost:5432/facturas_db"
    
    # OpenAI
    openai_api_key: str = "your_openai_api_key_here"
    
    # Aplicación
    debug: bool = True
    secret_key: str = "your_secret_key_here_change_in_production"
    
    # PaddleOCR
    paddle_use_gpu: bool = False
    
    # Límites de archivos
    max_file_size: int = 52428800  # 50MB en bytes
    
    # Directorios
    upload_dir: str = "uploads"
    
    # Servidor
    host: str = "127.0.0.1"
    port: int = 8080
    
    # WhatsApp (opcional)
    whatsapp_token: Optional[str] = None
    phone_number_id: Optional[str] = None
    
    # Hosts permitidos
    allowed_hosts: Optional[str] = None
    
    # HTTPS
    force_https: Optional[bool] = False
    
    # Configuración Pydantic
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Permitir campos adicionales
    
    @property
    def upload_path(self) -> Path:
        """Retorna la ruta de uploads como Path object."""
        return Path(self.upload_dir)


# Instancia global de configuración
settings = Settings()
