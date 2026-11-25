"""CountLees standalone review candidate. Local-only; no ecosystem dependencies."""
import os, sys, json, hashlib, shutil, tempfile, time, uuid, zipfile, stat
from pathlib import Path

def digest(p):
    with open(p,'rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def safe(p):
    p=Path(p)
    return p.is_file() and not any(x.is_symlink() or getattr(x.lstat(),'st_file_attributes',0)&1024 for x in (p,*p.parents))
def scan(root):
    root=Path(root).absolute(); rows=[]
    for d,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[x for x in dirs if not x.startswith('.') and x not in ('Windows','Program Files','Program Files (x86)','System Volume Information','node_modules') and not (Path(d)/x).is_symlink()]
        for n in files:
            p=Path(d)/n
            try:
                if safe(p):
                    s=p.stat(); rows.append((p,s.st_size,'Temporary candidate' if p.suffix.lower() in ('.tmp','.temp') and time.time()-s.st_mtime>86400 else 'Review only'))
            except OSError: pass
    return sorted(rows,key=lambda x:x[1],reverse=True)
def quarantine(p,root):
    p=Path(p).absolute(); root=Path(root).absolute()
    if not safe(p) or not p.is_relative_to(root) or p.suffix.lower() not in ('.tmp','.temp') or time.time()-p.stat().st_mtime<=86400: raise ValueError('Only selected, older temporary files are eligible.')
    q=root/'.countlees-recovery'; q.mkdir(exist_ok=True)
    if q.is_symlink() or getattr(q.lstat(),'st_file_attributes',0)&1024: raise ValueError('Unsafe recovery directory')
    entry=q/uuid.uuid4().hex; entry.mkdir(); h=digest(p); dest=entry/'payload'; meta=entry/'record.json'
    meta.write_text(json.dumps({'original':str(p),'sha256':h,'bytes':p.stat().st_size}),encoding='utf8')
    os.rename(p,dest)
    return entry

def restore(entry):
    entry=Path(entry); m=json.loads((entry/'record.json').read_text()); p=Path(m['original']); payload=entry/'payload'
    if not safe(payload) or digest(payload)!=m['sha256'] or p.exists() or p.is_symlink() or not p.parent.is_dir() or any(x.is_symlink() or getattr(x.lstat(),'st_file_attributes',0)&1024 for x in p.parents): raise ValueError('Restore blocked: integrity, destination or path conflict')
    # Exclusive destination creation; never overwrite.
    with open(payload,'rb') as src, open(p,'xb') as dst: shutil.copyfileobj(src,dst)
    if digest(p)!=m['sha256']: raise ValueError('Restore verification failed; recovery copy retained')
    return p

def compress(p,out):
    p=Path(p); out=Path(out)
    if not safe(p): raise ValueError('Unsafe source')
    h=digest(p)
    with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z: z.write(p,p.name)
    with zipfile.ZipFile(out) as z, z.open(p.name) as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=h: raise ValueError('Verification failed')
    return p.stat().st_size,out.stat().st_size,h

def main():
    import tkinter as tk
    from tkinter import ttk,filedialog,messagebox
    from PIL import Image,ImageTk
    bg='#11100e'; gold='#d6ac64'; fg='#eee1ca'; panel='#211c16'
    app=tk.Tk(); app.title('LeeWay CountLees — standalone review'); app.geometry('1100x740'); app.configure(bg=bg)
    assets=Path(__file__).parent/'assets'; images={}
    app.iconphoto(True, ImageTk.PhotoImage(Image.open(assets/'countlees.png')))
    for n,sz in [('full',(320,320)),('half',(68,68))]:
        im=Image.open(assets/(n+'.png')); im.thumbnail(sz); images[n]=ImageTk.PhotoImage(im)
    def label(parent,t,size=14,**kw): return tk.Label(parent,text=t,font=('Segoe UI',size),bg=kw.pop('bg',bg),fg=kw.pop('fg',fg),**kw)
    def btn(parent,t,fn): return tk.Button(parent,text=t,command=fn,bg=panel,fg=gold,activebackground=gold,activeforeground=bg,relief='flat',padx=16,pady=10)
    def clear():
        for w in app.winfo_children(): w.destroy()
    from accounts import Accounts
    accounts=Accounts(); session=[None]; failures=[0]; retry_at=[0.0]
    def login(signup=False):
        session[0]=None; clear()
        header=tk.Frame(app,bg=bg); header.pack(fill='x'); label(header,'',image=images['half']).pack(side='left',padx=20,pady=12); label(header,'COUNTLEES  /  SECURE LOCAL ACCESS',20,fg=gold).pack(side='left')
        form=tk.Frame(app,bg=panel,padx=42,pady=24,highlightbackground='#765631',highlightthickness=1); form.pack(pady=20)
        label(form,'Create your account' if signup else 'Welcome back',26,bg=panel,fg=gold).pack(pady=(0,8))
        label(form,'Your device. Your data. Your control.',12,bg=panel).pack(pady=(0,20))
        fields=[]
        for name,secret in [('Username or email',False),('Password',True)]+([('Confirm password',True)] if signup else []):
            label(form,name,12,bg=panel).pack(anchor='w'); e=tk.Entry(form,width=39,font=('Segoe UI',13),bg='#14120f',fg=fg,insertbackground=gold,show='•' if secret else '',relief='flat'); e.pack(ipady=8,pady=(4,12)); fields.append(e)
        status=label(form,'',11,bg=panel,fg='#efb78a',wraplength=370); status.pack()
        def submit():
            try:
                values=[e.get() for e in fields]
                if signup:
                    accounts.register(*values); login(); return
                if time.monotonic()<retry_at[0]: status.config(text='Too many attempts. Wait a few seconds.'); return
                identity=accounts.authenticate(*values)
                if identity is None:
                    failures[0]+=1; retry_at[0]=time.monotonic()+min(30,2**min(failures[0],5)); status.config(text='Invalid username or password.'); return
                failures[0]=0; session[0]=identity; dashboard()
            except (ValueError,OSError,__import__('sqlite3').Error) as e: status.config(text=str(e))
        btn(form,'CREATE LOCAL ACCOUNT' if signup else 'SIGN IN',submit).pack(fill='x',pady=8)
        btn(form,'Already registered? Sign in' if signup else 'New to CountLees? Create an account',lambda:login(not signup)).pack(fill='x')
        label(app,'Offline account • No email verification or cloud connection required',11).pack(pady=8)
        label(app,'Local sign-in is not a replacement for operating-system access controls.',10).pack()
        for e in fields: e.bind('<Return>',lambda event:submit())
        fields[0].focus_set()
    def dashboard():
        clear(); top=tk.Frame(app,bg=bg); top.pack(fill='x'); label(top,'',image=images['half']).pack(side='left',padx=15,pady=10); label(top,'COUNTLEES  /  SYSTEM OPERATIONS',22,fg=gold).pack(side='left'); label(top,f'{session[0]}  •  OFFLINE',11).pack(side='right',padx=20)
        nav=tk.Frame(app,bg=panel,width=220); nav.pack(side='left',fill='y'); nav.pack_propagate(False)
        body=tk.Frame(app,bg=bg); body.pack(side='left',fill='both',expand=True,padx=24,pady=12)
        def page(title,description):
            for w in body.winfo_children(): w.destroy()
            label(body,title,26,fg=gold).pack(anchor='w'); label(body,description,12,wraplength=730,justify='left').pack(anchor='w',pady=(5,20))
        def health():
            page('System Health','Measured locally. No simulated scores.'); u=shutil.disk_usage(Path.home());
            label(body,f'Disk free: {u.free/2**30:.2f} GiB  /  {u.total/2**30:.2f} GiB',21).pack(anchor='w',pady=15); label(body,f'OS: {sys.platform}  •  Logical CPUs: {os.cpu_count()}',17).pack(anchor='w');
            try:
                import psutil
                label(body,f'Memory available: {psutil.virtual_memory().available/2**30:.2f} GiB  •  CPU: {psutil.cpu_percent(interval=.2)}%',17).pack(anchor='w',pady=15)
            except ImportError: label(body,'Install psutil for optional CPU / RAM telemetry.',12).pack(anchor='w')
            btn(body,'Refresh measurements',health).pack(anchor='w',pady=20)
        def cleanup():
            page('Smart Cleanup','Choose a user-owned folder. Review candidates; quarantine only older .tmp/.temp files. Quarantine does not immediately free disk space.'); rows=[]; root=[None]; tree=ttk.Treeview(body,columns=('bytes','class'),show='tree headings',selectmode='browse'); tree.heading('#0',text='File'); tree.heading('bytes',text='Bytes'); tree.heading('class',text='Classification'); tree.column('bytes',width=100); tree.column('class',width=140); tree.pack(fill='both',expand=True)
            def run():
                x=filedialog.askdirectory();
                if not x:return
                root[0]=Path(x); rows[:]=scan(x); tree.delete(*tree.get_children());
                for i,(p,s,c) in enumerate(rows): tree.insert('', 'end',iid=str(i),text=str(p.relative_to(root[0])),values=(s,c))
            def move():
                if not tree.selection():return
                i=int(tree.selection()[0]); p=rows[i][0]
                if messagebox.askyesno('Confirm quarantine',str(p)):
                    try: quarantine(p,root[0]); tree.delete(str(i)); messagebox.showinfo('Quarantine','Moved to recoverable storage.')
                    except Exception as e: messagebox.showerror('Blocked',str(e))
            btn(body,'Scan folder',run).pack(side='left',pady=12); btn(body,'Quarantine selected',move).pack(side='left',padx=10)
        def recovery():
            page('Recovery Center','Select a quarantine entry folder containing record.json and payload. Restoration never overwrites existing files.')
            def run():
                p=filedialog.askdirectory();
                if p:
                    try: messagebox.showinfo('Restored',str(restore(p)))
                    except Exception as e: messagebox.showerror('Blocked',str(e))
            btn(body,'Restore selected recovery entry',run).pack(anchor='w')
        def compression():
            page('File Compression','Standard ZIP / SHA-256 round-trip verification. Original retained. Canonical LeeWay Formula not yet available; this is not Formula compression.')
            def run():
                p=filedialog.askopenfilename();
                if not p:return
                o=filedialog.asksaveasfilename(defaultextension='.zip');
                if o:
                    try: a,b,h=compress(p,o); messagebox.showinfo('Verified ZIP',f'Original: {a:,} bytes\nArchive: {b:,} bytes\nSHA-256: {h}')
                    except Exception as e: messagebox.showerror('Blocked',str(e))
            btn(body,'Compress and verify file',run).pack(anchor='w')
        def updates():
            page('Performance & Updates','Open native Windows maintenance controls. No processes killed or settings changed automatically.');
            if sys.platform=='win32':
                for t,u in [('Storage Sense','ms-settings:storagesense'),('Windows Update','ms-settings:windowsupdate'),('Startup apps','ms-settings:startupapps')]: btn(body,t,lambda u=u:os.startfile(u)).pack(anchor='w',pady=5)
            else: label(body,'Native update integration not implemented on this platform.').pack(anchor='w')
        for t,fn in [('System Health',health),('Smart Cleanup',cleanup),('File Compression',compression),('Recovery Center',recovery),('Performance & Updates',updates),('Sign out',login)]: btn(nav,t,fn).pack(fill='x',padx=8,pady=5)
        health()
    label(app,'',image=images['full']).pack(pady=(80,10)); label(app,'COUNTLEES',34,fg=gold).pack(); label(app,'ENGINEERED FOR LEGACY',16,fg=gold).pack(pady=8); label(app,'Initializing local system maintenance…',12).pack(pady=8); progress=ttk.Progressbar(app,mode='indeterminate',length=300); progress.pack(pady=12); progress.start(12); app.after(1800,login); app.mainloop()
if __name__=='__main__': main()
