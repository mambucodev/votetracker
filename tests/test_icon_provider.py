import unittest
from unittest.mock import patch, MagicMock

from src.votetracker.icon_provider import (
    get_icon,
    has_icon,
    get_icon_fallback,
    create_simple_svg_icon
)

class TestIconProvider(unittest.TestCase):
    def test_has_icon(self):
        """has_icon should always return True."""
        self.assertTrue(has_icon("any-icon-name"))
        self.assertTrue(has_icon(""))

    def test_get_icon_fallback(self):
        """get_icon_fallback should always return a bullet point."""
        self.assertEqual(get_icon_fallback("any-icon-name"), "●")
        self.assertEqual(get_icon_fallback("home"), "●")

    @patch('src.votetracker.icon_provider.QApplication')
    @patch('src.votetracker.icon_provider.QIcon')
    def test_get_icon_standard(self, mock_qicon, mock_qapp):
        """Test getting a standard icon."""
        # Setup mock app and style
        mock_instance = MagicMock()
        mock_style = MagicMock()
        mock_icon = MagicMock()
        mock_icon.isNull.return_value = False

        mock_qapp.instance.return_value = mock_instance

        # We need to bypass the isinstance check by mocking the class itself or skipping it
        # Actually, let's just make isinstance return True for this specific test
        import builtins
        original_isinstance = builtins.isinstance

        def mock_isinstance(obj, class_or_tuple):
            if obj is mock_instance:
                return True
            return original_isinstance(obj, class_or_tuple)

        with patch('builtins.isinstance', mock_isinstance):
            mock_instance.style.return_value = mock_style
            mock_style.standardIcon.return_value = mock_icon

            # document-save is in STANDARD_ICON_MAP
            result = get_icon("document-save")

            # Verify
            mock_style.standardIcon.assert_called_once()
            self.assertEqual(result, mock_icon)

    @patch('src.votetracker.icon_provider.QApplication')
    @patch('src.votetracker.icon_provider.QIcon')
    def test_get_icon_theme(self, mock_qicon, mock_qapp):
        """Test getting an icon from theme."""
        mock_qapp.instance.return_value = None

        mock_theme_icon = MagicMock()
        mock_theme_icon.isNull.side_effect = [False]
        mock_qicon.fromTheme.return_value = mock_theme_icon

        result = get_icon("non-standard-icon")

        mock_qicon.fromTheme.assert_called_once_with("non-standard-icon")
        self.assertEqual(result, mock_theme_icon)

    @patch('src.votetracker.icon_provider.QApplication')
    @patch('src.votetracker.icon_provider.QIcon')
    def test_get_icon_theme_symbolic(self, mock_qicon, mock_qapp):
        """Test getting an icon from theme with symbolic suffix."""
        mock_qapp.instance.return_value = None

        mock_theme_icon_null = MagicMock()
        mock_theme_icon_null.isNull.return_value = True

        mock_theme_icon_valid = MagicMock()
        mock_theme_icon_valid.isNull.return_value = False

        mock_qicon.fromTheme.side_effect = [mock_theme_icon_null, mock_theme_icon_valid]

        result = get_icon("non-standard-icon")

        self.assertEqual(mock_qicon.fromTheme.call_count, 2)
        mock_qicon.fromTheme.assert_any_call("non-standard-icon")
        mock_qicon.fromTheme.assert_any_call("non-standard-icon-symbolic")
        self.assertEqual(result, mock_theme_icon_valid)

    @patch('src.votetracker.icon_provider.create_simple_svg_icon')
    @patch('src.votetracker.icon_provider.QApplication')
    @patch('src.votetracker.icon_provider.QIcon')
    def test_get_icon_fallback_svg(self, mock_qicon, mock_qapp, mock_create_svg):
        """Test getting an SVG fallback icon."""
        mock_qapp.instance.return_value = None

        mock_theme_icon = MagicMock()
        mock_theme_icon.isNull.return_value = True
        mock_qicon.fromTheme.return_value = mock_theme_icon

        mock_svg_icon = MagicMock()
        mock_create_svg.return_value = mock_svg_icon

        result = get_icon("view-dashboard")

        mock_create_svg.assert_called_once_with("dashboard")
        self.assertEqual(result, mock_svg_icon)

    @patch('src.votetracker.icon_provider.create_simple_svg_icon')
    @patch('src.votetracker.icon_provider.QApplication')
    @patch('src.votetracker.icon_provider.QIcon')
    def test_get_icon_fallback_type(self, mock_qicon, mock_qapp, mock_create_svg):
        """Test getting an SVG fallback icon with explicit fallback_type."""
        mock_qapp.instance.return_value = None

        mock_theme_icon = MagicMock()
        mock_theme_icon.isNull.return_value = True
        mock_qicon.fromTheme.return_value = mock_theme_icon

        mock_svg_icon = MagicMock()
        mock_create_svg.return_value = mock_svg_icon

        result = get_icon("unknown-icon", fallback_type="settings")

        mock_create_svg.assert_called_once_with("settings")
        self.assertEqual(result, mock_svg_icon)

    @patch('src.votetracker.icon_provider.QSvgRenderer')
    @patch('src.votetracker.icon_provider.QPixmap')
    @patch('src.votetracker.icon_provider.QPainter')
    @patch('src.votetracker.icon_provider.QIcon')
    def test_create_simple_svg_icon(self, mock_qicon, mock_qpainter, mock_qpixmap, mock_qsvgrenderer):
        """Test creation of SVG icon."""
        # Setup mocks
        mock_pixmap_instance = MagicMock()
        mock_qpixmap.return_value = mock_pixmap_instance

        mock_painter_instance = MagicMock()
        mock_qpainter.return_value = mock_painter_instance

        mock_renderer_instance = MagicMock()
        mock_qsvgrenderer.return_value = mock_renderer_instance

        mock_icon_instance = MagicMock()
        mock_qicon.return_value = mock_icon_instance

        # Call function
        result = create_simple_svg_icon("home", size=32, color="#FF0000")

        # Verify calls
        mock_qsvgrenderer.assert_called_once()
        mock_qpixmap.assert_called_once_with(32, 32)
        mock_pixmap_instance.fill.assert_called_once()
        mock_qpainter.assert_called_once_with(mock_pixmap_instance)
        mock_renderer_instance.render.assert_called_once_with(mock_painter_instance)
        mock_painter_instance.end.assert_called_once()
        mock_qicon.assert_called_once_with(mock_pixmap_instance)

        self.assertEqual(result, mock_icon_instance)

if __name__ == '__main__':
    unittest.main()
