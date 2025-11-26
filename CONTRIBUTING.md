# Panduan Kontribusi PrasKaaPyKit

Selamat datang! Kami sangat menghargai kontribusi Anda untuk mengembangkan PrasKaaPyKit. Dokumen ini berisi panduan lengkap untuk berkontribusi pada proyek ini.

## 🚀 Quick Start untuk Kontributor

### 1. Setup Development Environment
```bash
# Clone repository
git clone https://github.com/praskaa/pyrevit-tools.git
cd pyrevit-tools

# Setup Python environment (jika diperlukan)
pip install -r requirements-dev.txt
```

### 2. Understanding Architecture
```
PrasKaaPyKit.extension/     # Root extension folder
├── PrasKaaPyKit.tab/       # Main pyRevit tab
│   └── [Category].panel/   # Tool categories
│       └── [Tool].pushbutton/ # Individual tools
├── lib/                    # 🟢 SHARED LIBRARIES (importable)
│   ├── Snippets/          # UI utilities
│   ├── parameters/        # Parameter utilities
│   └── [utility].py       # Shared code modules
├── logic-library/         # 🔴 DOCUMENTATION ONLY (no import)
│   └── [specifications]/  # Design docs, API specs
├── ARCHITECTURE_GUIDE.md  # 🆕 Architecture documentation
├── IMPORT_GUIDELINES.md   # 🆕 Import best practices
└── README.md              # Main project documentation
```

**⚠️ IMPORTANT**: Read `ARCHITECTURE_GUIDE.md` and `IMPORT_GUIDELINES.md` before starting development!

### 3. Development Workflow
1. **📖 Read Documentation**: `ARCHITECTURE_GUIDE.md` dan `IMPORT_GUIDELINES.md`
2. **Fork** repository
3. **Create feature branch**: `git checkout -b feature/nama-fitur`
4. **Follow import guidelines** - import dari `lib/`, bukan `logic-library/`
5. **Make changes** dengan mengikuti coding standards
6. **Test imports** dengan `test_imports.py`
7. **Test thoroughly** di multiple Revit versions
8. **Update documentation** termasuk architecture docs jika diperlukan
9. **Submit pull request**

## 📋 Coding Standards

### Python Code Style
```python
# ✅ Good: Consistent dengan PEP 8 + pyRevit conventions
def process_elements(doc, element_ids, logger=None):
    """Process multiple elements dengan error handling.

    Args:
        doc (Document): Revit document
        element_ids (List[ElementId]): Elements to process
        logger: Optional logger untuk output

    Returns:
        List[Element]: Processed elements
    """
    try:
        # Implementation here
        pass
    except Exception as e:
        if logger:
            logger.print_md("❌ Error: {}".format(str(e)))
        raise
```

### File Structure untuk New Tools
```
[ToolName].pushbutton/
├── script.py              # Main script (required)
├── README.md              # Documentation (required)
├── icon.png               # Icon 32x32px (recommended)
├── bundle.yaml            # Configuration (required)
├── config.json            # Settings (optional)
├── lib.py                 # Tool-specific library (optional)
└── [additional files]     # As needed
```

### Naming Conventions
- **Files**: `snake_case.py` (Python), `kebab-case.md` (docs)
- **Functions**: `snake_case()` dengan descriptive names
- **Classes**: `PascalCase` untuk WPF windows dan data models
- **Constants**: `UPPER_SNAKE_CASE`
- **Variables**: `snake_case` descriptive names

## 🏗️ Architecture Guidelines

### Import Pattern (UPDATED)
```python
# ❌ WRONG: Logic library hanya dokumentasi
from logic_library.active.utilities.selection.smart_selection import get_filtered_selection

# ✅ CORRECT: Import dari lib folder
from Snippets.smart_selection import get_filtered_selection
from wall_orientation_logic import WallOrientationHandler
from parameters.framework import find_parameter_element

# ✅ With error handling
try:
    from Snippets.smart_selection import get_filtered_selection
except ImportError:
    # Fallback implementation
    def get_filtered_selection(*args, **kwargs):
        return []
```

**📖 Reference**: See `IMPORT_GUIDELINES.md` for complete import patterns and `ARCHITECTURE_GUIDE.md` for architecture overview.

### Error Handling Pattern
```python
def safe_operation(doc, operation_func, logger=None):
    """Execute operation dengan comprehensive error handling."""
    t = Transaction(doc, "Operation Name")
    try:
        t.Start()
        result = operation_func()
        t.Commit()
        return result
    except Exception as e:
        t.RollBack()
        if logger:
            logger.print_md("❌ **Error**: {}".format(str(e)))
        raise
```

