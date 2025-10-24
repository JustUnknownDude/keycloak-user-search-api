import asyncpg
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import urllib.parse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
security = HTTPBearer()

# Параметры подключения к базе кейклока
DB_CONFIG = {
    "user": "POSTGRES_DB_USER",
    "password": "POSTGRES_DB_PASS",
    "database": "keycloak_database_name",
    "host": "PG_HOST_ADDR",
    "port": "5432"
}

#Bearer token для доступа
HARDCODED_BEARER = "RANDOM_TOKEN_FOR_API_ACESS"

class ResponseModel(BaseModel):
    status: str
    status_code: int

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != HARDCODED_BEARER:
        raise HTTPException(status_code=401, detail="Invalid or missing Bearer token")
    return credentials.credentials

async def get_db_connection():
    return await asyncpg.connect(**DB_CONFIG)

@app.get("/api/jira_check", response_model=ResponseModel)
async def jira_check(
    ph: Optional[str] = None,
    em: Optional[str] = None,
    pc: Optional[str] = None,
    sc: Optional[str] = None,
    token: str = Depends(verify_token)
):
    params = [ph, em, pc, sc]
    non_empty_params = [p for p in params if p]

    if len(non_empty_params) > 1:
        raise HTTPException(status_code=400, detail="Укажите только один из параметров: телефон, адрес электронной почты, почтовый индекс или код субъекта.")
    elif len(non_empty_params) == 0:
        raise HTTPException(status_code=400, detail="Укажите один из параметров: телефон, адрес электронной почты, почтовый индекс или код субъекта.")

# Определяем значение и поле для поиска
    search_value = non_empty_params[0]
    if ph:
        search_field = "phoneNumber"
    elif em:
        search_field = "email"
    elif pc:
        search_field = "LDAP_ID"
    elif sc:
        search_field = "id"
    
    # Декодируем URL-кодированный ввод, сохраняя «+», заменяя «+» на «%2B»
    search_value = urllib.parse.unquote(search_value.replace('+', '%2B'))
    
    logger.info(f"Searching for field: {search_field}, value: {search_value!r}")
    
    try:
        # Подключение к базе
        conn = await get_db_connection()
        
        try:
            if search_field == "email":
                query = """
                    SELECT id FROM user_entity 
                    WHERE email = $1
                """
                result = await conn.fetch(query, search_value)

            elif search_field == "id":
                query = """
                    SELECT email FROM user_entity 
                    WHERE id = $1
                """
                result = await conn.fetch(query, search_value)
            
            elif search_field == "LDAP_ID":
               
                query = """
                    SELECT user_id FROM user_attribute 
                    WHERE name = $1 AND value = $2
                """
                result = await conn.fetch(query, search_field, search_value)

            else:
                # Поиск phoneNumber в таблице user_attribute
                query = """
                    SELECT user_id FROM user_attribute 
                    WHERE name = $1 AND value = $2
                """
                result = await conn.fetch(query, search_field, search_value)
            
            logger.info(f"Query result: {result}")
            
            # Если есть результат вовращаем ответ
            if result:
                return ResponseModel(status="ok", status_code=200)
            else:
                return ResponseModel(status="not found", status_code=404)
                
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
