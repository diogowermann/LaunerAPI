import logging
from logging.handlers import RotatingFileHandler, SMTPHandler

# Configure logging
def setup_logging():
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    log_file = "app.log"

    # Rotating file handler (limits log file size)
    file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setFormatter(log_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    # SMTP handler for sending error logs via email
    smtp_handler = SMTPHandler(
        mailhost=("host", 587),
        fromaddr="from email",
        toaddrs=["address email"], 
        subject="sub",
        credentials=("email", "pass"),  # Replace with your email credentials
        secure=()
    )
    smtp_handler.setLevel(logging.ERROR)  # Only send emails for errors
    smtp_handler.setFormatter(log_formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)  # Set default log level
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(smtp_handler)