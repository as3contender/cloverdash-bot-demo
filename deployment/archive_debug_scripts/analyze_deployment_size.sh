#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}📊 Deployment Size Analysis${NC}"
echo ""

# Function to get file count excluding patterns
get_file_count_with_exclusions() {
    local dir="$1"
    local exclude_file="$2"
    
    if [ -f "$exclude_file" ] && [ -d "$dir" ]; then
        # Create temporary directory for rsync test
        temp_dir=$(mktemp -d)
        if rsync -a --exclude-from="$exclude_file" "$dir"/ "$temp_dir"/ >/dev/null 2>&1; then
            count=$(find "$temp_dir" -type f | wc -l)
            echo "$count"
        else
            echo "0"
        fi
        rm -rf "$temp_dir"
    elif [ -d "$dir" ]; then
        find "$dir" -type f | wc -l
    else
        echo "0"
    fi
}

# Function to get directory size in bytes
get_dir_size() {
    local dir="$1"
    local exclude_file="$2"
    
    if [ -f "$exclude_file" ] && [ -d "$dir" ]; then
        # Create temporary directory for rsync test
        temp_dir=$(mktemp -d)
        if rsync -a --exclude-from="$exclude_file" "$dir"/ "$temp_dir"/ >/dev/null 2>&1; then
            size=$(du -sk "$temp_dir" 2>/dev/null | cut -f1)
            if [ -n "$size" ] && [ "$size" -gt 0 ]; then
                # Convert KB to bytes
                echo $((size * 1024))
            else
                echo "0"
            fi
        else
            echo "0"
        fi
        rm -rf "$temp_dir"
    elif [ -d "$dir" ]; then
        size=$(du -sk "$dir" 2>/dev/null | cut -f1)
        if [ -n "$size" ] && [ "$size" -gt 0 ]; then
            # Convert KB to bytes
            echo $((size * 1024))
        else
            echo "0"
        fi
    else
        echo "0"
    fi
}

# Function to format bytes
format_bytes() {
    local bytes=$1
    if [ $bytes -gt 1073741824 ]; then
        echo "$(echo "scale=1; $bytes/1073741824" | bc -l) GB"
    elif [ $bytes -gt 1048576 ]; then
        echo "$(echo "scale=1; $bytes/1048576" | bc -l) MB"
    elif [ $bytes -gt 1024 ]; then
        echo "$(echo "scale=1; $bytes/1024" | bc -l) KB"
    else
        echo "$bytes bytes"
    fi
}

# Analyze backend directory
if [ -d "../backend" ]; then
    echo -e "${YELLOW}🔍 Backend Analysis:${NC}"
    
    # Full size
    backend_full_size=$(get_dir_size "../backend")
    backend_full_files=$(find "../backend" -type f | wc -l)
    
    # Optimized size (with exclusions)
    backend_opt_size=$(get_dir_size "../backend" "../.deployignore")
    backend_opt_files=$(get_file_count_with_exclusions "../backend" "../.deployignore")
    
    echo "  📁 Full directory: $(format_bytes $backend_full_size) ($backend_full_files files)"
    echo "  ✅ Optimized: $(format_bytes $backend_opt_size) ($backend_opt_files files)"
    
    if [ -n "$backend_full_size" ] && [ -n "$backend_opt_size" ] && [ "$backend_full_size" -gt 0 ]; then
        savings_percent=$(echo "scale=1; ($backend_full_size - $backend_opt_size) * 100 / $backend_full_size" | bc -l 2>/dev/null)
        savings_bytes=$((backend_full_size - backend_opt_size))
        echo "  💾 Savings: $(format_bytes $savings_bytes) (${savings_percent:-0}%)"
    fi
    echo ""
else
    echo -e "${RED}❌ Backend directory not found${NC}"
fi

# Analyze telegram-bot directory
if [ -d "../telegram-bot" ]; then
    echo -e "${YELLOW}🔍 Telegram Bot Analysis:${NC}"
    
    # Full size
    bot_full_size=$(get_dir_size "../telegram-bot")
    bot_full_files=$(find "../telegram-bot" -type f | wc -l)
    
    # Optimized size (with exclusions)
    bot_opt_size=$(get_dir_size "../telegram-bot" "../.deployignore")
    bot_opt_files=$(get_file_count_with_exclusions "../telegram-bot" "../.deployignore")
    
    echo "  📁 Full directory: $(format_bytes $bot_full_size) ($bot_full_files files)"
    echo "  ✅ Optimized: $(format_bytes $bot_opt_size) ($bot_opt_files files)"
    
    if [ -n "$bot_full_size" ] && [ -n "$bot_opt_size" ] && [ "$bot_full_size" -gt 0 ]; then
        savings_percent=$(echo "scale=1; ($bot_full_size - $bot_opt_size) * 100 / $bot_full_size" | bc -l 2>/dev/null)
        savings_bytes=$((bot_full_size - bot_opt_size))
        echo "  💾 Savings: $(format_bytes $savings_bytes) (${savings_percent:-0}%)"
    fi
    echo ""
else
    echo -e "${RED}❌ Telegram-bot directory not found${NC}"
fi

# Total analysis
if [ -d "../backend" ] && [ -d "../telegram-bot" ]; then
    echo -e "${BLUE}📊 Total Deployment Analysis:${NC}"
    
    # Default to 0 if variables are empty
    backend_full_size=${backend_full_size:-0}
    bot_full_size=${bot_full_size:-0}
    backend_opt_size=${backend_opt_size:-0}
    bot_opt_size=${bot_opt_size:-0}
    
    total_full=$((backend_full_size + bot_full_size))
    total_opt=$((backend_opt_size + bot_opt_size))
    total_savings=$((total_full - total_opt))
    
    echo "  📁 Full deployment: $(format_bytes $total_full)"
    echo "  ✅ Optimized deployment: $(format_bytes $total_opt)"
    echo "  💾 Total savings: $(format_bytes $total_savings)"
    
    if [ "$total_full" -gt 0 ]; then
        total_savings_percent=$(echo "scale=1; $total_savings * 100 / $total_full" | bc -l 2>/dev/null)
        echo "  📈 Savings percentage: ${total_savings_percent:-0}%"
    fi
    echo ""
fi

# Show excluded files examples
echo -e "${BLUE}📋 Examples of excluded files:${NC}"
if [ -f "../.deployignore" ]; then
    echo -e "${YELLOW}Exclusion patterns from .deployignore:${NC}"
    grep -v '^#' "../.deployignore" | grep -v '^$' | head -10 | sed 's/^/  /'
    echo "  ..."
    echo ""
fi

# Show Docker optimization info
echo -e "${BLUE}🐳 Docker Build Optimization:${NC}"
echo "  📁 Backend .dockerignore: $([ -f "../backend/.dockerignore" ] && echo "✅ Configured" || echo "❌ Missing")"
echo "  📁 Telegram-bot .dockerignore: $([ -f "../telegram-bot/.dockerignore" ] && echo "✅ Configured" || echo "❌ Missing")"
echo ""

echo -e "${GREEN}✅ Analysis completed!${NC}"
echo ""
echo -e "${YELLOW}Benefits of optimization:${NC}"
echo "  🚀 Faster file transfers to server"
echo "  ⚡ Faster Docker build times"
echo "  💾 Less storage usage on server"
echo "  🔒 Better security (no dev files in production)"
echo "  🎯 Cleaner deployment environment" 