import os
import sys
import subprocess
import shutil
import platform
import importlib.util

try:
    import importlib.metadata as metadata
except ImportError:
    import importlib_metadata as metadata # fallback for older python

def build():
    # 0. Check Python version (Strictly 3.9 recommended, but allow 3.10+ if user is running it)
    v = sys.version_info
    print(f"Starting build for {platform.system()} (Python {v.major}.{v.minor})...")
    
    # 1. Setup paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    release_dir = os.path.join(base_dir, "releases")
    dist_dir = os.path.join(base_dir, "dist")
    build_temp_dir = os.path.join(base_dir, "build")
    app_name = "speech-to-text"
    
    # 2. Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("\nERROR: PyInstaller not found!")
        sys.exit(1)

    # 3. Clean up old build folders
    folders_to_clean = [release_dir, dist_dir, build_temp_dir]
    for folder in folders_to_clean:
        if os.path.exists(folder):
            print(f"Cleaning up {folder}...")
            shutil.rmtree(folder)
    
    os.makedirs(release_dir, exist_ok=True)

    # 4. Prepare metadata flags
    optional_distributions = [
        "torch", "tqdm", "regex", "requests", "packaging", 
        "filelock", "numpy", "tokenizers", "openai-whisper", "vosk", "PyQt6", "pynput",
        "ctranslate2", "transformers", "huggingface-hub", "sentencepiece", "speechbrain"
    ]
    
    metadata_flags = []
    for dist_name in optional_distributions:
        try:
            metadata.distribution(dist_name)
            metadata_flags.extend(["--copy-metadata", dist_name])
        except metadata.PackageNotFoundError:
            continue

    # 5. OS-Specific configuration
    os_name = platform.system().lower()
    extra_args = []
    
    if os_name == "darwin":
        # macOS specific: Create a .app bundle and handle permissions
        extra_args.extend([
            "--windowed", # No console window by default
            "--osx-bundle-identifier", "com.gemini.speech-to-text",
        ])
    elif os_name == "windows":
        extra_args.extend(["--windowed"]) # Use --console if you want to see logs on Windows
    
    # 6. Define PyInstaller command
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--name", app_name,
        "--distpath", release_dir,
        "--hidden-import", "pyaudiowpatch",
        "--hidden-import", "pyobjc",
        "--hidden-import", "torch",
        "--hidden-import", "torchaudio",
        "--hidden-import", "PyQt6",
        "--hidden-import", "pynput.keyboard._darwin",
        "--hidden-import", "pynput.keyboard._win32",
        "--hidden-import", "pynput.keyboard._xorg",
        "--hidden-import", "pynput.mouse._darwin",
        "--hidden-import", "pynput.mouse._win32",
        "--hidden-import", "pynput.mouse._xorg",
        "--hidden-import", "ctranslate2",
        "--hidden-import", "transformers",
        "--hidden-import", "huggingface_hub",
        "--hidden-import", "sentencepiece",
        "--hidden-import", "speechbrain",
        "--collect-all", "vosk",
        "--collect-all", "whisper",
        "--collect-all", "deep_translator",
        "--collect-all", "torch",
        "--collect-all", "torchaudio",
        "--collect-all", "PyQt6",
        "--collect-all", "pynput",
        "--collect-all", "ctranslate2",
        "--collect-all", "transformers",
        "--collect-all", "huggingface_hub",
        "--collect-all", "sentencepiece",
        "--collect-all", "speechbrain",
        "--collect-all", "silero_vad"
    ] + metadata_flags + extra_args + ["main.py"]

    print("\nRunning PyInstaller...")
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return

    # 7. Add extra files
    if os_name == "darwin":
        app_path = os.path.join(release_dir, f"{app_name}.app")
        plist_dest = os.path.join(app_path, "Contents", "Info.plist")
        if os.path.exists("Info.plist"):
            print(f"Overwriting {plist_dest} with custom Info.plist...")
            shutil.copy2("Info.plist", plist_dest)
        
        target_dir = os.path.join(release_dir)
    else:
        target_dir = os.path.join(release_dir, app_name)

    print(f"\nAdding extra files to {target_dir}...")
    for f in ["README.md", "requirements.txt"]:
        src = os.path.join(base_dir, f)
        if os.path.exists(src):
            shutil.copy2(src, target_dir)

    os.makedirs(os.path.join(target_dir, "models"), exist_ok=True)

    # 8. Create ZIP
    final_os = "macos" if os_name == "darwin" else os_name
    output_zip = f"speech-to-text-{final_os}"
    print(f"\nCreating ZIP: {output_zip}.zip")
    
    # Zip the entire folder in releases/
    if os_name == "darwin":
        # For Mac, we want to zip the .app AND the models folder if it was outside
        # But usually users expect a single folder or a dmg
        shutil.make_archive(os.path.join(release_dir, output_zip), 'zip', release_dir)
    else:
        shutil.make_archive(os.path.join(release_dir, output_zip), 'zip', target_dir)

    print("\nBUILD COMPLETE!")

if __name__ == "__main__":
    build()
