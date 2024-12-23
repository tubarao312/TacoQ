import asyncio
import signal
import click
from typing import Optional
from contextlib import AsyncExitStack
from worker.client import WorkerApplication


class ApplicationRunner:
    """
    # Application Runner

    Handles the lifecycle of a TacoQ worker application including:
    - Signal handling
    - Graceful shutdown
    - Application startup and teardown
    """

    def __init__(self, app: WorkerApplication):
        """
        Initialize Application Runner

        ### Args:
            - `app`: WorkerApplication instance to manage
        """
        self.app = app
        self._shutdown_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None
        self._loop = asyncio.get_event_loop()

    def _handle_signals(self):
        """Configure signal handlers for graceful shutdown"""
        for sig in (signal.SIGTERM, signal.SIGINT):
            self._loop.add_signal_handler(
                sig, lambda: asyncio.create_task(self._signal_handler())
            )

    async def _signal_handler(self):
        """Handle shutdown signals"""
        click.echo("\nShutdown signal received...", err=True)
        self._shutdown_event.set()

    async def startup(self, reload: bool = False):
        """
        Initialize and start the worker application

        ### Args:
            `reload`: Enable hot reload mode
        """
        click.echo("Initializing application...")
        self._handle_signals()

        self._task = asyncio.create_task(self.app.entrypoint())
        click.echo("Application started successfully")

        try:
            await self._shutdown_event.wait()
        except Exception as e:
            click.secho(f"ERROR: Application runtime error: {e}", fg="red", err=True)
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Gracefully shutdown the application"""
        if self._task and not self._task.done():
            try:
                click.echo("Initiating graceful shutdown...")
                self._task.cancel()
                await asyncio.wait_for(self._task, timeout=5.0)
                click.echo("Shutdown completed successfully")
            except asyncio.TimeoutError:
                click.secho(
                    "Warning: Application shutdown timed out", fg="yellow", err=True
                )
            except asyncio.CancelledError:
                click.echo("Application shutdown complete")
            except Exception as e:
                click.secho(f"ERROR: Shutdown error: {e}", fg="red", err=True)


async def run_application(
    app: WorkerApplication,
    reload: bool = False,
) -> None:
    """
    Run Worker Application

    Manages the complete lifecycle of a worker application.

    ### Args:
        `app`: WorkerApplication instance to run
        `reload`: Enable hot reload mode for development
    """
    async with AsyncExitStack():
        runner = ApplicationRunner(app)
        await runner.startup(reload)
