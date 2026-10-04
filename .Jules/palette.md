## 2024-05-18 - Missing Accessible Names on Icon-Only Buttons
**Learning:** In Qt/PySide6, icon-only buttons often lack accessible names for screen readers, unlike web buttons which use `aria-label`. While `setToolTip()` provides visual hints on hover, it's insufficient for complete accessibility.
**Action:** Always set both `setToolTip()` and `setAccessibleName()` on icon-only buttons (`QToolButton` or `QPushButton` without text). Remember to wrap the strings in the local `tr()` function for internationalization.
## 2024-05-19 - QLineEdit Clear Buttons

**Learning:** `QLineEdit` widgets in PySide6/Qt do not show clear buttons by default, unlike many modern desktop inputs. Enabling them is a standard, low-effort UX polish that users expect for text inputs.
**Action:** Always consider `setClearButtonEnabled(True)` for `QLineEdit` instances (search inputs, form fields) unless there's a specific reason not to.

## 2024-05-19 - Action Button Tooltips

**Learning:** Buttons with clear labels (e.g. "Delete") paired with icons still benefit from tooltips to clarify the exact impact of the action (e.g. "Delete mapping" vs "Delete selected year"), especially in dense interfaces.
**Action:** Provide specific tooltips for generic action buttons (Add, Delete, Edit) to offer contextual clarity.
