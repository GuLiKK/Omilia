Создать/обновить requirements.txt:
```
pip freeze > requirements.txt
```
Скачать зависимости:
```
pip install -r requirements.txt
```

Запуск:
```
cd C:\Project\api
# Установить переменные окружения (Windows PowerShell)
$env:SECRET_KEY="secret!"
$env:JWT_SECRET_KEY="jwt-secret!"
python app.py
```

Swagger-док:
```
http://127.0.0.1:5000/apidocs
```
