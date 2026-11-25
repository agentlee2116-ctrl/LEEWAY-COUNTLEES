# CountLees

CountLees is a local Windows desktop review candidate for system measurements, file review, recoverable temporary-file quarantine, and standard ZIP compression.

**This is a desktop application, not a browser app.** GitHub Pages hosts the project information and setup guide; it cannot run the Python/Tkinter application.

## Run on Windows

1. Install Python 3.12 or newer from [python.org](https://www.python.org/downloads/windows/) with Tk support enabled.
2. Download this repository using **Code → Download ZIP**, then extract it.
3. Open a terminal in the extracted folder and run:

   ```powershell
   py -m pip install -r requirements.txt
   py countlees.py
   ```

You can also run `Launch-CountLees.cmd` from the extracted folder.

## Important limitations

- Accounts and data are stored locally. There is no cloud registration, email verification, or password recovery.
- Local application sign-in is not an operating-system security boundary.
- Cleanup only offers selected `.tmp`/`.temp` files older than one day for recoverable quarantine; it does not permanently delete files or immediately reclaim disk space.
- Compression uses standard ZIP and keeps the original file. It is not LeeWay Formula compression.
- Performance and update controls open native Windows settings; they do not automatically optimize the system.
- Android and iOS are not implemented. This candidate is not independently verified or production qualified.

See the [CountLees project site](https://agentlee2116-ctrl.github.io/LEEWAY-COUNTLEES/) for the overview and setup information.
