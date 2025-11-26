# Changelog PrasKaaPyKit

Semua perubahan penting pada PrasKaaPyKit akan didokumentasikan di file ini.

Format changelog ini mengikuti [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
dan versi mengikuti [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-11-16

### Added
- **Major Release**: PrasKaaPyKit v2.0.0 - Complete rewrite dengan arsitektur modular
- **New Category: Documentation Panel**
  - Wall Detail Generator dengan template lengkap
  - Smart annotation tools
  - View management utilities
  - Sheet numbering automation
- **New Category: QualityControl Panel**
  - EXR Column validation tools
  - EXR Framing matching tools
  - Type mark checkers
  - Auto-load missing types
- **New Category: Rebar Panel**
  - Multi-layer area reinforcement dari filled region
  - Rebar inspection utilities
  - Area reinforcement parameter management
- **New Category: Templates Panel**
  - Family type generator dari CSV
  - Profile update utilities
  - Template repository system
- **Enhanced Line Color Tools**
  - Custom color picker dengan pattern support
  - Line & Pattern Color combined tool
  - Extended color palette (15+ tools)
- **Advanced Modeling Tools**
  - Join Shearwall & Corewall dengan priority logic
  - Auto-dimension tools untuk column dan wall
  - Framing manipulation utilities
- **Utility Enhancements**
  - Grid management (2D/3D toggle, table creation)
  - Adaptive point utilities
  - Detail item inspection tools
- **Logic Library Architecture**
  - Modular logic library system
  - Shared utilities dan helpers
  - Unit conversion framework
  - Parameter mapping system
- **Documentation System**
  - Comprehensive README.md untuk setiap alat
  - CHANGELOG.md tracking per alat
  - Technical specification documents
  - Troubleshooting guides

### Changed
- **Architecture**: Complete modular redesign dengan logic library separation
- **UI/UX**: Enhanced dengan WPF interfaces dan better error handling
- **Performance**: Optimized untuk large models dengan batch processing
- **Compatibility**: Extended support dari Revit 2018 ke 2026
- **Language**: Consistent Indonesian documentation dengan bilingual support

### Deprecated
- Legacy single-file scripts (migrated ke modular architecture)
- Old parameter mapping system (replaced dengan flexible matcher)

### Removed
- Outdated utilities yang tidak kompatibel dengan Revit 2020+
- Redundant tools yang digantikan dengan enhanced versions

### Fixed
- Memory leaks di large model processing
- Transaction handling issues
- Parameter setting errors untuk different storage types
- UI freezing pada complex operations

### Security
- Input validation untuk CSV processing
- Safe parameter setting dengan error recovery
- Transaction rollback pada critical failures

## [1.5.0] - 2024-08-15

### Added
- Initial Wall Detail Generator prototype
- Basic rebar inspection tools
- Enhanced join geometry utilities
- Grid management tools

### Changed
- Improved error handling across all tools
- Better UI feedback dan progress indicators

### Fixed
- Critical bugs di parameter setting
- Memory issues di large projects

## [1.0.0] - 2024-01-01

### Added
- Initial release PrasKaaPyKit
- Basic modeling tools (join, dimension)
- Line color utilities
- Core utility functions
- Basic documentation

### Changed
- Foundation architecture establishment
- Initial pyRevit integration

---

## Development Guidelines

### Version Numbering
Kami menggunakan [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes, architecture changes
- **MINOR**: New features, significant enhancements
- **PATCH**: Bug fixes, small improvements

### Changelog Categories
- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security-related changes

### Release Process
1. Update version numbers di semua files
2. Update CHANGELOG.md dengan perubahan baru
3. Tag release di git
4. Publish ke distribution channel
5. Update documentation

---

**Legend:**
- 🔴 Breaking Change
- 🟡 Major Feature
- 🟢 Enhancement
- 🔵 Bug Fix
- 🟣 Security