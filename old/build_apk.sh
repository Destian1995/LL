#!/bin/bash

# ============================================
#   build_apk.sh — модернизированный скрипт для сборки,
#   zipalign, подписи и установки APK, а также
#   копирования готового bin/ в ~/project
# ============================================
#
# Как пользоваться:
#   ./build_apk.sh debug    — соберёт debug-версию APK и установит её на подключённое устройство
#   ./build_apk.sh release  — соберёт release-версию, выполнит zipalign/apksigner,
#                           установит release-APK и скопирует bin/ → ~/project
#   Если аргумент не передан, по умолчанию — release.
#
# Важные моменты:
# 1) В buildozer.spec **уберите** (или закомментируйте) строку
#      android.release_signature = ...
#    иначе p4a попытается подписать APK сам, и ваш ручной apksigner-процесс может конфликтовать.
#
# 2) В шапке этого скрипта задайте ваши параметры подписи:
#      KEYSTORE_PATH   — путь до вашего .jks-ключа
#      KEY_ALIAS       — alias вашего ключа внутри keystore
#      KEYSTORE_PASS   — пароль keystore
#      KEY_PASS        — пароль ключа (обычно совпадает с KEYSTORE_PASS)
#
# 3) После успешной сборки в папке bin/ появятся:
#      <APP_NAME>-<VERSION>-release-unsigned-<архитектуры>.apk   — unsigned APK
#      <APP_NAME>-<VERSION>-release-aligned.apk                 — после zipalign (обычное)
#      <APP_NAME>-<VERSION>-release-signed.apk                  — финальный, подписанный APK
#      <APP_NAME>-<VERSION>-multiabi-release-aligned.apk        — zipalign для мульти-ABI
#      <APP_NAME>-<VERSION>-multiabi-release-signed.apk         — мульти-ABI signed
#
# 4) Затем bin/ автоматически копируется в ~/project.
# 5) Если нет подключённого устройства (adb), установка будет пропущена с предупреждением.

set -euo pipefail

### === Параметры для подписи === ###
# Путь до вашего keystore-файла (JKS)
KEYSTORE_PATH="$HOME/Lerdon/signkey.keystore"

# Alias ключа внутри keystore
KEY_ALIAS="lerdon-release"

# Пароль самого keystore
KEYSTORE_PASS="mypassword"

# Пароль для конкретного alias (обычно совпадает с KEYSTORE_PASS)
KEY_PASS="mypassword"
### ============================ ###

# Имя вашего приложения (для поиска .apk после сборки)
APP_NAME="lerdonlegends"

# Имя buildozer.spec (если лежит рядом со скриптом)
SPEC_FILE="buildozer.spec"

# Файл для записи лога buildozer
LOG_FILE="buildozer.log"

# Минимальный свободный объём диска (МБ) для сборки
MIN_DISK_SPACE_MB=5120

# Пути к Android SDK/NDK (Buildozer хранит всё в ~/.buildozer/android)
export ANDROID_SDK_ROOT="$HOME/.buildozer/android/platform/android-sdk"
export ANDROIDSDK="$ANDROID_SDK_ROOT"
export ANDROIDNDK="$HOME/.buildozer/android/platform/android-ndk-r25b"
export ANDROIDAPI=33
export ANDROIDMINAPI=21

# JAVA_HOME (OpenJDK 17)
export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"

# Часовой пояс (опционально)
export TZ=":/usr/share/zoneinfo/Etc/GMT-4"

# Файл ZIP с NDK (для проверки наличия перед сборкой)
NDK_ZIP="$HOME/.buildozer/android/platform/android-ndk-r25b-linux.zip"

# ============================================

# Функция: вывести ошибку + последние 50 строк лога
error_exit() {
    echo -e "\n❌ Ошибка: $1" >&2
    echo "📜 Последние 50 строк лога ($LOG_FILE):"
    if [ -f "$LOG_FILE" ]; then
        tail -n 50 "$LOG_FILE"
    fi
    exit 1
}

