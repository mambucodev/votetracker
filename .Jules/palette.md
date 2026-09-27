## 2024-05-18 - Missing Accessible Names on Icon-Only Buttons
**Learning:** In Qt/PySide6, icon-only buttons often lack accessible names for screen readers, unlike web buttons which use `aria-label`. While `setToolTip()` provides visual hints on hover, it's insufficient for complete accessibility.
**Action:** Always set both `setToolTip()` and `setAccessibleName()` on icon-only buttons (`QToolButton` or `QPushButton` without text). Remember to wrap the strings in the local `tr()` function for internationalization.
