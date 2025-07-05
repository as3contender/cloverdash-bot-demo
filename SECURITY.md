# 🔒 Security Guidelines

## 📋 Чувствительные данные в проекте

### ❌ НЕ коммитьте в Git:

1. **Файлы конфигурации с реальными данными:**
   - `deployment/deploy.env` - содержит IP сервера, SSH ключи
   - `backend/.env` - содержит пароли БД, OpenAI API ключи
   - `telegram-bot/.env` - содержит Telegram bot token

2. **SSH ключи и сертификаты:**
   - `~/.ssh/id_*` - приватные SSH ключи
   - Любые `.pem`, `.key`, `.crt` файлы

3. **Пароли и токены:**
   - API ключи (OpenAI, Telegram)
   - Пароли баз данных
   - JWT секретные ключи

### ✅ Безопасно коммитить:

1. **Примеры конфигураций:**
   - `deployment/deploy.env.example` - без реальных данных
   - `backend/env_example.txt` - шаблон с placeholders

2. **Документация:**
   - Инструкции по настройке
   - Примеры использования (с замаскированными данными)

## 🛡️ .gitignore конфигурация

Убедитесь, что `.gitignore` содержит:

```gitignore
# Environment variables
.env
.env.local
.env.*.local

# Deployment configuration (contains sensitive data)
deployment/deploy.env

# SSH keys
*.pem
*.key
id_*
```

## 🔍 Проверка безопасности

### Перед коммитом:

```bash
# 1. Проверьте, что чувствительные файлы игнорируются
git status

# 2. Найдите потенциально опасный контент
grep -r "password\|secret\|key\|token" . --exclude-dir=.git --exclude="SECURITY.md"

# 3. Проверьте IP адреса и хосты
grep -r "[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}" . --exclude-dir=.git

# 4. Запустите очистку безопасности
cd deployment && ./secure_cleanup.sh
```

### Регулярные проверки:

```bash
# Поиск потенциально утекших секретов
git log --all --full-history --source -- '*.env' '*.key' '*.pem'

# Проверка истории коммитов
git log --oneline | grep -i "password\|secret\|key"
```

## 🚨 Что делать при утечке

Если чувствительные данные попали в Git:

### 1. Немедленные действия:

```bash
# Смените скомпрометированные данные:
# - Пароли баз данных
# - API ключи
# - SSH ключи
# - JWT секреты
```

### 2. Очистка истории Git:

```bash
# Удалить файл из истории Git
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch path/to/sensitive/file' \
  --prune-empty --tag-name-filter cat -- --all

# Принудительно обновить удаленный репозиторий
git push origin --force --all
```

### 3. Уведомление команды:

- Сообщите всем разработчикам о смене ключей
- Обновите CI/CD переменные
- Проверьте логи на предмет несанкционированного доступа

## 📝 Рекомендации по разработке

### Переменные окружения:

```bash
# Используйте разные .env файлы для разных окружений
.env.development    # Для разработки
.env.staging       # Для тестирования  
.env.production    # Для продакшена
```

### Шаблоны конфигураций:

```bash
# Всегда создавайте .example файлы
cp .env .env.example
# Замените реальные данные на placeholders
sed -i 's/real_password/YOUR_PASSWORD/g' .env.example
```

### Валидация безопасности:

```bash
# Добавьте проверки в CI/CD
npm install --save-dev detect-secrets
detect-secrets scan --all-files
```

## 🎯 Checklist безопасности

- [ ] `.env` файлы добавлены в `.gitignore`
- [ ] SSH ключи не коммитятся
- [ ] Примеры файлов не содержат реальных данных
- [ ] IP адреса заменены на placeholders
- [ ] Пароли и токены не хардкожены в коде
- [ ] Документация не содержит чувствительной информации
- [ ] Настроены переменные окружения для CI/CD
- [ ] Команда знает о политике безопасности

## 🔗 Полезные ссылки

- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [Git Secrets Tool](https://github.com/awslabs/git-secrets)
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)

---

⚠️ **Помните**: Безопасность - это процесс, а не состояние. Регулярно проверяйте и обновляйте свои практики безопасности. 