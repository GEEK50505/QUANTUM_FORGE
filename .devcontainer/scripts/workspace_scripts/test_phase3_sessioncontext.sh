#!/bin/bash

# Phase 3 Session Context Test Script
# This script helps verify the SessionContext integration is working

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║          PHASE 3: SESSION CONTEXT TEST SUITE                      ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
  echo "❌ Error: frontend directory not found"
  exit 1
fi

echo "✅ Frontend directory found"
echo ""

# Check if SessionContext files were created
echo "📋 Checking SessionContext files..."
echo ""

if [ -f "frontend/src/context/SessionContext.tsx" ]; then
  echo "✅ SessionContext.tsx exists"
  wc -l frontend/src/context/SessionContext.tsx | awk '{print "   " $1 " lines of code"}'
else
  echo "❌ SessionContext.tsx NOT FOUND"
fi

if [ -f "frontend/src/context/SessionContext.examples.tsx" ]; then
  echo "✅ SessionContext.examples.tsx exists"
  wc -l frontend/src/context/SessionContext.examples.tsx | awk '{print "   " $1 " lines (documentation)"}'
else
  echo "❌ SessionContext.examples.tsx NOT FOUND"
fi

if [ -f "frontend/src/components/SessionDebugger.tsx" ]; then
  echo "✅ SessionDebugger.tsx exists"
  wc -l frontend/src/components/SessionDebugger.tsx | awk '{print "   " $1 " lines (dev tool)"}'
else
  echo "❌ SessionDebugger.tsx NOT FOUND"
fi

echo ""
echo "🔍 Checking integration points..."
echo ""

# Check App.tsx has SessionProvider
if grep -q "SessionProvider" frontend/src/App.tsx; then
  echo "✅ App.tsx has SessionProvider wrapper"
else
  echo "❌ App.tsx missing SessionProvider"
fi

# Check JobForm imports useSession
if grep -q "useSession" frontend/src/components/JobForm.tsx; then
  echo "✅ JobForm.tsx imports useSession hook"
else
  echo "❌ JobForm.tsx doesn't use useSession"
fi

# Check Dashboard has SessionDebugger
if grep -q "SessionDebugger" frontend/src/pages/Dashboard.tsx; then
  echo "✅ Dashboard.tsx includes SessionDebugger"
else
  echo "❌ Dashboard.tsx missing SessionDebugger"
fi

echo ""
echo "📊 File Statistics:"
echo ""

echo "Session Context Files:"
find frontend/src/context -name "*.tsx" -o -name "*.ts" | while read file; do
  if [[ ! "$file" == *".bak"* ]]; then
    size=$(wc -c < "$file")
    lines=$(wc -l < "$file")
    printf "  %-50s %6d bytes, %4d lines\n" "$(basename $file)" "$size" "$lines"
  fi
done

echo ""
echo "Integration Changes:"
total_changes=$(grep -l "useSession\|SessionProvider\|SessionDebugger" frontend/src/App.tsx frontend/src/components/JobForm.tsx frontend/src/pages/Dashboard.tsx 2>/dev/null | wc -l)
echo "  Components modified: $total_changes"

echo ""
echo "✨ MANUAL TESTING CHECKLIST:"
echo ""
echo "1. Start the frontend: npm run dev"
echo "2. Open http://localhost:5174 in your browser"
echo "3. Look for '🐛 Session Debug' button (bottom-right corner)"
echo "4. Enter a molecule name and XYZ file"
echo "5. Click '💾 Save Now' in debugger"
echo "6. Check 'localStorage Data' section in debugger"
echo "7. Refresh the page (Ctrl+R / Cmd+R)"
echo "8. Verify data is restored"
echo ""

echo "📚 Documentation:"
if [ -f "docs/PHASE_3_SESSION_CONTEXT.md" ]; then
  echo "✅ docs/PHASE_3_SESSION_CONTEXT.md created ($(wc -l < docs/PHASE_3_SESSION_CONTEXT.md) lines)"
else
  echo "⚠️  docs/PHASE_3_SESSION_CONTEXT.md not found"
fi

echo ""
echo "✅ PHASE 3 SESSION CONTEXT - READY FOR TESTING"
echo ""
echo "Next steps:"
echo "  1. Run: npm run dev (from frontend directory)"
echo "  2. Test session persistence with SessionDebugger"
echo "  3. Verify localStorage restoration after page reload"
echo "  4. Review docs/PHASE_3_SESSION_CONTEXT.md for full guide"
echo ""
