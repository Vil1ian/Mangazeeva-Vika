# Отчёт: развёртывание окружения WSL + SDK + PostgreSQL

## 1. Установка WSL и Ubuntu

Установка компонентов WSL через PowerShell. Процесс загрузки и завершение установки.
![wsl-1](screens/01-wsl-install.png)
![wsl-2](screens/02-wsl-success.png)

Создание пользователя `mangazeeva-v-p` и установка пароля.
![wsl-3](screens/screens03-wsl-user.png)

## 2. Первичная настройка и обновление системы

Вход в систему и проверка работы sudo (обновление списка пакетов `sudo apt update`).
![apt-1](screens/screens04-apt-update.png)
![apt-2](screens/screens05-apt-update-done.png)

Установка компилятора GCC и базовых утилит (пакет `build-essential`).
![apt-3](screens/screens06-install-build-essential.png)
![apt-4](screens/screens07-install-progress.png)
![apt-5](screens/screens08-install-done.png)

Проверка установленной версии компилятора GCC (15.2.0).
![gcc](screens/screens09-gcc-version.png)

## 3. Установка СУБД PostgreSQL

Установка PostgreSQL (команда `sudo apt install postgresql`).
![pg-1](screens/screens10-pg-install.png)
![pg-2](screens/screens11-pg-progress.png)

Проверка статуса службы PostgreSQL. Статус `active (exited)` является нормальным для обертки сервиса, так как основные процессы запускаются отдельно.
![pg-3](screens/screens12-pg-status.png)

Проверка текущей даты в системе (команда `date`).
![date](screens/screens13-date.png)

## 4. Установка дополнительных утилит и Python (SDK)

Установка утилит `curl`, `wget`, `git`, `nano`, `unzip`.
![utils](screens/screens14-utils-install.png)

Установка Python 3, pip и venv.
![python-1](screens/screens15-python-install.png)
![python-2](screens/screens16-python-progress.png)

Проверка версий Python (3.14.4) и pip (25.1.1).
![python-3](screens/screens17-python-version.png)

Проверка версии PostgreSQL в командной строке (18.6).
![psql](screens/screens18-psql-version.png)

## 5. Создание БД и проверка подключения

Создание пользователя БД `myuser` и базы данных `testdb`.
![db-1](screens/screens19-db-create.png)

Вывод списка баз данных (команда `\l`) — база `testdb` успешно создана.
![db-2](screens/screens20-db-list.png)

Подключение к базе `testdb` от имени пользователя `myuser` и проверка версии (`SELECT version();`).
![db-3](screens/screens21-db-connect.png)

## 6. Подготовка отчета

Создание рабочей директории `wsl-pg-report` и папки для скриншотов `screens`.
![dir](screens/screens22-mkdir.png)

Проверка версии операционной системы Ubuntu (26.04.1 LTS).
![version](screens/screens23-os-version.png)
