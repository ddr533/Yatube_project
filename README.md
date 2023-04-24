# Yatube  
##### Описание проекта 
Yatube - это социальная сеть, где можно публиковать записи о
событиях из жизни. 
##### Основные возможности:
* Создавать записи с фотографиями в тематических разделах.
* Оформлять подписки на авторов.
* Оставлять комментарии.
* Получать данные по API.
##### Технологии 
  
 - Python 3.9   
 - Django 4.0
 - Django rest_framework
 - Sqlite3
  
### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:ddr533/Yatube_project.git
```

```
cd Yatube_project
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

* Если у вас Linux/macOS

    ```
    source env/bin/activate
    ```

* Если у вас windows

    ```
    source env/scripts/activate
    ```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```

### Примеры запросов API:
* Создание нового пользователя:
  
  - api/v1/auth/users/
```
    {
        "email": "string",
        "username": "string",
        "password": "string"
    }

``` 
* Получение токена для аутентификации: 

  - api/v1/auth/jwt/create/
```
    {
        "username": "string",
        "password": "string"
    }

``` 
* Получить список всех публикаций: 

  - api/v1/posts/

  - Доступные параметры: limit, offset, search, ordering
```
    {  "count": 41,
       "next": "http://127.0.0.1:8000/api/v1/posts/?limit=5&offset=5",
       "previous": null,
       "results": [
           {
               "id": 0,
               "author": "string",
               "text": "string",
               "pub_date": "2021-10-14T20:41:29.648Z",
               "image": "string",
               "group": 0
           },
       ]    
    }

```
* Создать публикацию (для авторизованных пользователей): 

  - api/v1/posts/
  - В поле image можно передавать ссылку на картинку, или строку с картинкой
  в формате base64 

```
    {
        "text": "string",
        "image": "string",
        "group": 0
    }    

```
* Получить отдельную публикацию: 

  - api/v1/posts/{id}/

```
    {
        "id": 0,
        "author": "string",
        "text": "string",
        "pub_date": "2019-08-24T14:15:22Z",
        "image": "string",
        "group": 0
    }    

```
* Получить список сообществ: 

  - api/v1/groups/
  - Доступные параметры: search

```
    [
        {
            "id": 0,
            "title": "string",
            "slug": "string",
            "description": "string"
        }
    ]   

```
* Получить список комментариев к записи: 

  - api/v1/{post_id}/comments/
  - Доступные параметры: search, ordering

```
    [
        {
            "id": 0,
            "author": "string",
            "text": "string",
            "created": "2019-08-24T14:15:22Z",
            "post": 0
        }
    ]  

```
* Получить список подписок (для авторизованных пользователей): 

  - api/v1/follow/
  - Доступные параметры: search

```
    [
        {
            "author": "string"
        }
    ] 

```
* Все доступные запросы можно посмотреть по адресу v1/docs/

### Автор:
Андрей Дрогаль
