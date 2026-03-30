/**
 * Logger utility for frontend
 * Provides consistent logging across the application
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  data?: unknown;
  source?: string;
}

class Logger {
  private source: string;
  private logs: LogEntry[] = [];
  private maxLogs = 1000;

  constructor(source: string = 'app') {
    this.source = source;
  }

  private formatTimestamp(): string {
    return new Date().toISOString();
  }

  private log(level: LogLevel, message: string, data?: unknown): void {
    const entry: LogEntry = {
      timestamp: this.formatTimestamp(),
      level,
      message,
      data,
      source: this.source,
    };

    // Store in memory
    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    // Console output with styling
    const styles: Record<LogLevel, string> = {
      debug: 'color: #9ca3af',
      info: 'color: #3b82f6',
      warn: 'color: #f59e0b',
      error: 'color: #ef4444',
    };

    const prefix = `%c[${entry.timestamp}] [${level.toUpperCase()}] [${this.source}]`;

    switch (level) {
      case 'debug':
        console.debug(prefix, styles.debug, message, data ?? '');
        break;
      case 'info':
        console.info(prefix, styles.info, message, data ?? '');
        break;
      case 'warn':
        console.warn(prefix, styles.warn, message, data ?? '');
        break;
      case 'error':
        console.error(prefix, styles.error, message, data ?? '');
        break;
    }
  }

  debug(message: string, data?: unknown): void {
    this.log('debug', message, data);
  }

  info(message: string, data?: unknown): void {
    this.log('info', message, data);
  }

  warn(message: string, data?: unknown): void {
    this.log('warn', message, data);
  }

  error(message: string, data?: unknown): void {
    this.log('error', message, data);
  }

  // Get all logs (for debugging)
  getLogs(): LogEntry[] {
    return [...this.logs];
  }

  // Clear logs
  clearLogs(): void {
    this.logs = [];
  }
}

// Create logger instances for different parts of the app
export const appLogger = new Logger('App');
export const apiLogger = new Logger('API');
export const deviceLogger = new Logger('Devices');
export const metricsLogger = new Logger('Metrics');

export default Logger;
