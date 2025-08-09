[RU](#ru) | [EN](#en)
<p align="left">
  <img src="db/images/interface/icon.png" alt="Иконка приложения" width="200">
</p>

# DelegTa
## RU
**Делегирование задач между сотрудниками для руководителя** - программа делегации обязанностей людей для удобного управления задачами управляющему.
### Быстрый старт
Чтобы использовать программу, достаточно скачать zip-архив репозитория. После его установки, разаархивируйте папку в удобной для себя директории. Зайдите в папку и выберите для себя вариант использования программы.
1. В директории `DelegTaEXE` хранится файл `DelegTa.exe`, при нажатии на который активируется программа. Дополнительных действий и установок проводить не нужно.
2. В основной директории находится основной код программы и `start_delegation_tasks.bat`, на который нужно нажать, чтобы код программы был запущен.
> [!NOTE]
> Для второго  метода активации программы, на вашем устройстве должен поддерживаться язык программирования Python, быть доступен через PATH и быть в наличии библиотека PySide6. В противником случае `start_delegation_tasks.bat` выполнит самостоятельно установку.
### Условия использования
В обоих случаях необходимо, чтобы исходный файл программы находился одной директории с папкой `db`, отвечающая за хранение всех необходимых файлов. Если вы используете .exe версию программы, необходимо также наличие папки `_internal`, отвечающая за логику работы .exe файла. 

`create_shortcut.bat` при нажатии создаст автоматически ярлык к `start_delegation_tasks.bat`, который по желанию, пользователь может переместить.

`create_shortcut_exe.bat` при нажатии создаст автоматически ярлык к `DelegTa.exe`, который по желанию, пользователь может переместить.
> [!TIP]
> Директорию `DelegTaEXE` спокойно можно переместить и переименовать по желанию, однако необходимо булет пересоздать ярлык через `create_shortcut_exe.bat`.
## EN
**Delegation of tasks between people for the director** - program for delegating people's responsibilities to conveniently manage tasks for the director.
### Quick start
To use the program, simply download the repository zip archive. After installing it, unzip the folder into a convenient directory. Go to the folder and select the program option you want to use.
1. The `DelegTaEXE` directory contains the `DelegTa.exe` file, which activates the program when clicked. No additional actions or settings are required.
2. The main directory contains the main program code and `start_delegation_tasks.bat`, which you need to click to run the program code.
> [!NOTE]
> For the second method of activating the program, your device must support the Python programming language, be accessible via PATH, and have the PySide6 library available. Otherwise, `start_delegation_tasks.bat` will perform the installation itself.
### Terms of Use
In both cases, the original program file must be located in the same directory as the `db` folder, which is responsible for storing all necessary files. If you are using the .exe version of the program, you must also have the `_internal` folder, which is responsible for the logic of the .exe file.

When clicked, `create_shortcut.bat` will automatically create a shortcut to `start_delegation_tasks.bat`, which the user can move if desired.

When clicked, `create_shortcut_exe.bat` will automatically create a shortcut to `DelegTa.exe`, which the user can move if desired.
> [!TIP]
> The `DelegTaEXE` directory can be safely moved and renamed as desired, but you will need to recreate the shortcut using `create_shortcut_exe.bat`.
