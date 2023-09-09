# Парсер документации Python.

### Описание
Парсер собирает информацию о документации Python и PEP. Информации может выводится в формате таблицы, в csv-файл, или печататься в терминал построчно.

### Запуск проекта на Linux:
Клонируйте репозиторий
Создайте и активируйте виртуальное окружение:
```
python3 -m venv venv
```
```
source venv/bin/activate
```
Установите зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt

Перейдите в папку 'src':
```
cd src
```

### Режимы работы парсера:
 - whats-new - Парсинг обновлений документации Python.
 - latest_versions - Парсинг версий документации Python.
 - download - Загружает документацию Python.
 - pep - Парсинг статусов PEP.

### Пример запуска:
Справка о работе парсера:
```
python main.py -h
```
```
python main.py --help
```


### Автор  
Пётр Назаров  
(https://github.com/Pnazarov86)