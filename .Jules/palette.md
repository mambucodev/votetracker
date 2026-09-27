## 2024-05-18 - Add Tooltips & Accessible Names to Icon-Only Buttons
**Learning:** Icon-only navigation buttons in custom Qt widgets (like YearSelector) lack text contexts and are completely opaque to screen readers if not properly labeled.
**Action:** Always add `setToolTip` and `setAccessibleName` to any QToolButton that relies purely on visual icons.
