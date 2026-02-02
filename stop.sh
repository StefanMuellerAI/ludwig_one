#!/bin/bash

# LudwigOne Stop Script

echo "🛑 Stopping LudwigOne..."

docker-compose down

echo "✅ LudwigOne stopped"
echo ""
echo "💾 Data is preserved in Docker volumes"
echo "🗑️  To remove all data: docker-compose down -v"
