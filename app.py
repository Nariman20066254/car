from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import asyncio
from asyncio import WindowsSelectorEventLoopPolicy
import g4f
import requests
from bs4 import BeautifulSoup
import urllib.parse
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Замените на случайный секретный ключ

# Установка политики Event Loop для Windows
asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

# Mock данные для входа
USERNAME = 'admin'
PASSWORD = 'password'

# Декоратор для проверки аутентификации
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            print("Пользователь не авторизован. Перенаправляем на страницу логина.")
            return redirect(url_for('login'))
        print("Пользователь авторизован.")
        return f(*args, **kwargs)
    return decorated_function

async def get_car_part_info(messages: list) -> str:
    response = g4f.ChatCompletion.create(
        model=g4f.models.gpt_4o_mini,
        messages=messages
    )
    return response

def print_result(query: str) -> str:
    messages = []
    question = f"""
{query}
Производитель    
Тип    
Назначение    
Марка    
Модель напиши все на которые подходит
Двигатель напиши все на которые подходит
Объем напиши объемы которые подходят 
Год    
Артикул оставь пустым
Номер OEM оставь пустым 
Напиши вес    
Напиши длину
Напиши высоту
Напиши ширину 
И в конце напиши на 150 слов мини описание.
Заполни эти данные.
"""
    messages.append({"role": "user", "content": question})
    
    # Запуск асинхронного кода с использованием asyncio.run
    answer = asyncio.run(get_car_part_info(messages))
    print(answer)  # Печать результата в консоль
    return answer

def search_images(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    query = urllib.parse.quote(query)
    url = f"https://www.google.com/search?hl=en&tbm=isch&q={query}"
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    image_urls = []
    for img_tag in soup.find_all("img"):
        img_url = img_tag.get("src")
        if img_url and img_url.startswith("http"):
            image_urls.append(img_url)
    
    return image_urls

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            print("Успешный вход. Перенаправляем на главную страницу.")
            return redirect(url_for('search'))
        else:
            print("Неверное имя пользователя или пароль.")
            return "Неверные учетные данные. Попробуйте снова.", 403
    
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)  # Удаляем 'logged_in' из сессии
    print("Выход выполнен. Перенаправляем на страницу логина.")
    return redirect(url_for('login'))  # Перенаправляем на страницу логина

# Применение декоратора для защиты маршрута
@app.route('/', methods=['GET', 'POST'])
@login_required  # Проверка на наличие входа в систему
def search():
    query = None
    result = None
    images = []
    
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            print(f'Полученный запрос: {query}')
            result = print_result(query)  # Вызов функции с передачей данных
            
            # Поиск изображений и получение URL
            image_urls = search_images(query)
            images = image_urls[:5]  # Ограничить количество изображений
            
        # Для AJAX-запросов возвращаем фрагмент HTML
        return render_template('index.html', query=query, result=result, images=images)
    
    # Для GET-запросов возвращаем полный HTML
    return render_template('index.html', query=query, result=result, images=images)

if __name__ == '__main__':
    app.run(debug=True)
