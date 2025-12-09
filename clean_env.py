
import os

def clean_env():
    env_path = ".env"
    if not os.path.exists(env_path):
        print(".env not found.")
        return

    with open(env_path, "r") as f:
        lines = f.readlines()

    valid_lines = []
    print("Scanning .env for invalid lines...")
    for line in lines:
        stripped = line.strip()
        # Valid lines are empty, comments starting with #, or contain =
        if not stripped or stripped.startswith("#") or "=" in stripped:
            # Also exclude the divider lines if they are just =====
            if stripped.startswith("====="):
                print(f"Removing: {stripped}")
                continue
            valid_lines.append(line)
        else:
            print(f"Removing invalid line: {stripped}")

    # Write back
    with open(env_path, "w") as f:
        f.writelines(valid_lines)
    print("Cleaned .env file.")

if __name__ == "__main__":
    clean_env()
