# setup.py — UPGRADED one-time setup

import sys, os, subprocess
print("="*55)
print("  Smart Resume Analyzer — UPGRADED Setup")
print("="*55)

# NLTK data
print("\n📥 Downloading NLTK data...")
try:
    import nltk
    for r in ['stopwords','punkt','averaged_perceptron_tagger','wordnet']:
        nltk.download(r, quiet=True)
        print(f"   ✅  {r}")
except ImportError:
    print("   ❌  nltk not installed")

# spaCy model
print("\n🧠 Checking spaCy model...")
try:
    import spacy
    try:
        spacy.load('en_core_web_sm')
        print("   ✅  en_core_web_sm already downloaded")
    except OSError:
        print("   📥  Downloading en_core_web_sm...")
        subprocess.run([sys.executable,'-m','spacy','download','en_core_web_sm'], check=True)
        print("   ✅  en_core_web_sm downloaded")
except ImportError:
    print("   ⚠️   spaCy not installed. Run: pip install spacy")

# Sentence Transformers
print("\n🤖 Checking Sentence Transformers model...")
try:
    from sentence_transformers import SentenceTransformer
    print("   📥  Loading all-MiniLM-L6-v2 (downloads ~80MB on first run)...")
    SentenceTransformer('all-MiniLM-L6-v2')
    print("   ✅  Semantic model ready")
except ImportError:
    print("   ⚠️   sentence-transformers not installed. Run: pip install sentence-transformers")

# Directories
print("\n📁 Creating directories...")
for d in ['static/uploads','flask_sessions']:
    os.makedirs(os.path.join(os.path.dirname(__file__), d), exist_ok=True)
    print(f"   ✅  {d}/")

# Skills DB
print("\n📋 Checking skills database...")
p = os.path.join(os.path.dirname(__file__),'data','skills_db.json')
if os.path.exists(p):
    import json
    db = json.load(open(p))
    print(f"   ✅  {sum(len(v) for v in db.values())} skills in {len(db)} categories")
else:
    print("   ❌  skills_db.json not found!")

print("\n"+"="*55)
print("  ✅  Setup complete! Run: python run.py")
print("="*55)
