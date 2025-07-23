# Strategy Refactoring Troubleshooting Guide

## 🔧 **COMPREHENSIVE TROUBLESHOOTING GUIDE**

This document provides detailed solutions for common issues that may arise during the strategy refactoring implementation.

---

## 🚨 **COMMON ISSUES AND SOLUTIONS**

### **Issue 1: Import Errors**

#### **Symptoms:**
```
ImportError: cannot import name 'VolumeMomentumStrategy' from 'core.token_discovery_strategies'
```

#### **Root Causes:**
- Individual strategy files don't exist
- Import aggregator not correctly importing from individual files
- Typos in file names or class names
- Python path issues

#### **Solutions:**

**Step 1: Verify File Existence**
```bash
ls -la core/
# Should show all individual strategy files
```

**Step 2: Check Import Aggregator**
```python
# In core/token_discovery_strategies.py, verify:
from core.volume_momentum_strategy import VolumeMomentumStrategy
# Not:
from core.volume_momentum_strategy import VolumeStrategy  # Wrong!
```

**Step 3: Test Individual Imports**
```python
# Test each file individually:
from core.base_token_discovery_strategy import BaseTokenDiscoveryStrategy
from core.volume_momentum_strategy import VolumeMomentumStrategy
# etc.
```

---

### **Issue 2: Circular Import Errors**

#### **Symptoms:**
```
ImportError: cannot import name 'BaseTokenDiscoveryStrategy' from partially initialized module
```

#### **Root Causes:**
- Base strategy file importing from strategy files
- Strategy files importing from each other
- Import aggregator causing circular dependencies

#### **Solutions:**

**Step 1: Check Base Strategy File**
```python
# In core/base_token_discovery_strategy.py
# SHOULD NOT import any strategy files:
# ❌ from core.volume_momentum_strategy import VolumeMomentumStrategy  # Wrong!

# SHOULD only import external dependencies:
# ✅ from api.birdeye_connector import BirdeyeAPI  # Correct
```

**Step 2: Check Strategy Files**
```python
# In individual strategy files, ONLY import base class:
# ✅ from core.base_token_discovery_strategy import BaseTokenDiscoveryStrategy
# ❌ from core.volume_momentum_strategy import VolumeMomentumStrategy  # Wrong!
```

---

### **Issue 3: Missing Dependencies**

#### **Symptoms:**
```
NameError: name 'filter_major_tokens' is not defined
```

#### **Root Causes:**
- Missing imports in individual strategy files
- Dependencies not copied from original file

#### **Solutions:**

**Step 1: Check Required Imports in Strategy Files**
```python
# Each strategy file needs:
from typing import Dict, List, Any, Optional
import logging  # If used
import time     # If used (RecentListingsStrategy)

from core.base_token_discovery_strategy import BaseTokenDiscoveryStrategy
from api.birdeye_connector import BirdeyeAPI
```

**Step 2: Add Missing Function Imports**
```python
# If strategy uses filter_major_tokens, add to base class or import directly:
# In the execute method of base class, we have:
from services.early_token_detection import filter_major_tokens
```

---

### **Issue 4: Tests Failing**

#### **Symptoms:**
```
AttributeError: 'VolumeMomentumStrategy' object has no attribute 'some_method'
```

#### **Root Causes:**
- Incomplete class definitions in individual files
- Missing methods during copy/paste
- Incorrect inheritance

#### **Solutions:**

**Step 1: Verify Complete Class Copy**
```bash
# Check line counts match original:
# Original BaseTokenDiscoveryStrategy: lines 30-359 (329 lines)
wc -l core/base_token_discovery_strategy.py
# Should be approximately 329 lines + imports
```

**Step 2: Compare Method Signatures**
```python
# Original and refactored should have identical methods:
import inspect
from core.token_discovery_strategies import VolumeMomentumStrategy as Original
from core.volume_momentum_strategy import VolumeMomentumStrategy as Refactored

original_methods = set(dir(Original()))
refactored_methods = set(dir(Refactored()))
missing = original_methods - refactored_methods
extra = refactored_methods - original_methods
print(f"Missing: {missing}")
print(f"Extra: {extra}")
```

---

### **Issue 5: File Permission Errors**

#### **Symptoms:**
```
PermissionError: [Errno 13] Permission denied: 'core/base_token_discovery_strategy.py'
```

#### **Solutions:**
```bash
# Fix file permissions:
chmod 644 core/*.py
```

---

### **Issue 6: Syntax Errors in New Files**

#### **Symptoms:**
```
SyntaxError: invalid syntax
```

#### **Root Causes:**
- Incomplete copy/paste operations
- Missing imports or class definitions
- Indentation errors

#### **Solutions:**

**Step 1: Validate Python Syntax**
```bash
# Check each file for syntax errors:
python -m py_compile core/base_token_discovery_strategy.py
python -m py_compile core/volume_momentum_strategy.py
# etc.
```

