"""CountLees local account store. Not an operating-system security boundary."""
import os, sqlite3, hashlib, hmac, secrets, re
from pathlib import Path

def default_path():
    base = Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'.local/share'))) if os.name=='nt' else (Path.home()/'Library/Application Support' if __import__('sys').platform=='darwin' else Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share'))))
    return base/'CountLees'/'accounts.sqlite3'

class Accounts:
    def __init__(self,path=None):
        self.path=Path(path or default_path()); self.path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        if not self.path.exists():
            try: os.close(os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600))
            except FileExistsError: pass
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS accounts (username TEXT PRIMARY KEY, display_name TEXT NOT NULL, salt BLOB NOT NULL, verifier BLOB NOT NULL)')
    @staticmethod
    def derive(password,salt):
        return hashlib.scrypt(password.encode('utf-8'),salt=salt,n=32768,r=8,p=1,maxmem=64*1024*1024,dklen=32)
    def register(self,username,password,confirm):
        username=username.strip()
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.@+\-]{2,79}',username): raise ValueError('Use 3–80 letters, numbers or . _ @ + - for your username.')
        if not 12<=len(password)<=256: raise ValueError('Choose a password with 12–256 characters.')
        if password!=confirm: raise ValueError('Passwords do not match.')
        salt=secrets.token_bytes(16); verifier=self.derive(password,salt)
        try:
            with sqlite3.connect(self.path) as db: db.execute('INSERT INTO accounts VALUES (?,?,?,?)',(username.lower(),username,salt,verifier))
        except sqlite3.IntegrityError: raise ValueError('That local account already exists.') from None
    def authenticate(self,username,password):
        if len(username)>256 or len(password)>256: return None
        with sqlite3.connect(self.path) as db: row=db.execute('SELECT display_name,salt,verifier FROM accounts WHERE username=?',(username.strip().lower(),)).fetchone()
        candidate=self.derive(password,row[1] if row else b'\0'*16)
        return row[0] if row and hmac.compare_digest(candidate,row[2]) else None
