# v2.7.1 - CI Workflow and Enhanced Interactive Charts

## What's New

### CI/CD Workflow
- **Automated testing pipeline** with GitHub Actions
- **Test matrix** covering Python 3.8, 3.9, 3.10, 3.11, and 3.12
- **Code quality checks** with pyflakes for syntax errors and undefined names
- **Test coverage reporting** with HTML coverage reports uploaded as artifacts
- Runs automatically on every push and pull request to main branch

### Enhanced Interactive Charts
- **InteractiveBarChart** - Horizontal bars with gradient styling and hover tooltips showing detailed statistics
- **InteractiveDistributionChart** - Grade distribution histogram with percentage displays
- **GradeTrendChart** - Line chart showing grade progression over time with date labels
- Smooth hover animations and anti-aliased rendering for professional appearance
- Rich HTML tooltips displaying vote counts, grade breakdowns by type, and more

### Changes
- Updated Statistics page to use new enhanced chart widgets
- All existing charts replaced with interactive versions
- Added translations for "Grade Trend Over Time" (English and Italian)

## Technical Details

**New Files:**
- `.github/workflows/test.yml` - CI/CD pipeline with 3 jobs (test matrix, lint, coverage)
- `src/votetracker/enhanced_charts.py` - Interactive chart widgets (588 lines)

**Modified Files:**
- `src/votetracker/pages/statistics.py` - Integrated enhanced charts
- `src/votetracker/i18n.py` - Added new translations

**Testing:**
- All tests pass on Python 3.8-3.12
- No breaking changes
- Fully backward compatible

## Installation

**Arch Linux:**
```bash
yay -S votetracker
# or
cd scripts && makepkg -si
```

**pip:**
```bash
pip install --upgrade votetracker
```

**From source:**
```bash
git clone https://github.com/mambucodev/votetracker
cd votetracker
pip install .
```
