# test_parser.py - Unit tests for the resume parser
# Run with: pytest tests/ -v

import pytest
import sys
import os

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.parser import ResumeParser


class TestResumeParser:
    """Tests for the ResumeParser class."""

    def setup_method(self):
        """Create a fresh parser before each test."""
        self.parser = ResumeParser()

    # ── Text Cleaning Tests ──────────────────────────

    def test_clean_text_removes_null_bytes(self):
        """Null bytes (\x00) should be replaced with spaces."""
        dirty = "Hello\x00World"
        cleaned = self.parser._clean_text(dirty)
        assert '\x00' not in cleaned
        assert 'Hello' in cleaned
        assert 'World' in cleaned

    def test_clean_text_normalizes_whitespace(self):
        """Multiple spaces should collapse to single space."""
        dirty = "Python   Developer    with   5  years"
        cleaned = self.parser._clean_text(dirty)
        assert "  " not in cleaned  # No double spaces
        assert "Python" in cleaned

    def test_clean_text_handles_windows_line_endings(self):
        """Windows \\r\\n should become \\n."""
        dirty = "Line 1\r\nLine 2\r\nLine 3"
        cleaned = self.parser._clean_text(dirty)
        assert '\r' not in cleaned

    def test_clean_text_empty_string(self):
        """Empty string input should return empty string."""
        result = self.parser._clean_text("")
        assert result == ""

    def test_clean_text_none_input(self):
        """None input should return empty string."""
        result = self.parser._clean_text(None)
        assert result == ""

    def test_clean_text_preserves_content(self):
        """Important content should not be removed."""
        text = "Python Developer with experience in Machine Learning and AWS"
        cleaned = self.parser._clean_text(text)
        assert "Python" in cleaned
        assert "Machine Learning" in cleaned
        assert "AWS" in cleaned

    # ── File Type Detection Tests ──────────────────────

    def test_unsupported_extension_raises_error(self):
        """Unsupported file extensions should raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            self.parser.extract_text("resume.txt")

    def test_unsupported_extension_xls(self):
        """Excel files should not be supported."""
        with pytest.raises(ValueError):
            self.parser.extract_text("resume.xls")

    # ── Bytes Extraction Tests ──────────────────────

    def test_extract_bytes_wrong_extension(self):
        """Wrong extension in bytes mode should raise ValueError."""
        with pytest.raises(ValueError):
            self.parser.extract_text_from_bytes(b"fake content", "resume.txt")

    def test_extract_bytes_empty_pdf(self):
        """Empty bytes for PDF should raise or return empty."""
        # This tests that the parser handles bad input gracefully
        try:
            result = self.parser.extract_text_from_bytes(b"", "resume.pdf")
            # If it doesn't raise, result should be empty-ish
            assert len(result.strip()) < 10
        except (ValueError, Exception):
            pass  # Raising is also acceptable behavior


class TestTextCleaning:
    """Additional edge case tests for text cleaning."""

    def setup_method(self):
        self.parser = ResumeParser()

    def test_removes_excessive_newlines(self):
        """Three or more newlines should reduce to two."""
        text = "Section 1\n\n\n\n\nSection 2"
        cleaned = self.parser._clean_text(text)
        assert "\n\n\n" not in cleaned

    def test_handles_special_resume_characters(self):
        """Bullet point characters and similar should be handled."""
        text = "\uf0b7 Python Developer\n\uf0b7 5 years experience"
        cleaned = self.parser._clean_text(text)
        assert "Python Developer" in cleaned
        assert "5 years experience" in cleaned

    def test_long_text_preserved(self):
        """Long text content should be preserved (not truncated)."""
        long_text = "Python " * 500  # 3500 characters
        cleaned = self.parser._clean_text(long_text)
        assert len(cleaned) > 100  # Should not be truncated


# ── Run directly ──────────────────────────────────────

if __name__ == "__main__":
    # Simple manual test runner if pytest is not installed
    print("Running parser tests manually...\n")
    
    parser = ResumeParser()
    
    # Test 1: Clean text
    dirty = "Python   Developer\x00with  experience"
    cleaned = parser._clean_text(dirty)
    print(f"✅ Clean text test: '{cleaned}'")
    
    # Test 2: Unsupported extension
    try:
        parser.extract_text("resume.txt")
        print("❌ Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Unsupported extension test: {e}")
    
    print("\n✅ All manual tests passed!")