# Функция: логирование времени шагов
_time_start=0
log_time() {
    if [ $_time_start -ne 0 ]; then
        local now=$(date +%s)
        local diff=$((now - _time_start))
        echo "⏱️ Шаг завершён за ${diff} сек."
    fi
    _time_start=$(date +%s)
}

################################################################################
#                                  Мэйн скрипт                                 #
################################################################################

echo "✨ Сборка Lerdon APK (сегодня: $(date '+%Y-%m-%d %H:%M:%S'))"

# 1) Определяем режим сборки: debug или release (по умолчанию release)
BUILD_MODE="release"
if [ $# -ge 1 ]; then
    case "$1" in
        debug|release)
            BUILD_MODE="$1"
            ;;
        *)
            echo "⚠️ Неверный аргумент: '$1'. Используйте 'debug' или 'release'."
            exit 1
            ;;
    esac
fi
echo "🔧 Режим сборки: $BUILD_MODE"
log_time

# 2) Проверка наличия buildozer
echo "🔍 Проверка наличия команды buildozer..."
if ! command -v buildozer &> /dev/null; then
    error_exit "'buildozer' не найден. Установите его: pip3 install buildozer"
fi
log_time

# 3) Проверка свободного места на диске
echo "💾 Проверка свободного места на диске..."
DISK_FREE=$(df -m . | awk 'NR==2 {print $4}')
if (( DISK_FREE < MIN_DISK_SPACE_MB )); then
    error_exit "Недостаточно места. Требуется минимум ${MIN_DISK_SPACE_MB} МБ, доступно: ${DISK_FREE} МБ"
fi
log_time

# 4) Очистка временных файлов сборки (.buildozer)
echo "🧹 Очистка временных файлов сборки..."
mkdir -p "$HOME/.buildozer/android/platform"
rm -rf ./.buildozer
mkdir -p ./.buildozer
log_time

# 5) Принятие лицензии Android SDK
echo "📜 Принимаем лицензию Android SDK..."
SDK_LICENSE_DIR="$HOME/.buildozer/android/platform/android-sdk/licenses"
mkdir -p "$SDK_LICENSE_DIR"
echo "8933bad161af4178b1185d1a37fbf4f9829056a34" > "$SDK_LICENSE_DIR/android-sdk-license"
log_time

# 6) Проверка наличия NDK (ZIP-файла)
echo "📦 Проверка наличия NDK..."
if [ ! -f "$NDK_ZIP" ]; then
    error_exit "Файл NDK не найден по пути: $NDK_ZIP"
else
    echo "✅ Найден NDK: $(basename "$NDK_ZIP")"
fi
log_time

# 7) Проверка инициализации buildozer.spec
echo "⚙️ Проверка buildozer.spec..."
if [ ! -f "$SPEC_FILE" ]; then
    echo "📝 Файл $SPEC_FILE отсутствует. Создаём новый через buildozer init..."
    buildozer init > "$LOG_FILE" 2>&1 || error_exit "Не удалось создать $SPEC_FILE"
    echo "✅ buildozer.spec создан. Отредактируйте его и запустите скрипт снова."
    exit 0
else
    echo "✅ Используется существующий $SPEC_FILE."
fi
log_time

# 8) Авто-инкремент версии в buildozer.spec (X.Y.Z → X.Y.(Z+1))
echo "🔄 Авто-инкремент версии в $SPEC_FILE..."
# Ищем строку вида: version = 1.3.5 (без учёта кавычек)
CURRENT_VERSION_LINE=$(grep -E '^version\s*=\s*[0-9]+\.[0-9]+\.[0-9]+' "$SPEC_FILE" | head -n1)
if [ -z "$CURRENT_VERSION_LINE" ]; then
    echo "⚠️ Не найдена строка с версией вида 'version = X.Y.Z'. Пропускаем инкремент."