### UI Pattern (WPF)
```python
class CustomWindow(forms.WPFWindow):
    """Custom WPF window dengan proper error handling."""

    def __init__(self):
        # Setup UI dengan XAML
        xaml = self._load_xaml()
        forms.WPFWindow.__init__(self, xaml)

        # Initialize data dan event handlers
        self._setup_data_context()
        self._setup_event_handlers()

    def _load_xaml(self):
        """Load XAML dari embedded string atau file."""
        return """<Window xmlns="...">...</Window>"""
```

## 📚 Documentation Standards

### README.md Structure (wajib untuk setiap tool)
```markdown
# Tool Name

## Overview
Brief description dalam bahasa Indonesia.

## Features
- Feature 1
- Feature 2

## How to Use
Step-by-step instructions.

## Technical Details
Implementation details, dependencies.

## Requirements
Revit version, pyRevit version.

## Troubleshooting
Common issues dan solutions.

## Version History
Changelog untuk tool tersebut.
```

### Code Documentation
```python
# Module-level docstring
"""
Module description dalam bahasa Indonesia.

Classes:
    ClassName: Description

Functions:
    function_name: Description
"""

def function_name(param1, param2):
    """Function description dalam bahasa Indonesia.

    Args:
        param1 (Type): Description
        param2 (Type): Description

    Returns:
        Type: Description

    Raises:
        ExceptionType: When this happens
    """
    pass
```

## 🧪 Testing Guidelines

### Manual Testing Checklist
- [ ] Test di Revit 2018, 2020, 2022, 2024
- [ ] Test dengan empty selection
- [ ] Test dengan invalid inputs
- [ ] Test dengan large models (1000+ elements)
- [ ] Test error scenarios
- [ ] Verify console output
- [ ] Check transaction handling

### Automated Testing (Future)
```python
# tests/test_tool_name.py
import pytest
from PrasKaaPyKit.lib.tool_name import ToolClass

def test_tool_basic_functionality():
    """Test basic functionality."""
    # Test implementation
    pass
```

## 🔄 Pull Request Process

### PR Template
```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] 🐛 Bug fix
- [ ] ✨ New feature
- [ ] 💥 Breaking change
- [ ] 📚 Documentation
- [ ] 🎨 Style/Code quality

## Testing
- [ ] Tested di Revit [versions]
- [ ] Manual testing completed
- [ ] Documentation updated

## Screenshots (if applicable)
Add screenshots of UI changes.

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests pass
- [ ] No breaking changes
```

### Review Process
1. **Automated Checks**: Code style, basic validation
2. **Peer Review**: Code quality dan architecture
3. **Testing Review**: Functionality validation
4. **Documentation Review**: README completeness
5. **Merge**: After approval dari maintainers

## 🎯 Development Priorities

### High Priority
- Bug fixes dan stability improvements
- Performance optimizations
- User experience enhancements
- Documentation improvements

### Medium Priority
- New tools berdasarkan user requests
- UI/UX improvements
- Code refactoring

### Low Priority
- Experimental features
- Advanced automation
- Third-party integrations

## 🚨 Issue Reporting

### Bug Reports
```markdown
**Environment:**
- Revit version: [e.g., 2024]
- pyRevit version: [e.g., 4.8.12]
- OS: [e.g., Windows 11]

**Steps to reproduce:**
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior:**
What should happen

**Actual behavior:**
What actually happens

**Error messages:**
```
Console output atau error messages

**Screenshots:**
If applicable

### Feature Requests
```markdown
**Problem:**
Current limitation atau pain point

**Solution:**
Proposed solution

**Alternatives:**
Other approaches considered

**Additional context:**
Use cases, examples, mockups
```

## 📞 Communication

### Channels
- **GitHub Issues**: Bug reports dan feature requests
- **GitHub Discussions**: General questions dan ideas
- **Email**: support@praskaa.com untuk urgent issues

### Response Times
- **Bug fixes**: Within 1-2 weeks
- **Feature requests**: Response within 1 week
- **General questions**: Within 3-5 business days

## 🎉 Recognition

Contributors akan diakui di:
- CHANGELOG.md untuk significant contributions
- README.md acknowledgments
- GitHub contributors list
- Release notes

### Contribution Levels
- **🥉 Contributor**: Bug fixes, small improvements
- **🥈 Active Contributor**: Multiple contributions, documentation
- **🥇 Core Contributor**: Major features, architecture decisions
- **👑 Maintainer**: Ongoing maintenance, project direction

## 📋 Code of Conduct

### Standards
- **Respectful**: Treat all contributors dengan respect
- **Inclusive**: Welcome contributions dari semua backgrounds
- **Constructive**: Provide helpful feedback
- **Professional**: Maintain professional communication

### Unacceptable Behavior
- Harassment atau discriminatory language
- Personal attacks
- Spam atau off-topic content
- Sharing confidential information

---

**Terima kasih atas kontribusi Anda untuk PrasKaaPyKit! 🚀**

*Untuk questions, silakan buat issue di GitHub atau email ke tim development.*