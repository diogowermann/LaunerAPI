import win32serviceutil
import win32service
import win32event
import subprocess
import os
import sys
import logging

class FastAPIService(win32serviceutil.ServiceFramework):
    _svc_name_ = "LaunerAPIService"
    _svc_display_name_ = "Launer API Service"
    _svc_description_ = "Runs the Launer FastAPI application as a Windows service."

    def __init__(self, args):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.process = None
        
        # Setup logging
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'service.log')
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('LaunerAPIService')

    def SvcDoRun(self):
        """Start the FastAPI application."""
        try:
            app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'run.py'))
            self.logger.info(f"Starting FastAPI application from {app_path}")
            
            self.process = subprocess.Popen(
                [sys.executable, app_path],
                cwd=os.path.dirname(app_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            self.logger.info("Service started successfully")
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
        
        except Exception as e:
            self.logger.error(f"Error starting service: {str(e)}")
            raise

    def SvcStop(self):
        """Stop the FastAPI application."""
        try:
            self.logger.info("Stopping service...")
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.stop_event)
            
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=10)  # Wait up to 10 seconds for graceful shutdown
                self.logger.info("Service stopped successfully")
        
        except Exception as e:
            self.logger.error(f"Error stopping service: {str(e)}")
            raise

if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(FastAPIService)