else
    # Извлекаем только цифры: 1.3.5
    CURRENT_VERSION=$(echo "$CURRENT_VERSION_LINE" | sed -E 's/^version\s*=\s*([0-9]+\.[0-9]+\.[0-9]+).*/\1/')
    if [[ ! $CURRENT_VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "⚠️ Текущая версия '$CURRENT_VERSION' не соответствует формату X.Y.Z. Пропускаем инкремент."
    else
        # Увеличиваем последний компонент
        NEW_VERSION=$(echo "$CURRENT_VERSION" | awk -F. '{$NF = $NF + 1}1' OFS='.')
        # Заменяем всю строку version = ... на новую
        sed -i -E "s/^version\s*=\s*[0-9]+\.[0-9]+\.[0-9]+/version = $NEW_VERSION/" "$SPEC_FILE" \
            || error_exit "Не удалось заменить версию в $SPEC_FILE"
        echo "🆕 Версия: $CURRENT_VERSION → $NEW_VERSION"
    fi
fi
log_time

# 9) Обновление python-версии, p4a.bootstrap и android.archs в buildozer.spec
echo "🔧 Обновляем python-версию, p4a.whitelist и архитектуры в $SPEC_FILE..."

# — Устанавливаем Python 3.11.0 (или другую версию, если нужно)
WANTED_PYTHON="3.11.0"
if grep -q -E '^[[:space:]]*p4a\.python_version\s*=' "$SPEC_FILE"; then
    sed -i -E "s|^[[:space:]]*p4a\.python_version.*|p4a.python_version = ${WANTED_PYTHON}|" "$SPEC_FILE" \
        || error_exit "Не удалось обновить p4a.python_version в $SPEC_FILE"
    echo "✅ p4a.python_version → $WANTED_PYTHON"
else
    echo "p4a.python_version = ${WANTED_PYTHON}" >> "$SPEC_FILE"
    echo "✅ Добавили p4a.python_version = $WANTED_PYTHON"
fi

# — Обновляем p4a.whitelist на python3.11.0
if grep -q -E '^[[:space:]]*p4a\.whitelist\s*=' "$SPEC_FILE"; then
    sed -i -E "s|^[[:space:]]*p4a\.whitelist.*|p4a.whitelist = python${WANTED_PYTHON}|" "$SPEC_FILE" \
        || error_exit "Не удалось обновить p4a.whitelist в $SPEC_FILE"
    echo "✅ p4a.whitelist → python$WANTED_PYTHON"
else
    echo "p4a.whitelist = python${WANTED_PYTHON}" >> "$SPEC_FILE"
    echo "✅ Добавили p4a.whitelist = python$WANTED_PYTHON"
fi

# — Задаём архитектуры (armeabi-v7a и arm64-v8a для релизной сборки, только armeabi-v7a для debug)
if [ "$BUILD_MODE" = "debug" ]; then
    NEW_ARCHS="armeabi-v7a"
    echo "🔧 DEBUG → устанавливаем android.archs = $NEW_ARCHS"
else
    NEW_ARCHS="arm64-v8a, armeabi-v7a"
    echo "🔧 RELEASE → устанавливаем android.archs = $NEW_ARCHS"
fi

if grep -q -E '^[[:space:]]*android\.archs\s*=' "$SPEC_FILE"; then
    # заменяем всю строку, независимо от отступов
    sed -i -E "s|^[[:space:]]*android\.archs.*|android.archs = ${NEW_ARCHS}|" "$SPEC_FILE" \
        || error_exit "Не удалось обновить android.archs в $SPEC_FILE"
    echo "✅ Заменили android.archs на: $NEW_ARCHS"
else
    # если строки нет, просто дописываем в конец
    echo "android.archs = $NEW_ARCHS" >> "$SPEC_FILE"
    echo "✅ Добавили android.archs = $NEW_ARCHS"
fi

log_time


# 10) Запуск buildozer
echo "📦 Запускаем сборку ($BUILD_MODE) через buildozer..."
START_BUILD_TIME=$(date +%s)

if [ "$BUILD_MODE" = "debug" ]; then
    buildozer -v android debug > "$LOG_FILE" 2>&1
    BUILD_EXIT_CODE=$?
else
    # Для релизной сборки без встроенной подписи (будем подписывать вручную)
    buildozer -v android release > "$LOG_FILE" 2>&1
    BUILD_EXIT_CODE=$?
fi

BUILD_DURATION=$(( $(date +%s) - START_BUILD_TIME ))
echo "⏱️ Сборка ($BUILD_MODE) завершена за ${BUILD_DURATION} сек."

# 11) Проверка успешности сборки
if [ $BUILD_EXIT_CODE -ne 0 ]; then
    error_exit "Сборка завершилась с ошибкой (код: $BUILD_EXIT_CODE)."
fi

APK_DIR="bin"

# Переизвлекаем строку с версией, на случай, если её инкрементировали
VERSION_STR=$(grep -E '^version\s*=\s*[0-9]+\.[0-9]+\.[0-9]+' "$SPEC_FILE" | head -n1 | sed -E 's/^version\s*=\s*([0-9]+\.[0-9]+\.[0-9]+).*/\1/')

APK_BASENAME="${APP_NAME}-${VERSION_STR}"

if [ "$BUILD_MODE" = "debug" ]; then
    # debug: buildozer сам создаст <app>-<version>-debug.apk
    APK_FILENAME="${APK_BASENAME}-debug.apk"
    APK_PATH="${APK_DIR}/${APK_FILENAME}"
    if [ -f "$APK_PATH" ]; then
        echo "✅ Debug-APK готов: $APK_PATH"
        # Попытка установки на подключённое устройство
        if command -v adb &> /dev/null; then
            echo "📲 Пытаемся установить debug-APK через adb..."
            if adb devices | grep -w "device" &> /dev/null; then
                adb install -r "$APK_PATH" && echo "✅ Установка debug-APK прошла успешно."
            else
                echo "⚠️ Устройство не найдено по adb. Пропускаем установку."
            fi
        else
            echo "⚠️ adb не найден. Пропускаем установку."
        fi
        exit 0
    else
        error_exit "Debug-APK не найден: $APK_PATH"
    fi
else
    ################################################################################
    # 12) Находим обычный unsigned-APK, выполняем zipalign и подпись для него       #
    ################################################################################
    UNSIGNED_APK=$(ls "${APK_DIR}/${APK_BASENAME}-release-unsigned"*".apk" 2>/dev/null | head -n1)
    if [ -z "$UNSIGNED_APK" ] || [ ! -f "$UNSIGNED_APK" ]; then
        error_exit "Unsigned-APK не найден: ${APK_DIR}/${APK_BASENAME}-release-unsigned*.apk"
    fi

    # 12.1) Zipalign для обычного APK
    ALIGNED_APK="${UNSIGNED_APK%.apk}-aligned.apk"
    echo "🔧 Запускаем zipalign (обычный unsigned → aligned)..."
    "$ANDROID_SDK_ROOT/build-tools/36.0.0/zipalign" -v -p 4 \
        "$UNSIGNED_APK" \
        "$ALIGNED_APK" \
        || error_exit "zipalign (обычный) завершился с ошибкой."

    # 12.2) Apksigner для обычного APK
    SIGNED_APK="${UNSIGNED_APK%.apk}-signed.apk"
    echo "🔧 Подписываем обычный APK через apksigner..."
    "$ANDROID_SDK_ROOT/build-tools/36.0.0/apksigner" sign \
        --ks "$KEYSTORE_PATH" \
        --ks-key-alias "$KEY_ALIAS" \
        --ks-pass "pass:$KEYSTORE_PASS" \
        --key-pass "pass:$KEY_PASS" \
        --out "$SIGNED_APK" \
        "$ALIGNED_APK" \
        || error_exit "apksigner (обычный) завершился с ошибкой."

    # 12.3) Проверяем подпись (обычный APK)
    echo "🔎 Проверяем подпись обычного APK..."
    "$ANDROID_SDK_ROOT/build-tools/36.0.0/apksigner" verify --print-certs "$SIGNED_APK" \
        || error_exit "apksigner verify (обычный) вернул ошибку."

    echo "✅ Обычный Release-APK готов и подписан: $SIGNED_APK"

    ################################################################################
    # 13) Zipalign и apksigner для мульти-ABI unsigned-APK                          #
    ################################################################################
    echo "🔧 Дополнительный шаг: Zipalign + Apksigner для мульти-ABI unsigned-APK"

    cd ~/Lerdon/bin || error_exit "Не удалось перейти в папку ~/Lerdon/bin"

    ANDROID_BUILD_TOOLS="$HOME/.buildozer/android/platform/android-sdk/build-tools/36.0.0"

    # Исходное имя unsigned-мульти-ABI APK (строим по шаблону):
    MULTI_UNSIGNED="${APP_NAME}-${VERSION_STR}-arm64-v8a_armeabi-v7a_x86_x86_64-release-unsigned.apk"
    if [ ! -f "$MULTI_UNSIGNED" ]; then
        echo "⚠️ Мульти-ABI unsigned-APK не найден: $MULTI_UNSIGNED"
    else
        # 13.1) Zipalign мульти-ABI unsigned → multiabi-aligned
        MULTI_ALIGNED="${APP_NAME}-${VERSION_STR}-multiabi-release-aligned.apk"
        echo "🔧 zipalign для мульти-ABI unsigned → $MULTI_ALIGNED"
        "$ANDROID_BUILD_TOOLS/zipalign" -v -p 4 \
            "$MULTI_UNSIGNED" \
            "$MULTI_ALIGNED" \
            || error_exit "zipalign (мульти-ABI) завершился с ошибкой."

        # 13.2) Apksigner для мульти-ABI aligned → multiabi-signed
        MULTI_SIGNED="${APP_NAME}-${VERSION_STR}-multiabi-release-signed.apk"
        echo "🔧 apksigner для мульти-ABI aligned → $MULTI_SIGNED"
        "$ANDROID_BUILD_TOOLS/apksigner" sign \
            --ks ../signkey.keystore \
            --ks-key-alias "$KEY_ALIAS" \
            --ks-pass "pass:$KEYSTORE_PASS" \
            --key-pass "pass:$KEY_PASS" \
            --out "$MULTI_SIGNED" \
            "$MULTI_ALIGNED" \
            || error_exit "apksigner (мульти-ABI) завершился с ошибкой."

        echo "✅ Мульти-ABI Release-APK готов и подписан: $MULTI_SIGNED"
    fi

    # Возвращаемся в корень проекта
    cd - > /dev/null
    ################################################################################
    # 14) Установка подписанного release-APK и копирование bin/ → ~/project         #
    ################################################################################
    # Пытаемся установить только обычный signed APK (не multi-ABI)
    if command -v adb &> /dev/null; then
        echo "📲 Пытаемся установить release-APK через adb..."
        if adb devices | grep -w "device" &> /dev/null; then
            adb install -r "$SIGNED_APK" && echo "✅ Установка release-APK прошла успешно."
        else
            echo "⚠️ Устройство не найдено по adb. Пропускаем установку."
        fi
    else
        echo "⚠️ adb не найден. Пропускаем установку."
    fi

    echo "📂 Копируем bin/ → ~/project"
    cp -rf bin ~/project || echo "⚠️ Не удалось скопировать bin/ в ~/project"
    echo "✅ Готово! Весь bin/ скопирован в ~/project"

    exit 0
fi