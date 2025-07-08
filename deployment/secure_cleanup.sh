#!/bin/bash

# Security cleanup script - removes sensitive data from all files
# Заменяет реальные IP, SSH ключи и другие чувствительные данные на placeholders

echo "🔒 Security Cleanup: Removing sensitive data from repository files..."

# Реальные данные для замены (замените на ваши реальные данные)
REAL_IP="YOUR_REAL_SERVER_IP"  # Замените на ваш реальный IP
REAL_SSH_KEY="your_real_ssh_key"  # Замените на ваше реальное имя SSH ключа

# Placeholders для замены
PLACEHOLDER_IP="YOUR_SERVER_IP"
PLACEHOLDER_SSH_KEY="your_ssh_key"

# Файлы для обработки (исключаем deploy.env - это рабочий файл)
FILES_TO_CLEAN=(
    "deploy_all.sh"
    "setup_deploy.sh"
    "test_docker_installation.sh"
    "diagnose_backend_failure.sh"
    "debug_docker.sh"
    "fix_docker_compose.sh"
    "logs.sh"
    "README.md"
    "DEPLOYMENT_README.md"
)

echo "Replacing sensitive data in files..."

for file in "${FILES_TO_CLEAN[@]}"; do
    if [ -f "$file" ]; then
        echo "  📝 Cleaning $file"
        
        # Заменяем IP адреса
        sed -i.backup "s/$REAL_IP/$PLACEHOLDER_IP/g" "$file"
        
        # Заменяем SSH ключи
        sed -i.backup "s/$REAL_SSH_KEY/$PLACEHOLDER_SSH_KEY/g" "$file"
        
        # Удаляем backup файлы
        rm -f "$file.backup"
    else
        echo "  ⚠️  File not found: $file"
    fi
done

echo ""
echo "✅ Security cleanup completed!"
echo ""
echo "📋 Summary of changes:"
echo "  • Replaced real IP addresses with: $PLACEHOLDER_IP"
echo "  • Replaced real SSH key names with: $PLACEHOLDER_SSH_KEY"
echo "  • Files cleaned: ${#FILES_TO_CLEAN[@]}"
echo ""
echo "⚠️  Note: deploy.env was NOT modified (it's your working config)"
echo "⚠️  Note: deploy.env is now properly ignored by Git"
echo ""
echo "🔍 To verify changes:"
echo "  git diff"
echo ""
echo "💾 To commit security fixes:"
echo "  git add -A"
echo "  git commit -m \"Security: Remove sensitive data from repository\"" 