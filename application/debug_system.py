"""
Debug System for Renderware Modding Suite
Simple file-based logging system that writes everything to a .log file
"""

import os
import sys
import time
import json
import traceback
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import colorama
from colorama import Fore, Back, Style

class LogLevel(Enum):
    """Debug log levels"""
    TRACE = 0
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5


class LogCategory(Enum):
    """Log categories for better organization"""
    SYSTEM = "SYSTEM"
    UI = "UI"
    FILE_IO = "FILE_IO"
    TOOL = "TOOL"
    MEMORY = "MEMORY"
    PERFORMANCE = "PERFORMANCE"
    USER_ACTION = "USER_ACTION"
    ERROR = "ERROR"


class DebugLogger:
    """Simple debug logger that outputs to terminal and writes to log file"""
    
    def __init__(self):
        # Initialize colorama for colored terminal output
        colorama.init(autoreset=True)
        self.session_start = datetime.now()
        self.active_timers = {}
        self.lock = threading.Lock()
        
        # Create logs directory
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Setup log file
        self.log_file = self.logs_dir / f"debug_session_{self.session_start.strftime('%Y%m%d_%H%M%S')}.log"
        
        # Color mapping for terminal output
        self.level_colors = {
            LogLevel.TRACE: Fore.LIGHTBLACK_EX,
            LogLevel.DEBUG: Fore.CYAN,
            LogLevel.INFO: Fore.GREEN,
            LogLevel.WARNING: Fore.YELLOW,
            LogLevel.ERROR: Fore.RED,
            LogLevel.CRITICAL: Fore.MAGENTA + Style.BRIGHT
        }
        
        self.category_colors = {
            LogCategory.SYSTEM: Fore.BLUE,
            LogCategory.UI: Fore.LIGHTBLUE_EX,
            LogCategory.FILE_IO: Fore.LIGHTGREEN_EX,
            LogCategory.TOOL: Fore.LIGHTYELLOW_EX,
            LogCategory.MEMORY: Fore.LIGHTMAGENTA_EX,
            LogCategory.PERFORMANCE: Fore.LIGHTCYAN_EX,
            LogCategory.USER_ACTION: Fore.WHITE,
            LogCategory.ERROR: Fore.LIGHTRED_EX
        }
        
        # Initialize with session start
        self.log(LogLevel.INFO, LogCategory.SYSTEM, "Debug session started", {
            "session_id": self.session_start.isoformat(),
            "python_version": sys.version,
            "platform": sys.platform
        })
    
    
    def log(self, level: LogLevel, category: LogCategory, message: str, 
            data: Optional[Dict[str, Any]] = None, source: Optional[str] = None):
        """Main logging method"""
        with self.lock:
            # Get caller info if not provided
            if source is None:
                frame = sys._getframe(1)
                source = f"{frame.f_code.co_filename}:{frame.f_lineno}"
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": level.name,
                "category": category.value,
                "message": message,
                "source": source,
                "data": data or {},
                "thread": threading.current_thread().name
            }
            
            # Write to file
            self._write_to_file(log_entry)
            
            # Print to terminal
            self._print_to_terminal(log_entry)
    
    def _write_to_file(self, log_entry: dict):
        """Write log entry to file"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"Failed to write log to file: {e}")
    
    def _print_to_terminal(self, log_entry: dict):
        """Print formatted log entry to terminal with colors"""
        try:
            timestamp = datetime.fromisoformat(log_entry["timestamp"]).strftime("%H:%M:%S.%f")[:-3]
            level = LogLevel[log_entry["level"]]
            category = LogCategory[log_entry["category"]]
            message = log_entry["message"]
            thread = log_entry.get("thread", "Main")
            
            # Get colors
            level_color = self.level_colors.get(level, "")
            category_color = self.category_colors.get(category, "")
            
            # Format main log line
            formatted_line = (
                f"{Fore.WHITE}[{timestamp}] "
                f"{level_color}{level.name.ljust(8)} "
                f"{category_color}{category.value.ljust(12)} "
                f"{Fore.WHITE}{message}"
            )
            
            # Add thread info if not main thread
            if thread != "MainThread":
                formatted_line += f" {Fore.LIGHTBLACK_EX}[{thread}]"
            
            print(formatted_line)
            
            # Print additional data if present
            if log_entry.get("data"):
                data = log_entry["data"]
                if isinstance(data, dict) and data:
                    print(f"{Fore.LIGHTBLACK_EX}    └─ Data: {json.dumps(data, indent=6)[1:-1]}")
            
            # Print source info for errors and critical logs
            if level.value >= LogLevel.ERROR.value and log_entry.get("source"):
                print(f"{Fore.LIGHTBLACK_EX}    └─ Source: {log_entry['source']}")
                
        except Exception as e:
            # Fallback to simple print if formatting fails
            print(f"[DEBUG] {log_entry.get('message', 'Unknown message')} - {e}")
    
    def trace(self, category: LogCategory, message: str, data: Optional[Dict] = None):
        """Log trace level message"""
        self.log(LogLevel.TRACE, category, message, data)
    
    def debug(self, category: LogCategory, message: str, data: Optional[Dict] = None):
        """Log debug level message"""
        self.log(LogLevel.DEBUG, category, message, data)
    
    def info(self, category: LogCategory, message: str, data: Optional[Dict] = None):
        """Log info level message"""
        self.log(LogLevel.INFO, category, message, data)
    
    def warning(self, category: LogCategory, message: str, data: Optional[Dict] = None):
        """Log warning level message"""
        self.log(LogLevel.WARNING, category, message, data)
    
    def error(self, category: LogCategory, message: str, data: Optional[Dict] = None):
        """Log error level message"""
        self.log(LogLevel.ERROR, category, message, data)
    
    def critical(self, category: LogCategory, message: str, data: Optional[Dict] = None):
        """Log critical level message"""
        self.log(LogLevel.CRITICAL, category, message, data)
    
    def log_exception(self, category: LogCategory, message: str, exception: Exception):
        """Log an exception with full traceback"""
        self.error(category, message, {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "traceback": traceback.format_exc()
        })
    
    def log_function_call(self, func_name: str, args: tuple = (), kwargs: dict = None):
        """Log function call with parameters"""
        self.trace(LogCategory.SYSTEM, f"Function call: {func_name}", {
            "function": func_name,
            "args": str(args)[:200],  # Limit length
            "kwargs": str(kwargs or {})[:200]
        })
    
    def log_user_action(self, action: str, details: Optional[Dict] = None):
        """Log user actions"""
        self.info(LogCategory.USER_ACTION, f"User action: {action}", details)
    
    def log_file_operation(self, operation: str, file_path: str, success: bool = True, 
                          details: Optional[Dict] = None):
        """Log file operations"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        self.log(level, LogCategory.FILE_IO, f"File {operation}: {file_path}", details)
    
    def log_tool_operation(self, tool_name: str, operation: str, details: Optional[Dict] = None):
        """Log tool operations"""
        self.info(LogCategory.TOOL, f"Tool {tool_name}: {operation}", details)
    
    def log_memory_usage(self, component: str, memory_mb: float):
        """Log memory usage"""
        self.debug(LogCategory.MEMORY, f"Memory usage - {component}: {memory_mb:.2f} MB", {
            "component": component,
            "memory_mb": memory_mb
        })
    
    def start_performance_timer(self, operation: str) -> str:
        """Start a performance timer"""
        timer_id = f"{operation}_{int(time.time() * 1000)}"
        self.active_timers[timer_id] = {
            "operation": operation,
            "start_time": time.time(),
            "start_timestamp": datetime.now().isoformat()
        }
        self.trace(LogCategory.PERFORMANCE, f"Started timer: {operation}", {"timer_id": timer_id})
        return timer_id
    
    def end_performance_timer(self, timer_id: str, details: Optional[Dict] = None):
        """End a performance timer"""
        if timer_id not in self.active_timers:
            self.warning(LogCategory.PERFORMANCE, f"Timer not found: {timer_id}")
            return
        
        timer_data = self.active_timers.pop(timer_id)
        duration = time.time() - timer_data["start_time"]
        
        perf_data = {
            "operation": timer_data["operation"],
            "duration_ms": duration * 1000,
            "start_time": timer_data["start_timestamp"],
            "end_time": datetime.now().isoformat(),
            "details": details or {}
        }
        
        self.info(LogCategory.PERFORMANCE, 
                 f"Performance: {timer_data['operation']} took {duration*1000:.2f}ms", 
                 perf_data)
        
        # Print performance metric to terminal
        self._print_performance_metric(perf_data)
    
    def _print_performance_metric(self, perf_data: dict):
        """Print performance metric to terminal"""
        operation = perf_data["operation"]
        duration_ms = perf_data["duration_ms"]
        
        # Color code based on duration
        if duration_ms < 10:
            color = Fore.GREEN
        elif duration_ms < 100:
            color = Fore.YELLOW
        else:
            color = Fore.RED
        
        print(f"{Fore.LIGHTCYAN_EX}⚡ PERF: {color}{operation} {duration_ms:.2f}ms{Style.RESET_ALL}")
    


# Global debug logger instance
_debug_logger = None

def get_debug_logger() -> DebugLogger:
    """Get the global debug logger instance"""
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = DebugLogger()
    return _debug_logger


def debug_function(category: LogCategory = LogCategory.SYSTEM):
    """Decorator to automatically log function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_debug_logger()
            func_name = f"{func.__module__}.{func.__qualname__}"
            
            # Log function entry
            logger.log_function_call(func_name, args, kwargs)
            
            # Start performance timer
            timer_id = logger.start_performance_timer(func_name)
            
            try:
                result = func(*args, **kwargs)
                logger.trace(category, f"Function completed: {func_name}")
                return result
            except Exception as e:
                logger.log_exception(category, f"Function failed: {func_name}", e)
                raise
            finally:
                logger.end_performance_timer(timer_id)
        
        return wrapper
    return decorator
