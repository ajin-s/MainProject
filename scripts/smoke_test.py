"""
Run this after `pip install -r requirements.txt` to confirm your environment is ready.
Does NOT require a camera, LLM, or hardware — just checks imports and Python version.
"""
import sys

def check(label, fn):
    try:
        fn()
        print(f"  [OK]   {label}")
        return True
    except Exception as e:
        print(f"  [FAIL] {label}: {e}")
        return False

def main():
    print(f"Python version: {sys.version.split()[0]}")
    ok = True
    ok &= check("pydantic", lambda: __import__("pydantic"))
    ok &= check("opencv-python (cv2)", lambda: __import__("cv2"))
    ok &= check("mediapipe", lambda: __import__("mediapipe"))
    ok &= check("fastapi", lambda: __import__("fastapi"))
    ok &= check("sentence-transformers", lambda: __import__("sentence_transformers"))
    ok &= check("faiss", lambda: __import__("faiss"))
    ok &= check("networkx", lambda: __import__("networkx"))

    print()
    if ok:
        print("✅ environment OK — you're ready to write code.")
    else:
        print("⚠️  some packages failed to import — re-run: pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()
