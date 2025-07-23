#!/usr/bin/env python3
"""
🔧 Fix the final indentation error in high_conviction_token_detector.py
"""

print("🔧 Fixing final indentation error...")

# Read the file
with open('scripts/high_conviction_token_detector.py', 'r') as f:
    content = f.read()

# Fix the indentation error in except block
old_section = """            except Exception as e:
            self.logger.error(f"❌ Error printing cycle summary: {e}")"""

new_section = """            except Exception as e:
                self.logger.error(f"❌ Error printing cycle summary: {e}")"""

# Apply the fix
if old_section in content:
    content = content.replace(old_section, new_section)
    print("✅ Fixed final indentation error")
else:
    print("⚠️ Except block not found in expected location")

# Write the fixed content back
with open('scripts/high_conviction_token_detector.py', 'w') as f:
    f.write(content)

print("🎉 All syntax errors fixed!")
