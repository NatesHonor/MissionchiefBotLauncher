from handlers.console import send_messages, send_warning, send_success, send_system, send_error
from handlers.logging import log_info, log_warning, log_error, log_exception
from utils import state


def stop_bot():
    send_system("Initiating shutdown sequence...")
    log_info("Bot stop requested")

    try:
        active = state.get_active_processes() if hasattr(state, 'get_active_processes') else {}
        count = len(active) if isinstance(active, dict) else 0

        if count > 0:
            send_warning(f"Terminating {count} active process{'es' if count != 1 else ''}...")
            log_info(f"Stopping {count} active processes")
        else:
            send_system("No active processes found")
            log_info("No active processes to stop")

        state.stop_all()

        remaining = state.get_active_processes() if hasattr(state, 'get_active_processes') else {}
        remaining_count = len(remaining) if isinstance(remaining, dict) else 0

        if remaining_count > 0:
            send_error(f"{remaining_count} process{'es' if remaining_count != 1 else ''} failed to terminate")
            log_error(f"{remaining_count} processes failed to terminate")

            if hasattr(state, 'force_kill_all'):
                send_warning("Force killing remaining processes...")
                state.force_kill_all()
                send_success("All processes force terminated")
                log_info("Force killed remaining processes")
        else:
            send_success("All processes terminated successfully")
            log_info("All processes terminated cleanly")

    except Exception as e:
        send_error(f"Error during shutdown: {e}")
        log_exception("Exception during bot shutdown")

        try:
            state.stop_all()
        except Exception:
            pass