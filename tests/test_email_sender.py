# tests/test_email_sender.py
from unittest.mock import patch, MagicMock
from modules.email_sender import send_email, SendResult

_SMTP_CFG = {"host": "smtp.gmail.com", "port": 587,
             "username": "a@b.com", "from_email": "a@b.com"}

def test_send_returns_success():
    with patch('smtplib.SMTP') as mock_smtp:
        ctx = MagicMock()
        mock_smtp.return_value.__enter__.return_value = ctx
        result = send_email(_SMTP_CFG, "pw", ["r@t.com"], "Subject", "<p>Hi</p>")
        assert result.success is True
        assert ctx.sendmail.called

def test_send_returns_failure_on_exception():
    with patch('smtplib.SMTP') as mock_smtp:
        mock_smtp.return_value.__enter__.side_effect = Exception("refused")
        result = send_email(_SMTP_CFG, "bad", ["r@t.com"], "Subject", "<p>Hi</p>")
        assert result.success is False
        assert "refused" in result.error
