import subprocess

def run_command(command):
    try:
        out = subprocess.run(command, shell=True, check=False, text=True, capture_output=True)
        if out.returncode != 0:
            return out.stderr if out.stderr else f"Error: Process exited with code {out.returncode}"
        return out.stdout
    except Exception as e:
        return str(e)
    