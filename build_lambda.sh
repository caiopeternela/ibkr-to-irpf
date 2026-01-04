#!/bin/bash
set -e

echo "🧹 Cleaning up previous builds..."
rm -rf build/
rm -f lambda.zip

echo "📁 Creating build directory..."
mkdir -p build

echo "📦 Installing production dependencies..."
uv pip install --target build/ \
    --python-platform x86_64-manylinux_2_17 \
    --python-version 3.12 \
    -r <(uv pip compile pyproject.toml 2>/dev/null | grep -v "^#")

echo "📂 Copying application source code..."
cp -r src/ build/src/

echo "🗜️ Creating zip file..."
cd build
zip -r ../lambda.zip . -x "*.pyc" -x "__pycache__/*" -x "*.dist-info/*" -x "bin/*"
cd ..

echo "📊 Zip file size:"
du -h lambda.zip

echo ""
echo "✅ Build complete! lambda.zip is ready for deployment."
echo ""
echo "📋 Lambda Configuration:"
echo "   Handler: src.main.handler"
echo "   Runtime: Python 3.12"
echo "   Architecture: x86_64"