**Step 2: Check Indentation**
```python
# Ensure consistent indentation (4 spaces)
# Use your editor's "show whitespace" feature
```

---

### **Issue 7: Storage/History File Conflicts**

#### **Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/discovery_results/...'
```

#### **Root Causes:**
- Storage paths changed during refactoring
- History files not accessible

#### **Solutions:**

**Step 1: Verify Storage Directory Structure**
```bash
mkdir -p data/discovery_results
```

**Step 2: Check Storage File Naming**
```python
# In base class, storage file naming should remain the same:
self.storage_file = self.storage_dir / f"{name.lower().replace(' ', '_')}_results.json"
```

---

## 🧪 **DEBUGGING TECHNIQUES**

### **1. Step-by-Step Import Testing**

```python
# Test imports one by one:
try:
    from core.base_token_discovery_strategy import BaseTokenDiscoveryStrategy
    print("✅ Base strategy imported")
except Exception as e:
    print(f"❌ Base strategy failed: {e}")

try:
    from core.volume_momentum_strategy import VolumeMomentumStrategy
    print("✅ Volume momentum imported")
except Exception as e:
    print(f"❌ Volume momentum failed: {e}")

# Continue for each strategy...
```

### **2. Class Comparison**

```python
# Compare original vs refactored classes:
def compare_classes(original_cls, refactored_cls):
    orig_attrs = set(dir(original_cls))
    refact_attrs = set(dir(refactored_cls))
    
    missing = orig_attrs - refact_attrs
    extra = refact_attrs - orig_attrs
    
    print(f"Missing attributes: {missing}")
    print(f"Extra attributes: {extra}")
    
    return len(missing) == 0 and len(extra) == 0
```

### **3. Method Signature Verification**

```python
import inspect

def verify_method_signatures(original_cls, refactored_cls):
    for attr_name in dir(original_cls):
        if callable(getattr(original_cls, attr_name)):
            orig_method = getattr(original_cls, attr_name)
            refact_method = getattr(refactored_cls, attr_name, None)
            
            if refact_method is None:
                print(f"❌ Missing method: {attr_name}")
                continue
                
            orig_sig = inspect.signature(orig_method)
            refact_sig = inspect.signature(refact_method)
            
            if orig_sig != refact_sig:
                print(f"❌ Signature mismatch for {attr_name}:")
                print(f"   Original: {orig_sig}")
                print(f"   Refactored: {refact_sig}")
```

---

## 🔄 **ROLLBACK PROCEDURES**

### **Complete Rollback**

If the refactoring fails completely:

```bash
# 1. Remove all new files
rm core/base_token_discovery_strategy.py
rm core/volume_momentum_strategy.py
rm core/recent_listings_strategy.py
rm core/price_momentum_strategy.py
rm core/liquidity_growth_strategy.py
rm core/high_trading_activity_strategy.py

# 2. Restore original file
cp core/token_discovery_strategies.py.backup core/token_discovery_strategies.py

# 3. Verify system works
python -m pytest tests/unit/test_token_discovery_strategies.py -v
```

### **Partial Rollback**

If only some files have issues:

```bash
# Remove problematic files and recreate them
rm core/volume_momentum_strategy.py
# Recreate with correct content
```

---

## ✅ **VALIDATION CHECKLIST**

After fixing any issues, run through this checklist:

### **File Structure Validation**
- [ ] All 7 files exist in core/ directory
- [ ] All files have proper .py extension
- [ ] File permissions are correct (644)

### **Import Validation**
- [ ] Base strategy imports work
- [ ] Individual strategy imports work
- [ ] Backward compatibility imports work
- [ ] No circular import errors

### **Class Validation**
- [ ] All strategies can be instantiated
- [ ] All methods are accessible
- [ ] Inheritance works correctly
- [ ] Parameters are properly set

### **Functionality Validation**
- [ ] Existing tests pass
- [ ] New validation test passes
- [ ] System functionality unchanged
- [ ] No performance degradation

### **Integration Validation**
- [ ] Dependent modules work
- [ ] Scripts run without errors
- [ ] No breaking changes introduced

---

## 📞 **GETTING HELP**

If you encounter issues not covered in this guide:

1. **Check the validation test output** - It provides detailed error messages
2. **Compare with original file** - Use diff tools to verify correct copying
3. **Test incrementally** - Don't implement all at once
4. **Use the rollback procedure** - Return to working state if needed
5. **Verify environment** - Ensure Python path and dependencies are correct

---

## 📝 **PREVENTION TIPS**

To avoid common issues:

1. **Always create backups** before starting
2. **Test after each step** - Don't wait until the end
3. **Use exact copy/paste** - Don't retype code
4. **Verify imports immediately** after creating each file
5. **Run validation tests frequently** during implementation
6. **Keep original file** until everything is verified working

---

**🎯 Remember: The goal is to maintain 100% functionality while improving organization. If in doubt, rollback and try again!** 