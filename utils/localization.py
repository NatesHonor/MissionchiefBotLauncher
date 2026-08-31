"""Small offline UI translation catalog with automatic system-locale detection."""

from __future__ import annotations

from PyQt6.QtCore import QLocale

from utils.settings_store import get as get_setting, set_values


LANGUAGES = {
    "auto": "Automatic",
    "en": "English",
    "de": "Deutsch",
    "es": "Español",
    "ru": "Русский",
}

CATALOGS = {
    "en": {
        "app_name": "Mission Helper", "dashboard": "Dashboard", "navigation": "Navigation", "region": "Region",
        "settings": "Settings", "controls": "Controls", "start_bot": "Start Bot", "stop_bot": "Stop Bot", "exit": "Exit",
        "connected": "Connected", "status": "Status", "idle": "Idle", "running": "Running", "starting": "Starting bot...", "ready": "Ready",
        "console_output": "Console Output", "console": "Console", "mission_control": "MissionChief", "up_to_date": "Up to date",
        "update_available": "Update available", "version": "Version", "profile": "Local Profile", "operator": "Operator",
        "display_name": "Display name", "role": "Role", "choose_avatar": "Change picture", "remove_avatar": "Remove picture",
        "save_profile": "Save profile", "profile_saved": "Profile saved", "appearance": "Appearance", "theme": "Theme",
        "language": "Language", "automatic": "Automatic", "blue_themes": "Blue themes", "bot_configuration": "Bot Configuration",
        "edit_config": "Edit config.ini for bot settings", "save_config": "Save Config", "repair": "Repair", "config_saved": "Configuration saved",
        "config_missing": "Config.ini is missing — run repair first", "repair_complete": "Repair completed successfully",
        "repair_missing": "Repair could not find a cached bot release", "select_region": "Select Region", "choose_region": "Choose MissionChief region",
        "region_switched": "Region switched", "update_check": "Checking for updates...", "update_skipped": "Update check unavailable",
        "close": "Close", "minimize": "Minimize", "maximize": "Maximize", "profile_hint": "Stored only on this computer",
        "hero_eyebrow": "MISSIONCHIEF LAUNCHER", "hero_title": "Launch MissionChief with confidence",
        "hero_copy": "Start the bot, watch its output, and keep MissionChief ready in one place.",
        "required_update": "Required Update", "changelog": "CHANGELOG", "preparing_update": "Preparing update...",
        "skip": "Skip", "install_update": "Install Update", "installing": "Installing...",
        "launching_updater": "Launching updater...", "self_update_source": "Self-update is available from packaged builds only.",
        "no_details": "No details provided.", "input": "Input", "enter_value": "Enter a value:",
        "cancel": "Cancel", "confirm": "Confirm", "console_placeholder": "Bot output will appear here...",
        "clear_console": "Clear console", "console_cleared": "Console cleared", "share_log": "Share log", "uploading_log": "Uploading log...", "log_url_copied": "Log URL copied", "already_running": "Mission Helper is already running.",
        "startup_failed": "The launcher could not start. Check the session log for details.",
        "virtual_environment": "Virtual Environment", "venv_prompt": "Enter a name for the Python virtual environment:",
        "region_hint": "MissionChief will open on this region.", "open_workspace": "Open MissionChief in the embedded workspace",
        "settings_copy": "Personalize the launcher and keep your operator profile local.",
    },
    "de": {
        "app_name": "Mission Helper", "dashboard": "Übersicht", "navigation": "Navigation", "region": "Region", "settings": "Einstellungen",
        "controls": "Steuerung", "start_bot": "Bot starten", "stop_bot": "Bot stoppen", "exit": "Beenden", "connected": "Verbunden",
        "status": "Status", "idle": "Bereit", "running": "Läuft", "starting": "Bot wird gestartet...", "ready": "Bereit", "console_output": "Konsolenausgabe",
        "console": "Konsole", "mission_control": "MissionChief", "up_to_date": "Aktuell", "update_available": "Update verfügbar",
        "version": "Version", "profile": "Lokales Profil", "operator": "Operator", "display_name": "Anzeigename", "role": "Rolle",
        "choose_avatar": "Bild ändern", "remove_avatar": "Bild entfernen", "save_profile": "Profil speichern", "profile_saved": "Profil gespeichert",
        "appearance": "Darstellung", "theme": "Design", "language": "Sprache", "automatic": "Automatisch", "blue_themes": "Blaue Designs",
        "bot_configuration": "Bot-Konfiguration", "edit_config": "config.ini für Bot-Einstellungen bearbeiten", "save_config": "Config speichern",
        "repair": "Reparieren", "config_saved": "Konfiguration gespeichert", "config_missing": "Config.ini fehlt — zuerst reparieren",
        "repair_complete": "Reparatur erfolgreich abgeschlossen", "repair_missing": "Kein gecachter Bot zum Reparieren gefunden", "select_region": "Region wählen",
        "choose_region": "MissionChief-Region wählen", "region_switched": "Region gewechselt", "update_check": "Suche nach Updates...",
        "update_skipped": "Updateprüfung nicht verfügbar", "close": "Schließen", "minimize": "Minimieren", "maximize": "Maximieren",
        "profile_hint": "Nur auf diesem Computer gespeichert",
        "hero_eyebrow": "MISSIONCHIEF LAUNCHER", "hero_title": "MissionChief sicher starten",
        "hero_copy": "Starte den Bot, überwache die Ausgabe und halte MissionChief an einem Ort bereit.",
        "required_update": "Erforderliches Update", "changelog": "ÄNDERUNGEN", "preparing_update": "Update wird vorbereitet...",
        "skip": "Überspringen", "install_update": "Update installieren", "installing": "Installation...",
        "launching_updater": "Updater wird gestartet...", "self_update_source": "Selbst-Updates sind nur in gepackten Builds verfügbar.",
        "no_details": "Keine Details vorhanden.", "input": "Eingabe", "enter_value": "Wert eingeben:",
        "cancel": "Abbrechen", "confirm": "Bestätigen", "console_placeholder": "Bot-Ausgabe wird hier angezeigt...",
        "clear_console": "Konsole leeren", "console_cleared": "Konsole geleert", "share_log": "Log teilen", "uploading_log": "Log wird hochgeladen...", "log_url_copied": "Log-URL kopiert", "already_running": "Mission Helper wird bereits ausgeführt.",
        "startup_failed": "Der Launcher konnte nicht gestartet werden. Prüfe das Sitzungsprotokoll.",
        "virtual_environment": "Virtuelle Umgebung", "venv_prompt": "Name der Python-Umgebung eingeben:",
        "region_hint": "MissionChief wird für diese Region geöffnet.", "open_workspace": "MissionChief im eingebetteten Arbeitsbereich öffnen",
        "settings_copy": "Personalisiere den Launcher und speichere dein Operator-Profil lokal.",
    },
    "es": {
        "app_name": "Mission Helper", "dashboard": "Panel", "navigation": "Navegación", "region": "Región", "settings": "Ajustes",
        "controls": "Controles", "start_bot": "Iniciar bot", "stop_bot": "Detener bot", "exit": "Salir", "connected": "Conectado",
        "status": "Estado", "idle": "En espera", "running": "En ejecución", "starting": "Iniciando bot...", "ready": "Listo", "console_output": "Salida de consola",
        "console": "Consola", "mission_control": "MissionChief", "up_to_date": "Actualizado", "update_available": "Actualización disponible",
        "version": "Versión", "profile": "Perfil local", "operator": "Operador", "display_name": "Nombre visible", "role": "Rol",
        "choose_avatar": "Cambiar imagen", "remove_avatar": "Eliminar imagen", "save_profile": "Guardar perfil", "profile_saved": "Perfil guardado",
        "appearance": "Apariencia", "theme": "Tema", "language": "Idioma", "automatic": "Automático", "blue_themes": "Temas azules",
        "bot_configuration": "Configuración del bot", "edit_config": "Editar config.ini del bot", "save_config": "Guardar configuración",
        "repair": "Reparar", "config_saved": "Configuración guardada", "config_missing": "Falta config.ini — repara primero",
        "repair_complete": "Reparación completada", "repair_missing": "No se encontró una versión del bot en caché", "select_region": "Elegir región",
        "choose_region": "Elige la región de MissionChief", "region_switched": "Región cambiada", "update_check": "Buscando actualizaciones...",
        "update_skipped": "Actualización no disponible", "close": "Cerrar", "minimize": "Minimizar", "maximize": "Maximizar",
        "profile_hint": "Guardado solo en este equipo",
        "hero_eyebrow": "MISSIONCHIEF LAUNCHER", "hero_title": "Inicia MissionChief con confianza",
        "hero_copy": "Inicia el bot, supervisa su salida y mantén MissionChief listo en un solo lugar.",
        "required_update": "Actualización obligatoria", "changelog": "CAMBIOS", "preparing_update": "Preparando actualización...",
        "skip": "Omitir", "install_update": "Instalar actualización", "installing": "Instalando...",
        "launching_updater": "Iniciando actualizador...", "self_update_source": "La autoactualización solo está disponible en versiones empaquetadas.",
        "no_details": "No hay detalles.", "input": "Entrada", "enter_value": "Introduce un valor:",
        "cancel": "Cancelar", "confirm": "Confirmar", "console_placeholder": "La salida del bot aparecerá aquí...",
        "clear_console": "Limpiar consola", "console_cleared": "Consola limpiada", "share_log": "Compartir registro", "uploading_log": "Subiendo registro...", "log_url_copied": "URL del registro copiada", "already_running": "Mission Helper ya está en ejecución.",
        "startup_failed": "No se pudo iniciar el launcher. Revisa el registro de sesión.",
        "virtual_environment": "Entorno virtual", "venv_prompt": "Introduce un nombre para el entorno virtual de Python:",
        "region_hint": "MissionChief se abrirá en esta región.", "open_workspace": "Abrir MissionChief en el espacio integrado",
        "settings_copy": "Personaliza el launcher y guarda tu perfil de operador localmente.",
    },
    "ru": {
        "app_name": "Mission Helper", "dashboard": "Панель", "navigation": "Навигация", "region": "Регион", "settings": "Настройки",
        "controls": "Управление", "start_bot": "Запустить бота", "stop_bot": "Остановить бота", "exit": "Выход", "connected": "Подключено",
        "status": "Статус", "idle": "Ожидание", "running": "Запущен", "starting": "Запуск бота...", "ready": "Готово", "console_output": "Вывод консоли",
        "console": "Консоль", "mission_control": "MissionChief", "up_to_date": "Актуально", "update_available": "Доступно обновление",
        "version": "Версия", "profile": "Локальный профиль", "operator": "Оператор", "display_name": "Отображаемое имя", "role": "Роль",
        "choose_avatar": "Изменить изображение", "remove_avatar": "Удалить изображение", "save_profile": "Сохранить профиль", "profile_saved": "Профиль сохранён",
        "appearance": "Внешний вид", "theme": "Тема", "language": "Язык", "automatic": "Автоматически", "blue_themes": "Синие темы",
        "bot_configuration": "Настройки бота", "edit_config": "Изменить config.ini бота", "save_config": "Сохранить настройки",
        "repair": "Восстановить", "config_saved": "Настройки сохранены", "config_missing": "config.ini отсутствует — сначала восстановите",
        "repair_complete": "Восстановление завершено", "repair_missing": "Кэш бота не найден", "select_region": "Выбрать регион",
        "choose_region": "Выберите регион MissionChief", "region_switched": "Регион изменён", "update_check": "Проверка обновлений...",
        "update_skipped": "Проверка обновлений недоступна", "close": "Закрыть", "minimize": "Свернуть", "maximize": "Развернуть",
        "profile_hint": "Хранится только на этом компьютере",
        "hero_eyebrow": "MISSIONCHIEF LAUNCHER", "hero_title": "Запускайте MissionChief уверенно",
        "hero_copy": "Запускайте бота, следите за выводом и держите MissionChief под рукой в одном месте.",
        "required_update": "Обязательное обновление", "changelog": "ИЗМЕНЕНИЯ", "preparing_update": "Подготовка обновления...",
        "skip": "Пропустить", "install_update": "Установить обновление", "installing": "Установка...",
        "launching_updater": "Запуск обновлятора...", "self_update_source": "Самообновление доступно только в упакованных сборках.",
        "no_details": "Подробности отсутствуют.", "input": "Ввод", "enter_value": "Введите значение:",
        "cancel": "Отмена", "confirm": "Подтвердить", "console_placeholder": "Вывод бота появится здесь...",
        "clear_console": "Очистить консоль", "console_cleared": "Консоль очищена", "share_log": "Поделиться журналом", "uploading_log": "Загрузка журнала...", "log_url_copied": "Ссылка на журнал скопирована", "already_running": "Mission Helper уже запущен.",
        "startup_failed": "Не удалось запустить лаунчер. Проверьте журнал сеанса.",
        "virtual_environment": "Виртуальная среда", "venv_prompt": "Введите имя виртуальной среды Python:",
        "region_hint": "MissionChief откроется для этого региона.", "open_workspace": "Открыть MissionChief во встроенном рабочем пространстве",
        "settings_copy": "Настройте лаунчер и храните профиль оператора локально.",
    },
}


def available_languages():
    return LANGUAGES.copy()


def _detected_language() -> str:
    code = QLocale.system().name().split("_")[0].lower()
    return code if code in CATALOGS else "en"


def language_code() -> str:
    selected = get_setting("language", "auto").lower()
    return _detected_language() if selected == "auto" else selected if selected in CATALOGS else "en"


def language_setting() -> str:
    selected = get_setting("language", "auto").lower()
    return selected if selected in LANGUAGES else "auto"


def set_language(language: str) -> str:
    selected = language.lower().strip()
    if selected not in LANGUAGES:
        raise ValueError("Unsupported language")
    set_values({"language": selected})
    return selected


def tr(key: str, **values) -> str:
    text = CATALOGS.get(language_code(), CATALOGS["en"]).get(key, CATALOGS["en"].get(key, key))
    return text.format(**values) if values else text
